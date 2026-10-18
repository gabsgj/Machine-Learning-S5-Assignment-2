"""Five experiments; finite enumeration appears ONLY in evaluation oracle."""
import csv,itertools,json,time,platform
from pathlib import Path
import numpy as np
from embedding import FactoredEmbedding,similarity
ROOT=Path(__file__).parent

def oracle_holds(state,conditions):
    for p in conditions:
        a=state[p['var']];b=p['value'];op=p['op']
        if op=='eq':ok=a==b
        elif op=='ne':ok=a!=b
        elif op=='gt':ok=a>b
        elif op=='ge':ok=a>=b
        elif op=='lt':ok=a<b
        elif op=='le':ok=a<=b
        elif op=='in':ok=a in b
        else:raise ValueError(op)
        if not ok:return False
    return True

def oracle(c,state,problem):
    if not oracle_holds(state,c['preconditions']+c['constraints']+problem['global_constraints']):return None
    out=state.copy();out.update(c['effects'])
    return out if oracle_holds(out,problem['global_constraints']) else None

def states(problem):
    names=sorted(problem['variables'])
    return [dict(zip(names,values)) for values in itertools.product(*(problem['variables'][k] for k in names))]

def run_sequence(caps,state,p):
    current=state
    for c in caps:
        if current is None:break
        current=oracle(c,current,p)
    return current

