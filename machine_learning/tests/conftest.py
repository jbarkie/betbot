import sys
from pathlib import Path

# Add the project root to sys.path so machine_learning.* and api.* imports work
# regardless of which directory pytest is invoked from.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
