from pathlib import Path
import json, csv, time, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from embedding import CapabilityEmbedding

def load():
    return json.loads((ROOT/"data"/"experimental_dataset.json").read_text(encoding="utf-8"))

def write_csv(name, rows):
    if not rows: return
    with open(ROOT/"results"/name, "w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def main():
    data=load()
    caps={c["name"]:c for c in data["capabilities"]}
    emb=CapabilityEmbedding.from_dataset(data)
    print("="*72)
    print("PCCST503 ASSIGNMENT 2 - ONLINE COURSE ENROLLMENT")
    print("Problem-specific vector embedding and capability composition")
    print("="*72)
    print("Embedding dimension:", emb.dimension)

    # E1: compatibility
    print("\n[Experiment 1] Capability compatibility")
    rows=[]
    tests=[
        ("SelectCourse","MakePayment",
         {"Student.registered":True,"Course.selected":True,"Course.seats_available":True,
          "Payment.status":"NOT_PAID","Enrollment.status":"NOT_ENROLLED","Notification.sent":False}),
        ("MakePayment","EnrollStudent",
         {"Student.registered":True,"Course.selected":True,"Course.seats_available":True,
          "Payment.status":"SUCCESS","Enrollment.status":"NOT_ENROLLED","Notification.sent":False}),
        ("MakePayment","CancelCourse",
         {"Student.registered":True,"Course.selected":True,"Course.seats_available":True,
          "Payment.status":"SUCCESS","Enrollment.status":"NOT_ENROLLED","Notification.sent":False}),
        ("ViewCourseDetails","EnrollStudent",
         {"Student.registered":True,"Course.selected":False,"Course.seats_available":True,
          "Payment.status":"NOT_PAID","Enrollment.status":"NOT_ENROLLED","Notification.sent":False})
    ]
    for a,b,state_after in tests:
        d=emb.compatibility_details(caps[a],caps[b],state_after)
        print(f"{a:22s} -> {b:22s} | score={d['compatibility_score']:.3f} | composable={d['composable']}")
        rows.append({"c1":a,"c2":b,**{k:f"{v:.4f}" if isinstance(v,float) else v for k,v in d.items()}})
    write_csv("experiment1_compatibility.csv",rows)

    # E2: composition
    print("\n[Experiment 2] Capability composition")
    chain=["SelectCourse","MakePayment","EnrollStudent","SendNotification"]
    comp=emb.compose([caps[x] for x in chain])
    rows=[]
    for x in chain:
        s=emb.similarity(emb.encode_capability(caps[x]),comp)
        rows.append({"atomic_capability":x,"similarity_to_composite":f"{s:.4f}"})
        print(f"{x:22s} similarity={s:.4f}")
    write_csv("experiment2_composition.csv",rows)

    # E3: alternatives
    print("\n[Experiment 3] Alternative implementations")
    pairs=[("EnrollStudent","ManualEnrollStudent")]
    rows=[]
    for a,b in pairs:
        s=emb.similarity(emb.encode_capability(caps[a]),emb.encode_capability(caps[b]))
        print(f"{a} vs {b}: functional similarity={s:.4f}")
        rows.append({"capability_1":a,"capability_2":b,"functional_similarity":f"{s:.4f}",
                     "mechanisms":"DATABASE vs GUI"})
    write_csv("experiment3_alternatives.csv",rows)

    # E4: irrelevant capabilities
    print("\n[Experiment 4] Goal relevance")
    goal=data["problems"][0]["goal"]
    relevant=["MakePayment","EnrollStudent","SendNotification"]
    irrelevant=["ViewCourseDetails","CancelCourse","ScholarshipVerification"]
    rows=[]
    for x in relevant+irrelevant:
        rel=emb.goal_relevance(caps[x],goal)
        sim=emb.similarity(emb.encode_capability(caps[x]),emb.encode_goal(goal))
        category="relevant" if x in relevant else "irrelevant"
        print(f"{x:22s} {category:10s} effect-goal={rel:.3f} vector-goal={sim:.4f}")
        rows.append({"capability":x,"category":category,
                     "effect_goal_relevance":f"{rel:.4f}",
                     "vector_goal_similarity":f"{sim:.4f}"})
    write_csv("experiment4_goal_relevance.csv",rows)

    # E5: operational attributes
    print("\n[Experiment 5] Operational attributes")
    base=caps["MakePayment"]
    variants=[]
    fast=json.loads(json.dumps(base)); fast["name"]="MakePayment_Faster"; fast["cost"]["time_ms"]=100
    unreliable=json.loads(json.dumps(base)); unreliable["name"]="MakePayment_LessReliable"; unreliable["reliability"]=0.80
    unavailable=json.loads(json.dumps(base)); unavailable["name"]="MakePayment_Unavailable"; unavailable["availability"]=0
    variants=[fast,unreliable,unavailable]
    rows=[]
    bv=emb.encode_capability(base)
    for v in variants:
        s=emb.similarity(bv,emb.encode_capability(v))
        print(f"Base vs {v['name']}: similarity={s:.4f}")
        rows.append({"base":"MakePayment","variant":v["name"],
                     "similarity":f"{s:.4f}",
                     "time_ms":v["cost"]["time_ms"],
                     "reliability":v["reliability"],
                     "availability":v["availability"]})
    write_csv("experiment5_operational.csv",rows)

    # E6: consistency across four formally specified problems
    print("\n[Experiment 6] Cross-problem consistency")
    rows=[]
    for p in data["problems"]:
        chain=[caps[x] for x in p["composition"]]
        cvec=emb.compose(chain)
        goalvec=emb.encode_goal(p["goal"])
        rows.append({
            "problem":p["id"],
            "title":p["title"],
            "number_of_capabilities":len(chain),
            "composite_goal_similarity":f"{emb.similarity(cvec,goalvec):.4f}",
            "composite_norm":f"{np.linalg.norm(cvec):.4f}"
        })
        print(f"{p['id']:32s} goal similarity={rows[-1]['composite_goal_similarity']}")
    write_csv("experiment6_consistency.csv",rows)

    # Efficiency measurement
    print("\n[Efficiency] Encoding/composition cost")
    sample=caps["EnrollStudent"]
    n=2000
    t0=time.perf_counter()
    for _ in range(n): emb.encode_capability(sample)
    enc_ms=(time.perf_counter()-t0)*1000/n
    chain=[caps[x] for x in ["SelectCourse","MakePayment","EnrollStudent","SendNotification"]]
    t0=time.perf_counter()
    for _ in range(n): emb.compose(chain)
    comp_ms=(time.perf_counter()-t0)*1000/n
    eff=[{"operation":"encode_capability","average_ms":f"{enc_ms:.5f}"},
         {"operation":"compose_4_capabilities","average_ms":f"{comp_ms:.5f}"}]
    write_csv("efficiency.csv",eff)
    print(f"encode_capability average: {enc_ms:.5f} ms")
    print(f"compose(4) average:        {comp_ms:.5f} ms")

    # Save vectors for reproducibility
    vectors={}
    for name in caps:
        vectors[name]=emb.encode_capability(caps[name]).tolist()
    (ROOT/"results"/"capability_vectors.json").write_text(json.dumps(vectors,indent=2),encoding="utf-8")

    print("\nAll experiments completed. Results are in:", ROOT/"results")

if __name__=="__main__":
    main()
