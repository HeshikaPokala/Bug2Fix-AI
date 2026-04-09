from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mini_repo.calculator import average

print("Running minimal repro...")
print("Input:", [])
print("Expected: 0.0 (graceful behavior)")
print("Actual:")
print(average([]))
