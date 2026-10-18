import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
import pandas as pd
from common import CreateOrder, MakePayment, CancelCart, compatibility, input_output_compatibility, is_composable

results = [
    {"Capability": "CreateOrder -> MakePayment", "Precondition Compatibility": compatibility(CreateOrder, MakePayment), "Input-Output Compatibility": input_output_compatibility(CreateOrder, MakePayment), "Composable": is_composable(CreateOrder, MakePayment)},
    {"Capability": "CreateOrder -> CancelCart", "Precondition Compatibility": compatibility(CreateOrder, CancelCart), "Input-Output Compatibility": input_output_compatibility(CreateOrder, CancelCart), "Composable": is_composable(CreateOrder, CancelCart)}
]
data = pd.DataFrame(results)
print("EXPERIMENT 1: CAPABILITY COMPATIBILITY")
print(data.to_string(index=False))
data.to_csv(Path(__file__).resolve().parents[1] / "results" / "experiment1_results.csv", index=False)
plt.figure(figsize=(8, 5))
plt.bar(data["Capability"], data["Precondition Compatibility"])
plt.ylim(0, 1.1)
plt.ylabel("Compatibility Score")
plt.title("Capability Compatibility")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(Path(__file__).resolve().parents[1] / "results" / "experiment1_compatibility.png")
plt.show()
