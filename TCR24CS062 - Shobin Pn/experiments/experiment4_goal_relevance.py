import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
import pandas as pd
from common import CAPABILITIES, goal, goal_relevance

rows = []
for capability in CAPABILITIES:
    rows.append({"Capability": capability.name, "Goal Relevance": goal_relevance(capability, goal)})
data = pd.DataFrame(rows)
print("EXPERIMENT 4: IRRELEVANT CAPABILITIES")
print(data.to_string(index=False))
data.to_csv(Path(__file__).resolve().parents[1] / "results" / "experiment4_results.csv", index=False)
plt.figure(figsize=(8, 5))
plt.bar(data["Capability"], data["Goal Relevance"])
plt.ylim(0, 1.1)
plt.ylabel("Goal Relevance")
plt.title("Capability Relevance to Goal")
plt.xticks(rotation=25)
plt.tight_layout()
plt.savefig(Path(__file__).resolve().parents[1] / "results" / "experiment4_goal_relevance.png")
plt.show()
