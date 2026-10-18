"""Exact finite-state capability embedding. Python 3.10+, NumPy."""
import itertools, json, math
from dataclasses import dataclass
import numpy as np

def holds(state, conditions):
    for p in conditions:
        x, op, v = p
        a = state[x]
        if not {'eq': lambda: a == v, 'ne': lambda: a != v,
                'gt': lambda: a > v, 'le': lambda: a <= v,
                'in': lambda: a in v}[op]():
            return False
    return True

def signature(port):
    return (port['name'], port['type'], json.dumps(port['domain'],sort_keys=True), port.get('required',True))

def matches(output, inp):
    return (output['name']==inp['name'] and output['type']==inp['type']
            and set(output['domain']) <= set(inp['domain']))

@dataclass
class Encoded:
    kind: str
    vector: np.ndarray
    schema: str
    transition: object = None
    metadata: object = None

class Embedding:
    def __init__(self, problem):
        self.problem=problem
        self.keys=sorted(problem['variables'])
        self.states=[dict(zip(self.keys,v)) for v in itertools.product(
            *(problem['variables'][k] for k in self.keys))]
        self.index={tuple(s[k] for k in self.keys): i for i,s in enumerate(self.states)}
        caps=problem['capabilities']
        self.ports=sorted(set(signature(p) for c in caps for p in c['inputs']+c['outputs']))
        self.mechanisms=sorted(set(json.dumps([c['type'],c['mechanism']],sort_keys=True) for c in caps))
        self.resources=sorted(set(r for c in caps for r in c['resources']))
        self.schema=json.dumps([problem['variables'],self.ports,self.mechanisms,self.resources],sort_keys=True)
        self.n=len(self.states)
    def state_index(self,s):
        return self.index[tuple(s[k] for k in self.keys)]
    def transition(self,c):
        t=np.zeros((self.n,self.n))
        for i,s in enumerate(self.states):
            if holds(s,c['preconditions']+c['constraints']+self.problem['global_constraints']):
                out={**s,**c['effects']}
                if holds(out,self.problem['global_constraints']):
                    t[i,self.state_index(out)]=1
        return t
    def encode(self,entity,kind='capability'):
        if isinstance(entity,Encoded):
            if entity.schema!=self.schema:raise ValueError('Schema mismatch')
            return entity
        if kind=='state':
            v=np.zeros(self.n);v[self.state_index(entity)]=1
            return Encoded(kind,v,self.schema)
        if kind=='goal':
            return Encoded(kind,np.array([holds(s,entity) for s in self.states],float),self.schema)
        c=entity;t=self.transition(c)
        return self.pack(t,c)
    def pack(self,t,c):
        ports=[float(any(signature(p)==q for p in c[role])) for role in ['inputs','outputs'] for q in self.ports]
        # Composite keeps mechanism counts, enabling distinction from atomic implementations.
        ms=c.get('mechanism_counts',{json.dumps([c['type'],c['mechanism']],sort_keys=True):1})
        mech=[ms.get(m,0) for m in self.mechanisms]
        res=[float(r in c['resources']) for r in self.resources]
        q=c['quality']
        ops=[q[k] for k in ['time_ms','resource_cost','money','risk','energy']]+[c['reliability'],float(c['available'])]
        return Encoded('capability',np.concatenate([t.ravel(),ports,mech,res,ops]),self.schema,t,c)
    def compose(self,capabilities):
        if not capabilities: raise ValueError('Empty sequence')
        encoded=[c if isinstance(c,Encoded) else self.encode(c) for c in capabilities]
        if any(c.schema!=self.schema or c.kind!='capability' for c in encoded): raise ValueError('Schema/kind mismatch')
        t=np.eye(self.n);external=[];outputs=[];resources=set();ms={}
        q=dict.fromkeys(['time_ms','resource_cost','money','energy'],0.0); survival=1.; rel=1.;avail=True
        for e in encoded:
            c=e.metadata
            for inp in c['inputs']:
                if not inp.get('required',True):continue
                if any(matches(o,inp) for o in outputs):continue
                if any(o['name']==inp['name'] for o in outputs):
                    raise ValueError('Incompatible internal port: '+inp['name'])
                if not any(matches(x,inp) for x in external):external.append(inp)
            outputs=[o for o in outputs if o['name'] not in {p['name'] for p in c['outputs']}]+c['outputs']
            t=t@e.transition
            resources.update(c['resources'])
            counts=c.get('mechanism_counts',{json.dumps([c['type'],c['mechanism']],sort_keys=True):1})
            for m,v in counts.items():ms[m]=ms.get(m,0)+v
            for k in q:q[k]+=c['quality'][k]
            survival*=1-c['quality']['risk'];rel*=c['reliability'];avail &= c['available']
        q['risk']=1-survival
        if not t.any(): raise ValueError('Sequence has no valid initial state')
        c={'name':' -> '.join(e.metadata['name'] for e in encoded),'type':'COMPOSITE','mechanism':{},
           'mechanism_counts':ms,'inputs':external,'outputs':outputs,'resources':sorted(resources),
           'quality':q,'reliability':rel,'available':avail}
        return self.pack(t,c)
    def compatibility(self,a,b):
        a=a if isinstance(a,Encoded) else self.encode(a);b=b if isinstance(b,Encoded) else self.encode(b)
        if a.schema!=self.schema or b.schema!=self.schema:raise ValueError('Schema mismatch')
        active=a.transition.sum(1);passed=(a.transition@b.transition).sum(1)
        required=[p for p in b.metadata['inputs'] if p.get('required',True)]
        io=all(any(matches(o,p) for o in a.metadata['outputs']) for p in required)
        coverage=float(passed.sum()/active.sum()) if active.sum() else 0.
        return {'state_coverage':coverage,'io_compatible':io,'existential':bool(passed.any() and io),
                'guaranteed':bool(active.any() and coverage==1 and io)}
    def execute(self,c,state,resources,inputs):
        e=c if isinstance(c,Encoded) else self.encode(c)
        if not e.metadata['available']:raise ValueError('Unavailable')
        if not set(e.metadata['resources'])<=set(resources):raise ValueError('Missing resource')
        for p in e.metadata['inputs']:
            if p.get('required',True) and (p['name'] not in inputs or inputs[p['name']] not in p['domain']):
                raise ValueError('Missing/invalid input')
        row=e.transition[self.state_index(state)]
        if not row.any():raise ValueError('Precondition/constraint violation')
        return self.states[int(row.argmax())].copy()
    def goal_score(self,c,state,goal):
        e=c if isinstance(c,Encoded) else self.encode(c)
        return float(self.encode(state,'state').vector@e.transition@self.encode(goal,'goal').vector)

def similarity(x,y,semantic=True):
    if x.schema!=y.schema or x.kind!=y.kind:raise ValueError('Incomparable encodings')
    a=x.transition.ravel() if semantic and x.kind=='capability' else x.vector
    b=y.transition.ravel() if semantic and y.kind=='capability' else y.vector
    d=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.clip(a@b/d,-1,1)) if d else 0.