def main():
    problems=json.loads((ROOT/'dataset.json').read_text())['problems'];results=[]
    for p in problems:
        m=FactoredEmbedding(p);caps=p['capabilities'];byname={c['name']:c for c in caps};vectors=[m.encode(c) for c in caps];universe=states(p);pairs=[];correct=baseline_correct=coverage_errors=app_errors=0
        for a,e in zip(caps,vectors):
            for s in universe:
                try:out=m.apply(e,s)
                except ValueError:out=None
                app_errors+=out!=oracle(a,s,p)
        for i,a in enumerate(caps):
            for j,b in enumerate(caps):
                valid=[]
                for s in universe:
                    out=oracle(a,s,p)
                    if out is not None:valid.append(oracle(b,out,p) is not None)
                io=all(any(o['name']==z['name'] and o['type']==z['type'] and set(o['domain'])<=set(z['domain']) for o in a['outputs']) for z in b['inputs'] if z.get('required',True))
                truth=bool(valid and all(valid) and io)
                prediction=m.compatibility(vectors[i],vectors[j]);coverage=sum(valid)/len(valid) if valid else 0.
                coverage_errors+=abs(coverage-prediction['state_coverage'])>1e-12
                sim=similarity(vectors[i],vectors[j]);correct+=truth==prediction['guaranteed'];baseline_correct+=truth==(sim>=.8)
                pairs.append([a['name'],b['name'],truth,prediction['guaranteed'],coverage,sim])
        compositions=[]
        for names in p['compositions']:
            chaincaps=[byname[n] for n in names];chain=m.compose(chaincaps);errors=0
            for s in universe:
                expected=run_sequence(chaincaps,s,p)
                try:out=m.apply(chain,s)
                except ValueError:out=None
                errors+=out!=expected
            left=m.compose([m.compose(chaincaps[:-1]),chaincaps[-1]])
            right=m.compose([chaincaps[0],m.compose(chaincaps[1:])])
            leave=[]
            for index in range(len(chaincaps)):
                try:reduced=m.compose([c for j,c in enumerate(chaincaps) if j!=index]);leave.append(m.goal_satisfied(reduced,p['initial_state'],p['goal']))
                except ValueError:leave.append(False)
            compositions.append(dict(names=names,checks=len(universe),errors=errors,guards={k:sorted(v,key=repr) for k,v in chain.guards.items()},effects=chain.effects,associative=np.allclose(left.values,right.values),goal_satisfied=m.goal_satisfied(chain,p['initial_state'],p['goal']),goal_relevance=m.goal_relevance(chain,p['goal']),leave_one_out=leave,raw_sum_l2_error=float(np.linalg.norm(chain.values-sum(m.encode(c).values for c in chaincaps))),quality=chain.metadata['quality'],reliability=chain.metadata['reliability'],inputs=chain.metadata['inputs'],outputs=chain.metadata['outputs']))
        first=caps[0];alternatives=[c for c in caps if c['name'].startswith(first['name']+'_')];altvectors=[m.encode(c) for c in alternatives]
        irrelevant=next(c for c in caps if c['name'] in ['ChangeTheme','RotateAudit','WarmCache'])
        ranks={}
        for alpha in [0,1,10]:
            ranks[str(alpha)]=sorted([dict(name=c['name'],score=c['reliability']-alpha*c['quality']['money']) for c in [first,*alternatives]],key=lambda x:x['score'],reverse=True)
        gates={}
        inputs={z['name']:z['domain'][0] for z in first['inputs']}
        for label,resources,api_available in [('normal',p['available_resources'],True),('no_database',[r for r in p['available_resources'] if r!='Database'],True),('api_unavailable',p['available_resources'],False)]:
            eligible=[]
            for c in [first,*alternatives]:
                c=json.loads(json.dumps(c))
                if c['name']==first['name']:c['available']=api_available
                try:m.execute(c,p['initial_state'],resources,inputs);eligible.append(c['name'])
                except ValueError:pass
            gates[label]=eligible
        start=time.perf_counter()
        for _ in range(500):m.encode(first)
        encode_ms=(time.perf_counter()-start)*2
        es=[m.encode(byname[n]) for n in p['compositions'][-1]]
        start=time.perf_counter()
        for _ in range(500):m.compose(es)
        compose_ms=(time.perf_counter()-start)*2
        result=dict(domain=p['name'],state_count=len(universe),variables=len(m.names),D=m.D,port_values=sum(len(v) for v in m.port_domains.values()),port_slots=len(m.port_slots),mechanisms=len(m.mechanisms),resources=len(m.resources),capabilities=len(caps),dimension=len(vectors[0].values),bytes_float64=vectors[0].values.nbytes,unique_vectors=len(np.unique(np.stack([e.values for e in vectors]),axis=0)),
          experiment1=dict(pairs=len(pairs),exact_correct=correct,baseline_correct=baseline_correct,coverage_errors=int(coverage_errors),first_to_second=m.compatibility(caps[0],caps[1]),first_to_cancel=m.compatibility(caps[0],next(c for c in caps if c['name'] in ['CancelCart','ReleaseStock','ResetBuild'])),wrong_input=m.compatibility(caps[0],next(c for c in caps if c['name'] in ['WrongTypedPayment','BadLabel','BadTest']))),
          experiment2=compositions,experiment3=dict(semantic_similarity=[similarity(vectors[0],e) for e in altvectors],full_distances=[float(np.linalg.norm(vectors[0].values-e.values)) for e in altvectors]),experiment4=dict(irrelevant_name=irrelevant['name'],direct_goal_relevance=m.goal_relevance(irrelevant,p['goal']),first_direct_goal_relevance=m.goal_relevance(first,p['goal']),full_chain_with_irrelevant_goal=m.goal_satisfied(m.compose([*es,m.encode(irrelevant)]),p['initial_state'],p['goal'])),experiment5=dict(ranks=ranks,gates=gates),atomic_state_checks=len(caps)*len(universe),atomic_errors=int(app_errors),timings=dict(encode_ms=encode_ms,compose_ms=compose_ms))
        results.append(result)
        with (ROOT/'results'/f'{p["name"]}_pairs.csv').open('w') as f:
            w=csv.writer(f);w.writerow(['first','second','oracle_guaranteed','factored_guaranteed','state_coverage','semantic_similarity']);w.writerows(pairs)
        np.savez_compressed(ROOT/'results'/f'{p["name"]}_vectors.npz',atomic=np.stack([e.values for e in vectors]),state=m.encode(p['initial_state'],'state').values,goal=m.encode(p['goal'],'goal').values,composite=m.compose(es).values)
    scaling=[]
    template=problems[0]['capabilities'][0]
    for n in [10,20,40,80,160]:
        first=json.loads(json.dumps(template));first.update(preconditions=[],constraints=[],effects={'x0':True},inputs=[],outputs=[],resources=[])
        second=json.loads(json.dumps(first));second.update(preconditions=[dict(var='x0',op='eq',value=True)],effects={'x1':True},name='Step2')
        problem=dict(variables={f'x{i}':[False,True] for i in range(n)},global_constraints=[],capabilities=[first,second])
        m=FactoredEmbedding(problem);a=m.encode(first);b=m.encode(second)
        start=time.perf_counter()
        for _ in range(200):m.compose([a,b])
        elapsed=(time.perf_counter()-start)*5
        scaling.append(dict(boolean_variables=n,states_if_enumerated=2**n,dimension=len(a.values),bytes_float64=a.values.nbytes,dense_transition_bytes=8*(2**n)**2,compose_ms=elapsed))
    report=dict(environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),results=results,scaling=scaling)
    (ROOT/'results'/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
