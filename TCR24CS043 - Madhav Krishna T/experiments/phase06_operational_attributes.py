"""Experiment 5 for SCE-128 v2. Reuses the controlled perturbations and reports v2 block behavior."""
from __future__ import annotations
import copy, json, math
from pathlib import Path
from src.dataset import load_dataset
from src.encoder import capability_blocks, cosine, encode_capability
from src.final_model import operational_similarity_v2
from src.schema import Capability, QualityAttributes
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'expanded_application.json'; OUT=ROOT/'results'/'final_v2_1'/'phase06_operational_attributes.json'; REPORT=ROOT/'results'/'final_v2_1'/'phase06_operational_attributes.md'

def clone_with(cap, **kwargs):
    c=copy.deepcopy(cap)
    for k,v in kwargs.items():
        if k in {'quality'}: c.quality=v
        else: setattr(c,k,v)
    return c

def main():
    _,caps=load_dataset(DATA); base=caps['C5']; base_vec=encode_capability(base); base_blocks=capability_blocks(base_vec)
    q=base.quality
    variants=[
        ('high_monetary_cost',clone_with(base,quality=QualityAttributes(q.execution_time_ms,q.resource_cost,(q.monetary_cost or 0.0)*10,q.risk,q.energy_cost))),
        ('low_reliability',clone_with(base,reliability=0.70)),
        ('unavailable',clone_with(base,availability=0)),
        ('high_risk',clone_with(base,quality=QualityAttributes(q.execution_time_ms,q.resource_cost,q.monetary_cost,min(1.0,(q.risk or 0.0)+0.50),q.energy_cost))),
    ]
    rows=[]
    for name,var in variants:
        v=encode_capability(var); b=capability_blocks(v)
        non_names=[k for k in base_blocks if k!='operational']
        non=np_mean([cosine(base_blocks[k],b[k]) for k in non_names])
        rows.append({'variant':name,'whole_cosine':cosine(base_vec,v),'operational_cosine':cosine(base_blocks['operational'],b['operational']),'non_operational_mean_cosine':non})
    payload={'experiment':'Experiment 5 - Operational Attributes','model':'SCE-128-v2','rows':rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    lines=['# Experiment 5 — SCE-128 v2','', '| Variant | Whole cosine | Operational cosine | Non-operational cosine |','|---|---:|---:|---:|']
    for r in rows: lines.append(f"| {r['variant']} | {r['whole_cosine']:.4f} | {r['operational_cosine']:.4f} | {r['non_operational_mean_cosine']:.4f} |")
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('=== PHASE 06 — OPERATIONAL ATTRIBUTES ===')
    for r in rows: print(f"  {r['variant']}: whole={r['whole_cosine']:.4f} operational={r['operational_cosine']:.4f} non_operational={r['non_operational_mean_cosine']:.4f}")
    print(f"JSON: {OUT}"); print(f"Report: {REPORT}")

def np_mean(xs): return sum(xs)/len(xs) if xs else 0.0
if __name__=='__main__': main()
