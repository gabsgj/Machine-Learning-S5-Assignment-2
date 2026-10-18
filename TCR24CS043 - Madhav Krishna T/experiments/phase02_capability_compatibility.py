"""Phase 02 — Capability Compatibility.

Evaluates formal compatibility and embedding-derived compatibility evidence."""
from __future__ import annotations
import json
from pathlib import Path
from src.compatibility import compatibility
from src.dataset import load_dataset
from src.encoder import cosine, encode_capability
from src.compatibility import effect_precondition_scores, output_input_scores
from src.final_model import blockwise_similarity_v2, structural_relation_similarity_v2
from src.evaluation import binary_metrics, mean, rank_auc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "expanded_application.json"
OUT = ROOT / "results" / "final_v2_1" / "phase02_capability_compatibility.json"
REPORT = ROOT / "results" / "final_v2_1" / "phase02_capability_compatibility.md"

def main() -> None:
    raw, caps = load_dataset(DATA)
    vecs = {cid: encode_capability(c) for cid, c in caps.items()}
    labels=[]; formal=[]; raw_cos=[]; block_scores=[]; relation_scores=[]; rows=[]
    for rel in raw['expected_relations']:
        s,t = caps[rel['from']], caps[rel['to']]
        y = rel['relation']=='compatible'
        r = compatibility(s,t)
        labels.append(y); formal.append(r.compatible)
        raw_cos.append(cosine(vecs[s.id],vecs[t.id]))
        block_scores.append(blockwise_similarity_v2(vecs[s.id],vecs[t.id]))
        relation_scores.append(structural_relation_similarity_v2(s,t))
        _, pe_vec, _ = effect_precondition_scores(s,t)
        _, io_vec, _ = output_input_scores(s,t)
        proxy_v2 = 0.70 * pe_vec + 0.30 * io_vec
        rows.append({"from":s.id,"to":t.id,"expected":y,"formal_compatible":r.compatible,
                     "raw_cosine":raw_cos[-1],"blockwise_cosine":block_scores[-1],
                     "structural_relation_score":relation_scores[-1],"v2_compatibility_proxy":proxy_v2,"formal_score":r.score})
    m=binary_metrics(labels,formal)
    v2_proxy=[r['v2_compatibility_proxy'] for r in rows]
    payload={"experiment":"Experiment 1 - Capability Compatibility","model":"SCE-128-v2",
             "formal_metrics":m,
             "raw_cosine_auc":rank_auc(labels,raw_cos),
             "blockwise_cosine_auc":rank_auc(labels,block_scores),
             "structural_relation_auc":rank_auc(labels,relation_scores),
             "v2_compatibility_proxy_auc":rank_auc(labels,v2_proxy),"pairs":rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    report=["# Experiment 1 — SCE-128 v2","",f"- Formal accuracy: **{m['accuracy']:.4f}**",
            f"- Raw cosine AUC: **{payload['raw_cosine_auc']:.4f}**",
            f"- Blockwise cosine AUC: **{payload['blockwise_cosine_auc']:.4f}**",
            f"- Structural relation AUC: **{payload['structural_relation_auc']:.4f}**",
            f"- v2 compatibility proxy AUC: **{payload['v2_compatibility_proxy_auc']:.4f}**","",
            "| From | To | Expected | Raw cosine | Blockwise cosine | Structural relation | |",
            "|---|---|:---:|---:|---:|---:|---|"]
    for r in rows:
        report.append(f"| {r['from']} | {r['to']} | {r['expected']} | {r['raw_cosine']:.4f} | {r['blockwise_cosine']:.4f} | {r['structural_relation_score']:.4f} | |")
    REPORT.write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('=== PHASE 02 — CAPABILITY COMPATIBILITY ===')
    print(f"Formal accuracy={m['accuracy']:.4f} Precision={m['precision']:.4f} Recall={m['recall']:.4f} F1={m['f1']:.4f}")
    print(f"Raw cosine AUC={payload['raw_cosine_auc']:.4f}")
    print(f"Blockwise cosine AUC={payload['blockwise_cosine_auc']:.4f}")
    print(f"Structural relation AUC={payload['structural_relation_auc']:.4f}")
    print(f"v2 compatibility proxy AUC={payload['v2_compatibility_proxy_auc']:.4f}")
    print(f"JSON: {OUT}")
    print(f"Report: {REPORT}")
if __name__ == '__main__': main()
