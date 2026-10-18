import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
import pandas as pd
from common import CAPABILITIES

rows = []
for capability in CAPABILITIES:
    rows.append({"Capability": capability.name, "Cost": capability.cost, "Reliability": capability.reliability, "Availability": capability.availability})
data = pd.DataFrame(rows)
print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")
print(data.to_string(index=False))
data.to_csv(Path(__file__).resolve().parents[1] / "results" / "experiment5_results.csv", index=False)
plt.figure(figsize=(8, 5))
plt.bar(data["Capability"], data["Cost"])
plt.ylabel("Cost")
plt.title("Capability Cost")
plt.xticks(rotation=25)
plt.tight_layout()
plt.savefig(Path(__file__).resolve().parents[1] / "results" / "experiment5_cost.png")
plt.show()
plt.figure(figsize=(8, 5))
plt.bar(data["Capability"], data["Reliability"])
plt.ylim(0, 1.1)
plt.ylabel("Reliability")
plt.title("Capability Reliability")
plt.xticks(rotation=25)
plt.tight_layout()
plt.savefig(Path(__file__).resolve().parents[1] / "results" / "experiment5_reliability.png")
plt.show()
