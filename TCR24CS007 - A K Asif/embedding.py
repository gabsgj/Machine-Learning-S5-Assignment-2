"""Factored Guard-Effect Embedding (FGEE), exact for unary finite guards.
No Cartesian state enumeration occurs in this module.
"""
from dataclasses import dataclass
import json
import numpy as np

OPS={'eq':lambda a,b:a==b,'ne':lambda a,b:a!=b,'gt':lambda a,b:a>b,
     'ge':lambda a,b:a>=b,'lt':lambda a,b:a<b,'le':lambda a,b:a<=b,
     'in':lambda a,b:a in b}

def holds(state,predicates):
    return all(OPS[p['op']](state[p['var']],p['value']) for p in predicates)

def port_match(out,inp):
    return out['name']==inp['name'] and out['type']==inp['type'] and set(out['domain'])<=set(inp['domain'])

def merge_input(ports,p):
    """Repeated external names must satisfy every requirement."""
    for old in ports:
        if old['name']==p['name']:
            if old['type']!=p['type']:raise ValueError('Conflicting external input type')
            overlap=[v for v in old['domain'] if v in p['domain']]
            if not overlap:raise ValueError('Empty external input domain')
            old['domain']=overlap;old['required']=old.get('required',True) or p.get('required',True)
            return
    ports.append(dict(p,domain=list(p['domain'])))

@dataclass
class Vector:
    kind:str
    values:np.ndarray
    schema:str
    guards:object=None
    effects:object=None
    metadata:object=None

