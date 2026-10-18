"""Phase 04 — Alternative Implementations."""
from __future__ import annotations
import json
from pathlib import Path
from src.dataset import load_dataset
from src.encoder import encode_capability
from src.final_model import functional_similarity_v2, implementation_similarity_v2, operational_similarity_v2, blockwise_similarity_v2
from src.evaluation import exact_contract_match, mean

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'expanded_application.json'; OUT=ROOT/'results'/'final_v2_1'/'phase04_alternative_implementations.json'; REPORT=ROOT/'results'/'final_v2_1'/'phase04_alternative_implementations.md'

def main():
    _,caps=load_dataset(DATA); group=['C4_API','C4_DB','C4_GUI']; negatives=['C5','C12','C14']
    V={i:encode_capability(caps[i]) for i in group+negatives}
    def rec(a,b):
        return {'a':a,'b':b,'contract':exact_contract_match(caps[a],caps[b]),
                'functional':functional_similarity_v2(V[a],V[b]),
                'implementation':implementation_similarity_v2(V[a],V[b]),
                'operational':operational_similarity_v2(V[a],V[b]),
                'overall_v2':0.85*functional_similarity_v2(V[a],V[b])+0.10*implementation_similarity_v2(V[a],V[b])+0.05*operational_similarity_v2(V[a],V[b]),
                'blockwise_all':blockwise_similarity_v2(V[a],V[b])}
    within=[rec(a,b) for i,a in enumerate(group) for b in group[i+1:]]
    negative=[rec(a,b) for a in group for b in negatives]
    summary={'within_functional_mean':mean([r['functional'] for r in within]),
             'negative_functional_mean':mean([r['functional'] for r in negative]),
             'within_overall_v2_mean':mean([r['overall_v2'] for r in within]),
             'negative_overall_v2_mean':mean([r['overall_v2'] for r in negative]),
             'overall_v2_gap':mean([r['overall_v2'] for r in within])-mean([r['overall_v2'] for r in negative]),
             'within_implementation_mean':mean([r['implementation'] for r in within])}
    payload={'experiment':'Experiment 3 - Alternative Implementations','model':'SCE-128-v2','within':within,'negative':negative,'summary':summary}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    lines=['# Experiment 3 — SCE-128 v2','',f"- Functional gap: **{summary['within_functional_mean']-summary['negative_functional_mean']:.4f}**",
           f"- v2 overall gap: **{summary['overall_v2_gap']:.4f}**",
           f"- Within-group implementation-block cosine: **{summary['within_implementation_mean']:.4f}**","",
           '| Pair | Contract | Functional | Implementation | Operational | Overall v2 |', '|---|:---:|---:|---:|---:|---:|']
    for r in within: lines.append(f"| {r['a']} ↔ {r['b']} | {r['contract']} | {r['functional']:.4f} | {r['implementation']:.4f} | {r['operational']:.4f} | {r['overall_v2']:.4f} |")
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('=== PHASE 04 — ALTERNATIVE IMPLEMENTATIONS ===')
    for r in within: print(f"  {r['a']} <-> {r['b']}: contract={r['contract']} functional={r['functional']:.4f} implementation={r['implementation']:.4f} operational={r['operational']:.4f} overall_v2={r['overall_v2']:.4f}")
    print(f"Negative-control functional mean={summary['negative_functional_mean']:.4f}")
    print(f"Negative-control overall v2 mean={summary['negative_overall_v2_mean']:.4f}")
    print(f"Overall v2 gap={summary['overall_v2_gap']:.4f}")
    print(f"JSON: {OUT}")
    print(f"Report: {REPORT}")
if __name__=='__main__': main()
