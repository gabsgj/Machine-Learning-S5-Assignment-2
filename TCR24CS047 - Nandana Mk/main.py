from experiments.experiment1 import run as experiment1
from experiments.experiment2 import run as experiment2
from experiments.experiment3 import run as experiment3
from experiments.experiment4 import run as experiment4
from experiments.experiment5 import run as experiment5
from evaluation.evaluator import Evaluator


def main():

    print("=" * 70)
    print("CAPABILITY EMBEDDING PROJECT")
    print("=" * 70)

    print("\nRunning Experiment 1...\n")
    experiment1()

    print("\nRunning Experiment 2...\n")
    experiment2()

    print("\nRunning Experiment 3...\n")
    experiment3()

    print("\nRunning Experiment 4...\n")
    experiment4()

    print("\nRunning Experiment 5...\n")
    experiment5()

    print("\nRunning Final Evaluation...\n")
    Evaluator.evaluate()

    print("\n" + "=" * 70)
    print("PROJECT EXECUTED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()