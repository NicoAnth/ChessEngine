import os
import sys
from pathlib import Path

# Ensure src is in path so we can import 'src' modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
