#!/usr/bin/env python3
"""
Audit PANBuster & Rétention — compatible listings "ls -lR" multi-fichiers
----------------------------------------------------------------------------

Objectifs :
  1) PANBuster : lire des **CSV** (et uniquement CSV), filtrer les lignes où la colonne
     **BIN Countries** contient un pays autorisé (par défaut `FR`) et produire un
     rapport texte lisible. **Pour chaque match FR, on renvoie aussi le `PAN Number`
     et le `Hostname`.**
  2) Rétention : lire des **fichiers d'inventaire** (format libre). Supporte :
       - format recommandé `find -printf '%T@,%p\n'` (CSV epoch,path)
       - format recommandé `find -printf '%T@\t%p\n'` (TSV epoch\tpath)
       - format **ls -lR** avec sections `"/chemin":` puis lignes `-rw... nom` (avec ou sans quotes)
         — y compris un **préfixe numérique** (n° de ligne) comme dans l'exemple fourni.

Entrées :
  - PANBuster : CSV dans `panbuster.input_dir` (par défaut `./panbuster_in/`). Colonnes typiques :
    `Hostname`, `File Path`, `PAN Number`, `BIN Issuer`, `BIN Brand`, `BIN Countries`,
    `PAN offset in file`, `PAN line offsets in file`, `Bytes before + PAN + Bytes After`.
  - Listings : plusieurs fichiers (ex: `*-data.txt`) dans `inventory.dir` (par défaut `./listings/`).

Sorties (lisibles par humain) dans `./out/report_YYYYmmdd_HHMMSS/` :
  - `REPORT.txt`                → résumé global
  - `panbuster_report.txt`      → **hostname + PAN + file path + countries (FR)** + agrégats par hostname
  - `retention_violations.txt`  → fichiers au-delà des seuils (chemin, âge, seuil)
  - `sensitive_dirs_tree.txt`   → arborescences reconstituées des répertoires sensibles
  - `signatures.txt`            → fichiers *.rspf / *.reqf / *.gpg trouvés

Dépendances : aucune obligatoire (PyYAML optionnel pour la conf YAML). Pas de pandas.

Exemples :
  python audit_pan_retention_v4.py --init-config conf.yml
  python audit_pan_retention_v4.py --config conf.yml --out ./out

"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

# ---------------------------------------------
# Configuration par défaut (modifiable via conf)
# ---------------------------------------------
DEFAULT_CONFIG: Dict[str, Any] = {
    "output": {"dir": "./out"},

    "panbuster": {
        "input_dir": "./panbuster_in",
        "glob": "*.csv",
        # Colonnes: auto-détectées si None (noms insensibles à la casse)
        "countries_column": None,   # ex: "BIN Countries"
        "pan_column": None,         # ex: "PAN Number"
        "hostname_column": None,    # ex: "Hostname"
        "filepath_column": None,    # ex: "File Path" (optionnel, utilité affichage)
        "allowed_countries": ["FR"],
        "output_file": "panbuster_report.txt",
    },

    "inventory": {
        "dir": "./listings",
        "glob": "*-data.txt",        # prend en compte tous les fichiers du type xxx-xxx-xxxx-data.txt
        "timezone": "Europe/Paris", # indicatif (affichage/approx.)
        "max_files": 0               # 0 = sans limite
    },

    # Règles de rétention (la plus spécifique l'emporte)
    "retention_rules": [
        {"path": "/staging",   "max_age_days": 1},
        {"path": "/processed", "max_age_days": 10},
        {"path": "/data",      "max_age_days": 10},
    ],
    "retention_output": "retention_violations.txt",

    # Répertoires sensibles + signatures
    "sensitive_dirs": {
        "paths": ["/requisition", "/sftp", "/sftp-p"],
        "max_depth": 4,
        "output_file": "sensitive_dirs_tree.txt",
    },
    "signatures": {
        "patterns": ["*.rspf", "*.reqf", "*.gpg"],
        "output_file": "signatures.txt",
    },

    "report_file": "REPORT.txt",
}

# ---------------
# Outils généraux
# ---------------

def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def epoch_to_dt(epoch: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)


def human_age_days(epoch: float) -> float:
    return max(0.0, (now_utc() - epoch_to_dt(epoch)).total_seconds() / 86400.0)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return json.loads(json.dumps(DEFAULT_CONFIG))  # deepcopy
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        try:
            cfg = yaml.safe_load(text)
            if isinstance(cfg, dict):
                return cfg
        except Exception:
            pass
    return json.loads(text)

# ----------------------------
# PANBuster (CSV → FR only)
# ----------------------------
PAN_COUNTRIES_CANDIDATES = [
    "bin countries", "countries", "country", "pays", "bin_country", "country_code"
]
PAN_PANNUM_CANDIDATES = [
    "pan number", "pan", "pan_number", "pan no", "pan_no"
]
PAN_HOSTNAME_CANDIDATES = [
    "hostname", "host", "server"
]
PAN_FILEPATH_CANDIDATES = [
    "file path", "filepath", "file", "path"
]


def find_column(name_candidates: List[str], header: List[str]) -> Optional[str]:
    idx = {h.lower(): h for h in header}
    for cand in name_candidates:
        if cand.lower() in idx:
            return idx[cand.lower()]
    return None


def normalize_token(tok: str) -> Optional[str]:
    t = tok.strip().upper()
    if not t or t in {"{VIDE}", "VIDE", "EMPTY", "NONE", "NULL", "N/A"}:
        return None
    if t in {"FRANCE", "FRA"}:  # mapping commun
        return "FR"
    if len(t) == 2 and t.isalpha():
        return t
    # tolérance: garder FR si présent dans une chaîne type "FR;CA" sera traité ailleurs
    return t if t == "FR" else None


def parse_countries_field(raw: Any) -> List[str]:
    if raw is None:
        return []
    s = str(raw)
    # remplace séparateurs et balises par espace
    s = re.sub(r"[\{\}\[\]\(\),;\|/\\]+", " ", s)
    tokens = [normalize_token(t) for t in s.split()]
    toks = [t for t in tokens if t]
    # dédoublonne en préservant l'ordre
    seen = set()
    out: List[str] = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def process_panbuster(cfg: Dict[str, Any], out_dir: Path) -> Dict[str, Any]:
    conf = cfg["panbuster"]
    folder = Path(conf["input_dir"]).expanduser()
    glob = conf.get("glob", "*.csv")
    allowed = {c.upper() for c in conf.get("allowed_countries", ["FR"])}
    out_file = out_dir / conf.get("output_file", "panbuster_report.txt")

    files = sorted(folder.glob(glob))
    total_rows = 0
    flagged: List[Dict[str, Any]] = []

    for f in files:
        try:
            with f.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.reader(fh)
                try:
                    header = next(reader)
                except StopIteration:
                    continue
                countries_col = conf.get("countries_column") or find_column(PAN_COUNTRIES_CANDIDATES, header)
                pan_col = conf.get("pan_column") or find_column(PAN_PANNUM_CANDIDATES, header)
                host_col = conf.get("hostname_column") or find_column(PAN_HOSTNAME_CANDIDATES, header)
                fpath_col = conf.get("filepath_column") or find_column(PAN_FILEPATH_CANDIDATES, header)
                if countries_col is None or pan_col is None:
                    # colonnes indispensables manquantes → passer au fichier suivant
                    continue
                hmap = {name: i for i, name in enumerate(header)}
                for row in reader:
                    total_rows += 1
                    try:
                        raw_countries = row[hmap[countries_col]] if countries_col in hmap else ""
                        coun_list = parse_countries_field(raw_countries)
                        if not set(coun_list) & allowed:
                            continue
                        pan_val = (row[hmap[pan_col]] or "").strip() if pan_col in hmap else ""
                        host_val = (row[hmap[host_col]] or "").strip() if host_col in hmap else ""
                        fpath_val = (row[hmap[fpath_col]] or "").strip() if fpath_col in hmap else ""
                        flagged.append({
                            "file": f.name,
                            "hostname": host_val,
                            "pan": pan_val,
                            "filepath": fpath_val,
                            "countries": coun_list,
                        })
                    except Exception:
                        continue
        except Exception:
            continue

    # Rapport texte humain
    with out_file.open("w", encoding="utf-8") as w:
        w.write("PANBUSTER — Lignes avec pays autorisés (ex: FR)\n")
        w.write("=" * 80 + "\n\n")
        w.write(f"Fichiers lus : {len(files)}\n")
        for f in files:
            w.write(f"  - {f.name}\n")
        w.write(f"\nTotal lignes (toutes) : {total_rows}\n")
        w.write(f"Total lignes retenues  : {len(flagged)}\n\n")
        if flagged:
            w.write("Détail (hostname\tPAN\tfilepath\tcountries)\n")
            w.write("-" * 80 + "\n")
            for it in flagged[:2000]:
                countries_str = ",".join(it.get("countries", []))
                w.write(f"{it.get('hostname','')}\t{it.get('pan','')}\t{it.get('filepath','')}\t{countries_str}\n")
            # Agrégats par hostname
            by_host: Dict[str, int] = {}
            for it in flagged:
                key = it.get("hostname", "")
                by_host[key] = by_host.get(key, 0) + 1
            if by_host:
                w.write("\nAgrégat par hostname (lignes retenues)\n")
                w.write("-" * 80 + "\n")
                for k in sorted(by_host):
                    w.write(f"{k or '<inconnu>'}: {by_host[k]}\n")
    return {
        "files": [f.name for f in files],
        "total_rows": total_rows,
        "flagged_count": len(flagged),
        "out": str(out_file),
    }

# -------------------------------------------------------
# Listings texte → (path, epoch_mtime) + rétention + tree
# -------------------------------------------------------

# A) Formats préférés (%T@ = epoch secondes)
REC_EPOCH_CSV = re.compile(r"^\s*(?:\d+\s+)?(?P<epoch>\d{10}(?:\.\d+)?)\s*,\s*(?P<path>/.+)$")
REC_EPOCH_TSV = re.compile(r"^\s*(?:\d+\s+)?(?P<epoch>\d{10}(?:\.\d+)?)\s+(?P<path>/.+)$")

# B) Heuristique 'ls -lR'
REC_DIR_HEADER = re.compile(r"^\s*(?:\d+\s+)?\"(?P<dir>/[^\"]+)\":\s*$")
REC_TOTAL = re.compile(r"^\s*(?:\d+\s+)?total\b", re.IGNORECASE)
REC_LS_FULLPATH = re.compile(
    r"^\s*(?:\d+\s+)?([bcdlps-][rwxStT-]{9})\s+\d+\s+\S+\s+\S+\s+\d+\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+"  # date er
    r"(?:\d{2}:\d{2}|\d{4})\s+(?P<path>/.+)$"
)
REC_LS_NAME = re.compile(
    r"^\s*(?:\d+\s+)?(?P<mode>[bcdlps-][rwxStT-]{9})\s+\d+\s+\S+\s+\S+\s+\d+\s+"
    r"(?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?:(?P<hour>\d{2}):(?P<min>\d{2})|(?P<year>\d{4}))\s+"
    r"(?P<name>\".*?\"|[^\"]+)\s*$"
)
MONTHS = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}


def parse_ls_line(line: str, current_dir: Optional[str]) -> Optional[Tuple[str, float]]:
    """Parse une ligne `ls -l`.
    - Si la ligne inclut un chemin absolu → retourne tel quel.
    - Sinon, combine `current_dir` + `name`.
    Retourne (path, epoch) ou None.
    """
    m = REC_LS_FULLPATH.match(line)
    if m:
        return None
    m = REC_LS_NAME.match(line)
    if not m:
        return None
    mode = m.group("mode")
    if mode and mode[0] == 'd':  # dossier → ignorer
        return None
    mon = MONTHS.get(m.group("mon"), 1)
    day = int(m.group("day"))
    year = int(m.group("year")) if m.group("year") else now_utc().year
    hour = int(m.group("hour") or 0)
    minute = int(m.group("min") or 0)
    # Nom (peut être entre quotes)
    name = m.group("name").strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    if name in {".", ".."}:
        return None
    # Compose chemin
    if name.startswith('/'):
        full = name
    elif current_dir:
        full = current_dir.rstrip('/') + '/' + name
    else:
        return None
    try:
        dt_local = dt.datetime(year, mon, day, hour, minute)
        epoch = dt_local.replace(tzinfo=dt.timezone.utc).timestamp()
        return full, float(epoch)
    except Exception:
        return None


def parse_inventory_file(f: Path) -> List[Tuple[str, float]]:
    entries: List[Tuple[str, float]] = []
    current_dir: Optional[str] = None
    try:
        with f.open("r", encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                # En-têtes de répertoire :  "<abs_path>":
                m_dir = REC_DIR_HEADER.match(line)
                if m_dir:
                    current_dir = m_dir.group("dir")
                    continue
                if REC_TOTAL.match(line):
                    continue
                # Formats epoch
                m = REC_EPOCH_CSV.match(line)
                if m:
                    entries.append((m.group("path"), float(m.group("epoch"))))
                    continue
                m = REC_EPOCH_TSV.match(line)
                if m:
                    entries.append((m.group("path"), float(m.group("epoch"))))
                    continue
                # ls -l (nom relatif)
                parsed = parse_ls_line(line, current_dir)
                if parsed:
                    entries.append(parsed)
    except Exception:
        return entries
    return entries


def load_inventory_files(cfg: Dict[str, Any]) -> List[Tuple[str, float]]:
    conf = cfg["inventory"]
    folder = Path(conf["dir"]).expanduser()
    glob = conf.get("glob", "*-data.txt")
    max_files = int(conf.get("max_files", 0))

    pairs: List[Tuple[str, float]] = []
    count_files = 0
    for f in sorted(folder.glob(glob)):
        if max_files and count_files >= max_files:
            break
        count_files += 1
        pairs.extend(parse_inventory_file(f))
    return pairs

# ----------------------
# Règles de rétention
# ----------------------

def most_specific_rule(path: str, rules: List[Tuple[str, int]]) -> Optional[int]:
    best_len = -1
    best_val: Optional[int] = None
    for base, age in rules:
        base = base.rstrip('/')
        if path.startswith(base + '/') or path == base:
            L = len(base)
            if L > best_len:
                best_len = L
                best_val = age
    return best_val


def check_retention(cfg: Dict[str, Any], entries: List[Tuple[str, float]], out_dir: Path) -> Dict[str, Any]:
    rules_cfg = cfg.get("retention_rules", [])
    rules: List[Tuple[str, int]] = [(r["path"], int(r["max_age_days"])) for r in rules_cfg]
    out_file = out_dir / cfg.get("retention_output", "retention_violations.txt")

    violations: List[Tuple[str, float, int]] = []  # (path, age_days, max_age)
    for path, epoch in entries:
        age = human_age_days(epoch)
        rule = most_specific_rule(path, rules)
        if rule is None:
            continue
        if age > float(rule):
            violations.append((path, age, rule))

    violations.sort(key=lambda x: x[1], reverse=True)

    with out_file.open("w", encoding="utf-8") as w:
        w.write("FICHIERS HORS RÉTENTION\n")
        w.write("=" * 80 + "\n")
        w.write("Chemin\tÂge (j)\tSeuil (j)\n")
        w.write("-" * 80 + "\n")
        for path, age, rule in violations:
            w.write(f"{path}\t{age:.2f}\t{rule}\n")
        w.write("\nTotal: %d fichiers hors rétention\n" % len(violations))
    return {"count": len(violations), "out": str(out_file)}

# -----------------------------------
# 3) Sensibles (tree) & signatures
# -----------------------------------

def build_virtual_tree(base: str, paths: Iterable[str], max_depth: int = 4) -> List[str]:
    base = base.rstrip('/')
    rels: List[str] = []
    for p in paths:
        if p.startswith(base + '/') or p == base:
            rel = p[len(base):].lstrip('/')
            rels.append(rel)
    rels = sorted(set(rels))
    lines: List[str] = [f"{base}/"]
    parts_map: Dict[str, List[str]] = {}
    for r in rels:
        parts = r.split('/') if r else []
        if not parts:
            continue
        parts_map.setdefault('', []).append(parts[0])
    def walk(prefix_rel: str, prefix_print: str, depth: int):
        if depth > max_depth:
            return
        children = sorted(set(parts_map.get(prefix_rel, [])))
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            connector = '└── ' if is_last else '├── '
            lines.append(prefix_print + connector + child)
            child_rel = (prefix_rel + '/' + child).strip('/')
            subkids: List[str] = []
            for r in rels:
                if r == child_rel or r.startswith(child_rel + '/'):
                    rest = r[len(child_rel):].lstrip('/')
                    if rest:
                        subkids.append(rest.split('/')[0])
            if subkids:
                parts_map[child_rel] = subkids
                new_prefix = prefix_print + ('    ' if is_last else '│   ')
                walk(child_rel, new_prefix, depth + 1)
    walk('', '', 1)
    return lines


def dump_sensitive_and_signatures(cfg: Dict[str, Any], entries: List[Tuple[str, float]], out_dir: Path) -> Dict[str, Any]:
    sens = cfg.get("sensitive_dirs", {})
    sens_paths: List[str] = [str(p) for p in sens.get("paths", [])]
    max_depth = int(sens.get("max_depth", 4))
    out_tree = out_dir / sens.get("output_file", "sensitive_dirs_tree.txt")

    sig = cfg.get("signatures", {})
    patterns: List[str] = [str(p) for p in sig.get("patterns", ["*.rspf", "*.reqf", "*.gpg"]) ]
    out_sig = out_dir / sig.get("output_file", "signatures.txt")

    all_paths = [p for p, _ in entries]

    # Tree
    with out_tree.open("w", encoding="utf-8") as w:
        for base in sens_paths:
            lines = build_virtual_tree(base, all_paths, max_depth=max_depth)
            if len(lines) == 1 and lines[0].endswith('/'):
                w.write(f"{base}/ (aucun fichier listé)\n\n")
            else:
                w.write("\n".join(lines) + "\n\n")

    # Signatures
    sig_hits: List[str] = []
    for p in all_paths:
        name = os.path.basename(p)
        if any(fnmatch(name, pat) for pat in patterns):
            sig_hits.append(p)
    sig_hits.sort()

    with out_sig.open("w", encoding="utf-8") as w:
        if not sig_hits:
            w.write("Aucun fichier signature trouvé.\n")
        else:
            for p in sig_hits:
                w.write(p + "\n")
            w.write(f"\nTotal: {len(sig_hits)}\n")

    return {"tree": str(out_tree), "signatures": str(out_sig), "sig_count": len(sig_hits)}

# ----------------------
# Rapport global texte
# ----------------------

def write_human_report(cfg: Dict[str, Any], out_dir: Path, pan: Dict[str, Any], inv_count: int, ret: Dict[str, Any], sens: Dict[str, Any]) -> Path:
    out_file = out_dir / cfg.get("report_file", "REPORT.txt")
    with out_file.open("w", encoding="utf-8") as w:
        w.write("AUDIT — PANBuster & Rétention\n")
        w.write("=" * 80 + "\n\n")
        w.write(f"Généré le : {now_utc().isoformat()} (UTC)\n")
        w.write(f"Dossier de sortie : {out_dir}\n\n")

        w.write("[1] PANBUSTER (CSV)\n")
        w.write("-" * 80 + "\n")
        w.write(f"Fichiers lus          : {len(pan.get('files', []))}\n")
        w.write(f"Total lignes (toutes) : {pan.get('total_rows', 0)}\n")
        w.write(f"Lignes retenues       : {pan.get('flagged_count', 0)}\n")
        w.write(f"Détail : {pan.get('out', '')}\n\n")

        w.write("[2] INVENTAIRES (listings)\n")
        w.write("-" * 80 + "\n")
        w.write(f"Entrées parseées      : {inv_count} (chemin + mtime)\n\n")

        w.write("[3] RÉTENTION\n")
        w.write("-" * 80 + "\n")
        for r in cfg.get("retention_rules", []):
            w.write(f"  - {r['path']:12s} → max {r['max_age_days']} jours\n")
        w.write(f"\nFichiers hors rétention : {ret.get('count', 0)}\n")
        w.write(f"Détail : {ret.get('out', '')}\n\n")

        w.write("[4] SENSIBLES & SIGNATURES\n")
        w.write("-" * 80 + "\n")
        w.write(f"Tree (sensibles)  : {sens.get('tree', '')}\n")
        w.write(f"Signatures (.rspf/.reqf/.gpg) trouvées : {sens.get('sig_count', 0)}\n")
        w.write(f"Détail signatures : {sens.get('signatures', '')}\n")
    return out_file

# -------------
# Entrée/Sortie
# -------------

def dump_default_config(path: Path) -> None:
    if yaml is None:
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False, allow_unicode=True), encoding="utf-8")


# -----
# Main
# -----

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Audit PANBuster & Rétention — sorties lisibles + ls -lR")
    ap.add_argument("--config", type=Path, help="Fichier de configuration (YAML ou JSON)")
    ap.add_argument("--init-config", type=Path, help="Génère un modèle de configuration et quitte")
    ap.add_argument("--out", type=Path, help="Dossier racine des sorties (écrase output.dir)")
    args = ap.parse_args(argv)

    if args.init_config:
        dump_default_config(args.init_config)
        print(f"Modèle de configuration écrit: {args.init_config}")
        return 0

    cfg = load_config(args.config) if args.config else json.loads(json.dumps(DEFAULT_CONFIG))

    out_base = Path(cfg.get("output", {}).get("dir", "./out"))
    if args.out:
        out_base = args.out
    stamp = now_utc().strftime("%Y%m%d_%H%M%S")
    out_dir = out_base / f"report_{stamp}"
    ensure_dir(out_dir)

    # 1) PANBuster (CSV)
    pan = process_panbuster(cfg, out_dir)

    # 2) Listings → (path, epoch)
    entries = load_inventory_files(cfg)

    # 3) Rétention
    ret = check_retention(cfg, entries, out_dir)

    # 4) Sensibles & signatures
    sens = dump_sensitive_and_signatures(cfg, entries, out_dir)

    # 5) Rapport lisible
    report_path = write_human_report(cfg, out_dir, pan, len(entries), ret, sens)

    # Console
    print("\n=== RÉSUMÉ ===")
    print(f"Sorties dans : {out_dir}")
    print(f"PANBuster → {pan['out']}")
    print(f"Rétention → {ret['out']} ({ret['count']} fichiers)")
    print(f"Sensibles → {sens['tree']}")
    print(f"Signatures → {sens['signatures']} ({sens['sig_count']})")
    print(f"Rapport → {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
