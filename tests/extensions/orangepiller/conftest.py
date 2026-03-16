import sys
from pathlib import Path

# Ensure the project root is on sys.path so `orangepiller` package resolves
# to the extension directory, not to this test subpackage.
_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
