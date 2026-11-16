"""Lets the tests `import app`, `import content`, etc. no matter where pytest is run from."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