class FactoredEmbedding:
    def __init__(self,problem):
        self.problem=problem;self.names=sorted(problem['variables'])
        self.domains={k:list(problem['variables'][k]) for k in self.names}
        if any(not v or len(set(v))!=len(v) for v in self.domains.values()):raise ValueError('Invalid finite domain')
        self.D=sum(map(len,self.domains.values()))
        self.port_slots=sorted({(p['name'],p['type']) for c in problem['capabilities'] for p in c['inputs']+c['outputs']})
        self.port_domains={k:sorted({v for c in problem['capabilities'] for p in c['inputs']+c['outputs'] if (p['name'],p['type'])==k for v in p['domain']},key=repr) for k in self.port_slots}
        self.mechanisms=sorted({json.dumps([c['type'],c['mechanism']],sort_keys=True) for c in problem['capabilities']})
        self.resources=sorted({r for c in problem['capabilities'] for r in c['resources']})
        self.schema=json.dumps([self.domains,[(k,self.port_domains[k]) for k in self.port_slots],self.mechanisms,self.resources],sort_keys=True)
        self.global_guards=self.guard_sets(problem['global_constraints'])
    def guard_sets(self,predicates):
        sets={k:set(v) for k,v in self.domains.items()}
        for p in predicates:
            name=p['var']
            sets[name]&={v for v in self.domains[name] if OPS[p['op']](v,p['value'])}
        return sets
    def masks(self,sets):
        return [float(v in sets[k]) for k in self.names for v in self.domains[k]]
    def encode(self,entity,kind='capability'):
        if isinstance(entity,Vector):
            if entity.schema!=self.schema:raise ValueError('Schema mismatch')
            return entity
        if kind=='state':
            if set(entity)!=set(self.names) or any(entity[k] not in self.domains[k] for k in self.names):raise ValueError('Invalid state')
            return Vector(kind,np.array([float(v==entity[k]) for k in self.names for v in self.domains[k]]),self.schema)
        if kind=='goal':
            return Vector(kind,np.array(self.masks(self.guard_sets(entity))),self.schema)
        if kind!='capability':raise ValueError('Unknown entity kind')
        c=entity;guards=self.guard_sets(c['preconditions']+c['constraints']+self.problem['global_constraints']);effects=dict(c['effects'])
        for k,v in effects.items():
            if v not in self.domains[k]:raise ValueError('Effect outside domain')
            if v not in self.global_guards[k]:guards[k]=set()
        return self.pack(guards,effects,c)
    def pack(self,g,e,c):
        effect_mask=[float(k in e and e[k]==v) for k in self.names for v in self.domains[k]]
        writes=[float(k in e) for k in self.names]
        ports=[]
        for role in ['inputs','outputs']:
            for slot in self.port_slots:
                ps=[p for p in c[role] if (p['name'],p['type'])==slot]
                if len(ps)>1:raise ValueError('Duplicate port slot')
                for v in self.port_domains[slot]:ports.append(float(bool(ps) and v in ps[0]['domain']))
        for role in ['inputs','outputs']:
            for p in c[role]:
                slot=(p['name'],p['type'])
                if slot not in self.port_slots or not p['domain'] or not set(p['domain'])<=set(self.port_domains[slot]):raise ValueError('Port outside schema')
        required=[float(any((p['name'],p['type'])==slot and p.get('required',True) for p in c['inputs'])) for slot in self.port_slots]
        counts=c.get('mechanism_counts',{json.dumps([c['type'],c['mechanism']],sort_keys=True):1})
        if not set(counts)<=set(self.mechanisms):raise ValueError('Mechanism outside schema')
        if not set(c['resources'])<=set(self.resources):raise ValueError('Resource outside schema')
        q=c['quality']
        values=self.masks(g)+writes+effect_mask+ports+required+[counts.get(m,0) for m in self.mechanisms]+[float(r in c['resources']) for r in self.resources]+[q[k] for k in ['time_ms','money','energy','risk','resource_cost']]+[c['reliability'],float(c['available'])]
        return Vector('capability',np.array(values,float),self.schema,{k:set(v) for k,v in g.items()},dict(e),c)
    @property
    def dimension(self):
        V=sum(len(v) for v in self.port_domains.values())
        return 2*self.D+len(self.names)+2*V+len(self.port_slots)+len(self.mechanisms)+len(self.resources)+7
    def from_vector(self,values):
        """Decode capability blocks without the original capability specification."""
        a=np.asarray(values,float)
        if a.shape!=(self.dimension,) or not np.isfinite(a).all():raise ValueError('Invalid vector shape/value')
        offset=0
        def take(n):
            nonlocal offset
            x=a[offset:offset+n];offset+=n;return x
        g={}
        for k in self.names:
            bits=take(len(self.domains[k]))
            if not np.isin(bits,[0,1]).all():raise ValueError('Nonbinary guard')
            g[k]={v for v,b in zip(self.domains[k],bits) if b}
        writes=take(len(self.names));e={}
        if not np.isin(writes,[0,1]).all():raise ValueError('Nonbinary write mask')
        for k,w in zip(self.names,writes):
            bits=take(len(self.domains[k]))
            if not np.isin(bits,[0,1]).all() or bits.sum()!=w:raise ValueError('Invalid effect block')
            if w:e[k]=self.domains[k][int(bits.argmax())]
        roles=[]
        for _ in range(2):
            ports=[]
            for slot in self.port_slots:
                bits=take(len(self.port_domains[slot]))
                if not np.isin(bits,[0,1]).all():raise ValueError('Nonbinary port mask')
                allowed=[v for v,b in zip(self.port_domains[slot],bits) if b]
                if allowed:ports.append(dict(name=slot[0],type=slot[1],domain=allowed))
            roles.append(ports)
        required=take(len(self.port_slots))
        if not np.isin(required,[0,1]).all():raise ValueError('Nonbinary requirement')
        for slot,b in zip(self.port_slots,required):
            selected=[p for p in roles[0] if (p['name'],p['type'])==slot]
            if b and not selected:raise ValueError('Required input absent')
            if selected:selected[0]['required']=bool(b)
        mc=take(len(self.mechanisms))
        if (mc<0).any() or not np.equal(mc,np.floor(mc)).all():raise ValueError('Invalid mechanism counts')
        counts={m:int(v) for m,v in zip(self.mechanisms,mc) if v}
        rb=take(len(self.resources))
        if not np.isin(rb,[0,1]).all():raise ValueError('Nonbinary resource mask')
        qv=take(7);q=dict(zip(['time_ms','money','energy','risk','resource_cost'],qv[:5]))
        if not 0<=qv[3]<=1 or not 0<=qv[5]<=1 or qv[6] not in [0,1]:raise ValueError('Invalid operational block')
        c=dict(name='DecodedCapability',type='DECODED',mechanism={},mechanism_counts=counts,
               inputs=roles[0],outputs=roles[1],resources=[r for r,b in zip(self.resources,rb) if b],
               quality=q,reliability=float(qv[5]),available=bool(qv[6]))
        return self.pack(g,e,c)
    def valid(self,e):return all(e.guards[k] for k in self.names)
    def apply(self,c,state):
        e=self.encode(c);self.encode(state,'state')
        if not all(state[k] in e.guards[k] for k in self.names):raise ValueError('Guard violation')
        return {**state,**e.effects}
    def execute(self,c,state,resources,inputs):
        e=self.encode(c)
        if not e.metadata['available']:raise ValueError('Unavailable')
        if not set(e.metadata['resources'])<=set(resources):raise ValueError('Missing resource')
        for p in e.metadata['inputs']:
            if p['name'] not in inputs:
                if p.get('required',True):raise ValueError('Missing input')
            elif inputs[p['name']] not in p['domain']:raise ValueError('Invalid input value')
        return self.apply(e,state)
    def compose(self,capabilities):
        if not capabilities:raise ValueError('Empty sequence')
        caps=[self.encode(c) for c in capabilities]
        if any(c.kind!='capability' for c in caps):raise ValueError('Expected capabilities')
        guards={k:set(v) for k,v in self.domains.items()};effects={};inputs=[];outputs=[];resources=set();counts={}
        q={k:0. for k in ['time_ms','money','energy','resource_cost']};rel=1.;safe=1.;available=True
        for e in caps:
            for k in self.names:
                if k in effects:
                    if effects[k] not in e.guards[k]:raise ValueError('Assigned value contradicts later guard')
                else:
                    guards[k]&=e.guards[k]
                    if not guards[k]:raise ValueError('No valid initial state')
            effects.update(e.effects)
            c=e.metadata
            for inp in c['inputs']:
                preceding=[o for o in outputs if o['name']==inp['name']]
                if preceding:
                    if not any(port_match(o,inp) for o in preceding):raise ValueError('Internal port mismatch')
                else:merge_input(inputs,inp)
            outputs=[o for o in outputs if o['name'] not in {p['name'] for p in c['outputs']}]+[dict(p,domain=list(p['domain'])) for p in c['outputs']]
            resources.update(c['resources'])
            ms=c.get('mechanism_counts',{json.dumps([c['type'],c['mechanism']],sort_keys=True):1})
            for m,v in ms.items():counts[m]=counts.get(m,0)+v
            for k in q:q[k]+=c['quality'][k]
            rel*=c['reliability'];safe*=1-c['quality']['risk'];available &= c['available']
        q['risk']=1-safe
        meta=dict(name=' -> '.join(e.metadata['name'] for e in caps),type='COMPOSITE',mechanism={},mechanism_counts=counts,inputs=inputs,outputs=outputs,resources=sorted(resources),quality=q,reliability=rel,available=available)
        return self.pack(guards,effects,meta)
    def compatibility(self,a,b):
        a=self.encode(a);b=self.encode(b)
        if a.kind!='capability' or b.kind!='capability':raise ValueError('Expected capabilities')
        coverage=1. if self.valid(a) else 0.
        for k in self.names:
            if k in a.effects:coverage*=float(a.effects[k] in b.guards[k])
            elif a.guards[k]:coverage*=len(a.guards[k]&b.guards[k])/len(a.guards[k])
        io=all(any(port_match(o,p) for o in a.metadata['outputs']) for p in b.metadata['inputs'] if p.get('required',True))
        guaranteed=self.valid(a) and all(({a.effects[k]} if k in a.effects else a.guards[k])<=b.guards[k] for k in self.names)
        return dict(state_coverage=coverage,io_compatible=io,existential=bool(coverage>0 and io),guaranteed=bool(guaranteed and io))
    def goal_relevance(self,c,goal):
        """Fraction of nontrivial goal-variable restrictions established by writes."""
        e=self.encode(c);g=self.guard_sets(goal)
        targets=[k for k in self.names if g[k]!=set(self.domains[k])]
        if not targets:return 1.
        return sum(k in e.effects and e.effects[k] in g[k] for k in targets)/len(targets)
    def goal_satisfied(self,c,state,goal):
        try:out=self.apply(c,state)
        except ValueError:return False
        return holds(out,goal)

def similarity(a,b):
    """Semantic weighted Jaccard: guard restrictions plus assigned values."""
    if a.schema!=b.schema or a.kind!=b.kind:raise ValueError('Schema/kind mismatch')
    if a.kind!='capability':
        union=np.maximum(a.values,b.values).sum();return float(np.minimum(a.values,b.values).sum()/union) if union else 1.
    # Guard sets are compared by intersection/union per constrained variable.
    # Effects get weight 0.7; guard resemblance gets weight 0.3.
    union=set(a.effects)|set(b.effects)
    effect=sum(k in a.effects and k in b.effects and a.effects[k]==b.effects[k] for k in union)/len(union) if union else 1.
    ratios=[len(a.guards[k]&b.guards[k])/len(a.guards[k]|b.guards[k]) if a.guards[k]|b.guards[k] else 1. for k in a.guards]
    return .7*effect+.3*sum(ratios)/len(ratios)
