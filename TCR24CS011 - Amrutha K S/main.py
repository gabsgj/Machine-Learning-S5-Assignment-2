import json
from src.models import Capability, InputSpec, OutputSpec, Cost
from src.encoder import CapabilityEncoder
from src.experiments import run_all

def load_data():
    with open("data/capabilities.json", encoding="utf-8") as f:
        return json.load(f)

def create_capabilities(data):
    result={}
    for x in data["capabilities"]:
        result[x["id"]]=Capability(
            id=x["id"], name=x["name"], type=x["type"],
            inputs=[InputSpec(**i) for i in x["inputs"]],
            outputs=[OutputSpec(**o) for o in x["outputs"]],
            preconditions=x["preconditions"], effects=x["effects"],
            constraints=x["constraints"], resources=x["resources"],
            cost=Cost(**x["cost"]), reliability=x["reliability"],
            availability=x["availability"], mechanism=x["mechanism"])
    return result

def main():
    data=load_data(); capabilities=create_capabilities(data)
    encoder=CapabilityEncoder(); matrix=encoder.fit(list(capabilities.values()))
    print("PCCST503 Assignment 2 - Vector Embedding for Capability Composition")
    print(f"Capabilities: {len(capabilities)}")
    print(f"Embedding dimension: {matrix.shape[1]}")
    print("\nRunning experiments...")
    run_all(capabilities,encoder,"results")
    print("Experiments completed.")
    print("Results saved in the results/ folder.")

if __name__ == "__main__":
    main()
