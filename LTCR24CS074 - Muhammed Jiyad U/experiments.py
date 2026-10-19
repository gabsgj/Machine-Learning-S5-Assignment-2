"""Run all five assignment experiments and exhaustive semantic checks."""
import json,time,platform,csv
from pathlib import Path
import numpy as np
from embedding import Embedding,similarity,holds,matches
ROOT=Path(__file__).parent

def oracle(c,s,p):
    # Independent interpreter, with no vector operations.
    if not holds(s,c['preconditions']+c['constraints']+p['global_constraints']):return None
    out=s.copy();out.update(c['effects'])
    return out if holds(out,p['global_constraints']) else None

def main():
    problems=json.loads((ROOT/'dataset.json').read_text())['problems'];results=[]
    for p in problems:
        model=Embedding(p);caps=p['capabilities'];enc=[model.encode(c) for c in caps];s=p['initial_state'];goal=p['goal']
        rows=[];correct=0;baseline_correct=0;checks=0
        for i,a in enumerate(caps):
            for j,b in enumerate(caps):
                successes=[]
                for state in model.states:
                    x=oracle(a,state,p)
                    if x is not None:successes.append(oracle(b,x,p) is not None)
                io=all(any(matches(o,z) for o in a['outputs']) for z in b['inputs'] if z.get('required',True))
                truth=bool(successes and all(successes) and io)
                predicted=model.compatibility(enc[i],enc[j])['guaranteed']
                baseline=similarity(enc[i],enc[j])>=.5
                correct+=truth==predicted;baseline_correct+=truth==baseline
                rows.append([p['name'],a['name'],b['name'],truth,predicted,similarity(enc[i],enc[j])])
        chain=model.compose(enc[:3]);left=model.compose([model.compose(enc[:2]),enc[2]]);right=model.compose([enc[0],model.compose(enc[1:3])])
        errors=0
        for state in model.states:
            current=state
            for c in caps[:3]:
                if current is None:break
                current=oracle(c,current,p)
            row=chain.transition[model.state_index(state)]
            errors+= (current is None and row.any()) or (current is not None and (not row.any() or model.states[int(row.argmax())]!=current))
            checks+=1
        app_errors=0
        for c,e in zip(caps,enc):
            for state in model.states:
                app_errors+=bool(e.transition[model.state_index(state)].any()) != (oracle(c,state,p) is not None)
        reduced=[]
        for i in range(3):
            seq=[enc[j] for j in range(3) if j!=i]
            try:score=model.goal_score(model.compose(seq),s,goal)
            except ValueError:score=0
            reduced.append(score)
        # Operations: documented illustrative preference, not learned ranking.
        ranked=[]
        for e in [enc[0],enc[4],enc[5]]:
            c=e.metadata;utility=c['reliability']-c['quality']['money']
            ranked.append({'name':c['name'],'utility':utility,'money':c['quality']['money'],'reliability':c['reliability']})
        ranking=sorted(ranked,key=lambda r:r['utility'],reverse=True)
        gates={}
        for label,resources,available in [('all',p['available_resources'],True),('no_database',[r for r in p['available_resources'] if r!='Database'],True),('api_unavailable',p['available_resources'],False)]:
            choices=[]
            for idx in [0,4,5]:
                c=json.loads(json.dumps(caps[idx]))
                if idx==0:c['available']=available
                try:model.execute(c,s,resources,{'request':'valid'});choices.append(c['name'])
                except ValueError:pass
            gates[label]=choices
        start=time.perf_counter()
        for _ in range(100):model.encode(caps[0])
        encoding_ms=(time.perf_counter()-start)*10
        start=time.perf_counter()
        for _ in range(30):model.compose(enc[:3])
        composition_ms=(time.perf_counter()-start)*1000/30
        result={'domain':p['name'],'states':model.n,'capabilities':len(caps),'dimension':len(enc[0].vector),'bytes_float64':enc[0].vector.nbytes,
          'experiment1':{'required_positive':model.compatibility(enc[0],enc[1]),'required_negative':model.compatibility(enc[0],enc[3]),'pair_count':len(rows),'exact_correct':correct,'cosine_baseline_correct':baseline_correct,'wrong_input':model.compatibility(enc[0],enc[7])},
          'experiment2':{'states_checked':checks,'semantic_errors':int(errors),'associative_full_vector':bool(np.allclose(left.vector,right.vector)),'sum_error_l2':float(np.linalg.norm(chain.transition-sum(e.transition for e in enc[:3]))),'goal_satisfied':model.goal_score(chain,s,goal),'constituent_cosines':[similarity(chain,e) for e in enc[:3]],'quality':chain.metadata['quality'],'reliability':chain.metadata['reliability'],'external_inputs':chain.metadata['inputs'],'outputs':chain.metadata['outputs']},
          'experiment3':{'functional_cosines':[similarity(enc[0],enc[i]) for i in [4,5]],'full_vector_distances':[float(np.linalg.norm(enc[0].vector-enc[i].vector)) for i in [4,5]]},
          'experiment4':{'direct_irrelevant_goal_score':model.goal_score(enc[6],s,goal),'chain_goal_score':model.goal_score(chain,s,goal),'leave_one_out_scores':reduced,'with_irrelevant_goal_score':model.goal_score(model.compose([*enc[:3],enc[6]]),s,goal)},
          'experiment5':{'ranking':ranking,'gates':gates},'applicability_errors':int(app_errors),'timing':{'encode_ms_mean_100':encoding_ms,'compose_ms_mean_30':composition_ms}}
        results.append(result)
        with (ROOT/'results'/f'{p["name"]}_pairs.csv').open('w') as f:
            w=csv.writer(f);w.writerow(['domain','first','second','oracle_guaranteed','embedding_guaranteed','semantic_cosine']);w.writerows(rows)
        np.savez_compressed(ROOT/'results'/f'{p["name"]}_vectors.npz',states=np.eye(model.n),goal=model.encode(goal,'goal').vector,atomic=np.stack([e.vector for e in enc]),composite=chain.vector)
    output={'environment':{'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform()},'results':results}
    (ROOT/'results'/'results.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
if __name__=='__main__':main()
