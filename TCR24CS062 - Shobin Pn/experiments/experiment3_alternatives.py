import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pandas as pd
from common import Capability, encode_capability, similarity

api = Capability("CreateOrder_API", "API", ["cart_id"], ["order_id"], {"cart_exists": True, "cart_nonempty": True}, {"order_exists": True}, ["Database", "Network"], 0.02, 0.99, 1)
database = Capability("CreateOrder_DATABASE", "DATABASE", ["cart_id"], ["order_id"], {"cart_exists": True, "cart_nonempty": True}, {"order_exists": True}, ["Database"], 0.01, 0.995, 1)
gui = Capability("CreateOrder_GUI", "GUI", ["cart_id"], ["order_id"], {"cart_exists": True, "cart_nonempty": True}, {"order_exists": True}, ["Database", "Network"], 0.03, 0.98, 1)
capabilities = [api, database, gui]
rows = []
for capability in capabilities:
    rows.append({"Capability": capability.name, "Type": capability.capability_type, "Effect": str(capability.effects), "Similarity with API": similarity(encode_capability(api), encode_capability(capability))})
data = pd.DataFrame(rows)
print("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")
print(data.to_string(index=False))
data.to_csv(Path(__file__).resolve().parents[1] / "results" / "experiment3_results.csv", index=False)
