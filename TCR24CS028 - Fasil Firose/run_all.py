"""
Single entry point: runs the experiment suite, the dataset export, and the
similarity/compatibility matrix generation, in that order.

    python3 run_all.py
"""

import subprocess
import sys


def run(script):
    print(f"\n########## running {script} ##########")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"!!! {script} FAILED (exit code {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run("experiments.py")
    run("export_dataset.py")
    run("matrices.py")
    print("\nAll steps completed successfully.")
