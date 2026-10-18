import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pandas as pd
from common import CreateOrder, MakePayment, SendNotification, compatibility, input_output_compatibility, compose, encode_capability, similarity

chain = [CreateOrder, MakePayment, SendNotification]
print("EXPERIMENT 2: CAPABILITY COMPOSITION")
for i in range(len(chain) - 1):
    c1, c2 = chain[i], chain[i + 1]
    print(f"{c1.name} -> {c2.name}: precondition compatibility = {compatibility(c1, c2):.3f}")
    print(f"Input-output compatibility = {input_output_compatibility(c1, c2):.3f}")
composite = compose(chain)
print("\nComposite capability:")
composite.display()
composite_vector = encode_capability(composite)
rows = []
for capability in chain:
    rows.append({"Atomic Capability": capability.name, "Composite Similarity": similarity(composite_vector, encode_capability(capability))})
data = pd.DataFrame(rows)
print("\nSimilarity with atomic capabilities:")
print(data.to_string(index=False))
data.to_csv(Path(__file__).resolve().parents[1] / "results" / "experiment2_results.csv", index=False)
