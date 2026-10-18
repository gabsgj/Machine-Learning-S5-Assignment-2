import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import initial_state, goal, encode_state, encode_goal, encode_capability, similarity, CAPABILITIES

print("PCCST503 Assignment 2")
print("Vector Embedding for Capability Composition")
print("\nInitial State:")
print(initial_state)
print("\nGoal:")
print(goal)
print("\nState vector:")
print(encode_state(initial_state))
print("\nGoal vector:")
print(encode_goal(goal))
print("\nState-goal similarity:", round(similarity(encode_state(initial_state), encode_goal(goal)), 4))
print("\nCapability vector lengths:")
for capability in CAPABILITIES:
    print(capability.name, ":", len(encode_capability(capability)))
print("\nRun the experiment files separately.")
