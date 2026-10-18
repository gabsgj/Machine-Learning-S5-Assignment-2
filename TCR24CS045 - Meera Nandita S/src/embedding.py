"""
PCCST503 Assignment 2
Problem-specific vector embedding for capability composition.

The vector has a shared condition space so that:
  state conditions <-> capability preconditions/effects <-> goal conditions
can be compared directly.

Compatibility is kept separate from cosine similarity because semantic
resemblance alone cannot prove executable composition.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Sequence
import numpy as np

def _unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n else v

def _cosine(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float)
    den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den else 0.0

@dataclass
class CapabilityEmbedding:
    condition_vocabulary: Dict[str,int]
    capability_vocabulary: Dict[str,int]
    operational_names: Sequence[str]=(
        "time_ms","resource","money","risk","energy","reliability","availability"
    )

    @classmethod
    def from_dataset(cls,dataset):
        conditions=set()
        cap_tokens=set()

        for p in dataset["problems"]:
            for k,v in p["initial_state"].items():
                conditions.add(f"{k}={v}")
            for k,v in p["goal"].items():
                conditions.add(f"{k}={v}")

        for c in dataset["capabilities"]:
            cap_tokens.add("TYPE:"+c["type"])
            for k,v in c["preconditions"].items():
                conditions.add(f"{k}={v}")
                cap_tokens.add(f"PRE:{k}={v}")
            for k,v in c["effects"].items():
                conditions.add(f"{k}={v}")
                cap_tokens.add(f"EFF:{k}={v}")
            for x in c["inputs"]:
                cap_tokens.add(f"IN_TYPE:{x['type']}")
                cap_tokens.add(f"IN_NAME:{x['name']}")
            for x in c["outputs"]:
                cap_tokens.add(f"OUT_TYPE:{x['type']}")
                cap_tokens.add(f"OUT_NAME:{x['name']}")
            for x in c["constraints"]:
                cap_tokens.add("CON:"+x)
            for x in c["resources"]:
                cap_tokens.add("RES:"+x)
            for k,v in c["mechanism"].items():
                cap_tokens.add(f"MECH:{k}={v}")

        return cls(
            {t:i for i,t in enumerate(sorted(conditions))},
            {t:i for i,t in enumerate(sorted(cap_tokens))}
        )

    @property
    def condition_dim(self):
        return len(self.condition_vocabulary)
    @property
    def capability_dim(self):
        return len(self.capability_vocabulary)
    @property
    def dimension(self):
        return self.condition_dim+self.capability_dim+len(self.operational_names)

    def _base(self):
        return np.zeros(self.dimension,float)
    def _cap_off(self):
        return self.condition_dim
    def _op_off(self):
        return self.condition_dim+self.capability_dim

    def _put_condition(self,v,key,weight=1.0):
        idx=self.condition_vocabulary.get(key)
        if idx is not None:
            v[idx]+=weight

    def encode_state(self,state):
        v=self._base()
        for k,val in state.items():
            self._put_condition(v,f"{k}={val}",1.0)
        return _unit(v)

    def encode_goal(self,goal):
        v=self._base()
        for k,val in goal.items():
            self._put_condition(v,f"{k}={val}",1.0)
        return _unit(v)

    def _encode_cap_raw(self,c):
        v=self._base()
        off=self._cap_off()
        def put(token,w=1.0):
            idx=self.capability_vocabulary.get(token)
            if idx is not None:
                v[off+idx]+=w

        # Effects and preconditions also occupy the shared condition block.
        for k,val in c["preconditions"].items():
            self._put_condition(v,f"{k}={val}",2.0)
            put(f"PRE:{k}={val}",2.0)
        for k,val in c["effects"].items():
            self._put_condition(v,f"{k}={val}",2.5)
            put(f"EFF:{k}={val}",2.5)

        put("TYPE:"+c["type"],1.5)
        for x in c["inputs"]:
            put(f"IN_TYPE:{x['type']}",1.2); put(f"IN_NAME:{x['name']}",0.7)
        for x in c["outputs"]:
            put(f"OUT_TYPE:{x['type']}",1.4); put(f"OUT_NAME:{x['name']}",0.8)
        for x in c["constraints"]: put("CON:"+x,0.8)
        for x in c["resources"]: put("RES:"+x,0.8)
        for k,val in c["mechanism"].items(): put(f"MECH:{k}={val}",0.4)

        op=c["cost"]
        vals=[
            np.log1p(op["time_ms"])/np.log1p(10000),
            op["resource"]/10.0, op["money"], op["risk"],
            op["energy"]/10.0, c["reliability"], c["availability"]
        ]
        for i,val in enumerate(vals): v[self._op_off()+i]=val
        return v

    def encode_capability(self,c):
        if "components" in c: return self.compose(c["components"])
        return _unit(self._encode_cap_raw(c))

    def compatibility_details(self,c1,c2,state_after_c1=None):
        p=c2["preconditions"]
        # A precondition may be established by C1's effect OR already remain
        # true in the state after C1. This models persistence of state variables.
        matched=0
        for k,v in p.items():
            if c1["effects"].get(k)==v:
                matched += 1
            elif state_after_c1 is not None and state_after_c1.get(k)==v:
                matched += 1
        pre_score=matched/len(p) if p else 1.0

        out_types={x["type"] for x in c1["outputs"]}
        in_types={x["type"] for x in c2["inputs"]}
        io=1.0 if out_types & in_types else 0.0

        r1,r2=set(c1["resources"]),set(c2["resources"])
        resource_overlap=len(r1&r2)/len(r2) if r2 else 0.0

        score=0.75*pre_score+0.15*io+0.10*resource_overlap
        # External inputs (student_id/course_id) can be supplied by the
        # application context. Precondition satisfaction is therefore the
        # primary composability test; IO match is an additional dependency.
        composable=(pre_score==1.0)
        return {
            "precondition_score":pre_score,
            "io_score":io,
            "resource_overlap":resource_overlap,
            "compatibility_score":score,
            "composable":composable
        }

    def compatibility(self,c1,c2,state_after_c1=None):
        return self.compatibility_details(c1,c2,state_after_c1)["compatibility_score"]

    def compose(self,capabilities):
        if not capabilities: return np.zeros(self.dimension)
        raw=np.zeros(self.dimension)
        total={k:0.0 for k in ["time_ms","resource","money","risk","energy"]}
        rel=1.0; avail=1.0
        for i,c in enumerate(capabilities):
            raw+=(1+0.05*i)*self._encode_cap_raw(c)
            for k in total: total[k]+=c["cost"][k]
            rel*=c["reliability"]; avail=min(avail,c["availability"])
        vals=[
            np.log1p(total["time_ms"])/np.log1p(10000),
            total["resource"]/10.0,total["money"],total["risk"]/max(1,len(capabilities)),
            total["energy"]/10.0,rel,avail
        ]
        for i,val in enumerate(vals): raw[self._op_off()+i]=val
        return _unit(raw)

    def similarity(self,x,y): return _cosine(x,y)

    def goal_relevance(self,capability,goal):
        if not goal:return 0.0
        return sum(1 for k,v in goal.items() if capability["effects"].get(k)==v)/len(goal)

    def state_applicability(self,state,capability):
        p=capability["preconditions"]
        return (sum(1 for k,v in p.items() if state.get(k)==v)/len(p)) if p else 1.0
