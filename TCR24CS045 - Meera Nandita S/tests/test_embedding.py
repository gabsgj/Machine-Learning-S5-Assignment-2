from pathlib import Path
import json, sys, numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from embedding import CapabilityEmbedding
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"data"/"experimental_dataset.json").read_text())
caps={c["name"]:c for c in data["capabilities"]}
emb=CapabilityEmbedding.from_dataset(data)

def test_shapes():
    assert emb.encode_state(data["problems"][0]["initial_state"]).shape==(emb.dimension,)
    assert emb.encode_goal(data["problems"][0]["goal"]).shape==(emb.dimension,)
    assert emb.encode_capability(caps["MakePayment"]).shape==(emb.dimension,)

def test_compatibility():
    state_after_payment={"Course.selected":True,"Payment.status":"SUCCESS"}
    assert emb.compatibility(caps["MakePayment"],caps["EnrollStudent"],state_after_payment)>=0.75
    assert emb.compatibility(caps["MakePayment"],caps["CancelCourse"],state_after_payment)<0.75

def test_composition():
    v=emb.compose([caps[x] for x in ["SelectCourse","MakePayment","EnrollStudent","SendNotification"]])
    assert np.isclose(np.linalg.norm(v),1.0)

def test_alternatives():
    s=emb.similarity(emb.encode_capability(caps["EnrollStudent"]),
                     emb.encode_capability(caps["ManualEnrollStudent"]))
    assert s>0.2

def test_goal_relevance_space():
    g=emb.encode_goal(data["problems"][0]["goal"])
    c=emb.encode_capability(caps["SendNotification"])
    assert emb.similarity(c,g)>0

if __name__=="__main__":
    for fn in [test_shapes,test_compatibility,test_composition,test_alternatives,test_goal_relevance_space]:
        fn()
    print("ALL TESTS PASSED")
