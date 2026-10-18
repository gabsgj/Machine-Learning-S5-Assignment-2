from pathlib import Path

from .experiments import run_all


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    dataset = project_root / "data" / "application.json"
    results = project_root / "results"
    run_all(str(dataset), str(results))
