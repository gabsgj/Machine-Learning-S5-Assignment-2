"""Phase 05 — Goal Relevance and Irrelevant Capabilities.

Uses the final hybrid embedding + symbolic reachability relevance score."""
from __future__ import annotations
import json
from pathlib import Path
from src.evaluation import rank_auc
from src.evaluation import mean
from src.dataset import load_dataset
from src.schema import Condition
from src.final_model import goal_relevance_v2

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'expanded_application.json'; OUT=ROOT/'results'/'final_v2_1'/'phase05_goal_relevance.json'; REPORT=ROOT/'results'/'final_v2_1'/'phase05_goal_relevance.md'

def main():
    raw,caps=load_dataset(DATA); goal=[Condition(**x) for x in raw['goal']]
    rows=[]
    for cid,label in raw['goal_relevance'].items():
        score=goal_relevance_v2(caps[cid],goal,caps)
        rows.append({'id':cid,'name':caps[cid].name,'ground_truth_relevant':bool(label),**score})
    ranked=sorted(rows,key=lambda r:r['score'],reverse=True)
    pos=[r['score'] for r in rows if r['ground_truth_relevant']]; neg=[r['score'] for r in rows if not r['ground_truth_relevant']]
    summary={'relevant_mean':mean(pos),'irrelevant_mean':mean(neg),'score_gap':mean(pos)-mean(neg),'auc':rank_auc([r['ground_truth_relevant'] for r in rows],[r['score'] for r in rows]),
             'precision_at_5':mean([1 if r['ground_truth_relevant'] else 0 for r in ranked[:5]]),'precision_at_10':mean([1 if r['ground_truth_relevant'] else 0 for r in ranked[:10]])}
    payload={'experiment':'Experiment 4 - Irrelevant Capabilities','model':'SCE-128-v2','rows':rows,'ranked':ranked,'summary':summary}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    lines=['# Experiment 4 — SCE-128 v2','',f"- Relevant mean: **{summary['relevant_mean']:.4f}**",f"- Irrelevant mean: **{summary['irrelevant_mean']:.4f}**",f"- Gap: **{summary['score_gap']:.4f}**",f"- AUC: **{summary['auc']:.4f}**",f"- Precision@5: **{summary['precision_at_5']:.4f}**",f"- Precision@10: **{summary['precision_at_10']:.4f}**","",
           '| Rank | ID | Capability | Relevant | Semantic | Exact goal support | Reachability | V2 score |','|---:|---|---|:---:|---:|---:|---:|---:|']
    for i,r in enumerate(ranked,1): lines.append(f"| {i} | {r['id']} | {r['name']} | {r['ground_truth_relevant']} | {r['semantic_effect_goal']:.4f} | {r['exact_goal_effect_coverage']:.4f} | {r['backward_goal_reachability']:.1f} | {r['score']:.4f} |")
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('=== PHASE 05 — GOAL RELEVANCE / IRRELEVANT CAPABILITIES ===')
    print(f"Relevant mean={summary['relevant_mean']:.4f} Irrelevant mean={summary['irrelevant_mean']:.4f} Gap={summary['score_gap']:.4f}")
    print(f"AUC={summary['auc']:.4f} Precision@5={summary['precision_at_5']:.4f} Precision@10={summary['precision_at_10']:.4f}")
    print('Top ranked capabilities:')
    for i,r in enumerate(ranked[:10],1): print(f"  {i}. {r['id']} {r['name']}: score={r['score']:.4f} relevant={r['ground_truth_relevant']} reach={int(r['backward_goal_reachability'])}")
    print(f"JSON: {OUT}"); print(f"Report: {REPORT}")
if __name__=='__main__': main()
