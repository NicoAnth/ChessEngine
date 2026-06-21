// Spike Étape 2B — benchmark perf de Stockfish WASM (single-thread) en Node.
// Mesure la MÊME charge que le natif (34 positions de l'Opera Game, depth 16,
// MultiPV 3) pour comparer au backend natif (~362 ms/analyse, ~11.9s total).
// Node + V8 + WASM single-thread = proxy fidèle et CONSERVATEUR du navigateur sans
// COOP/COEP (le multi-thread navigateur serait plus rapide).
//
// Le moteur écrit sur stdout directement : on intercepte process.stdout pour
// détecter 'bestmove' (fin d'analyse) et MASQUER le bruit ; le résumé va sur stderr.
const initEngine = require('stockfish');
const fens = require('./fens.json');

const DEPTH = 16;
const MPV = 3;
const log = (...a) => process.stderr.write(a.join(' ') + '\n');

let resolveCurrent = null;
const origWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = (chunk) => {
  const s = typeof chunk === 'string' ? chunk : chunk.toString();
  if (s.indexOf('bestmove') !== -1 && resolveCurrent) {
    const r = resolveCurrent;
    resolveCurrent = null;
    r();
  }
  return true; // swallow engine output
};

const send = (engine, c) => engine.ccall('command', null, ['string'], [c]);

function analyze(engine, fen) {
  return new Promise((resolve) => {
    resolveCurrent = resolve;
    send(engine, 'position fen ' + fen);
    send(engine, 'go depth ' + DEPTH);
  });
}

(async () => {
  log(`Charge: ${fens.length} positions, depth ${DEPTH}, MultiPV ${MPV}  (natif: ~11.9s, ~362 ms/analyse)\n`);
  for (const build of ['lite-single', 'single']) {
    try {
      const engine = await initEngine(build);
      send(engine, 'uci');
      send(engine, 'setoption name MultiPV value ' + MPV);
      send(engine, 'isready');
      await new Promise((r) => setTimeout(r, 500));
      const t = Date.now();
      for (const f of fens) await analyze(engine, f);
      const ms = Date.now() - t;
      const per = Math.round(ms / fens.length);
      log(
        `${build.padEnd(12)} -> ${(ms / 1000).toFixed(1)}s total | ${per} ms/analyse | ` +
        `~${Math.round((per * 80) / 1000)}s pour 80 demi-coups | ${(per / 362).toFixed(1)}x le natif`
      );
      if (typeof engine.terminate === 'function') engine.terminate();
    } catch (e) {
      log(`${build} -> ERREUR: ${e.message || e}`);
    }
  }
  process.stdout.write = origWrite;
  process.exit(0);
})();
