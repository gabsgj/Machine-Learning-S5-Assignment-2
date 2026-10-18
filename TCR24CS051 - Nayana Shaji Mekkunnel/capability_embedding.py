#!/usr/bin/env python3
"""Dependency-free formal capability embedding demo for Assignment 2."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Any


def conditions(items):
    return {x['variable']: x.get('expectedValue', x.get('value')) for x in items}

def effects(items):
    return {x['variable']: x['value'] for x in items}

def ports(items):
    return {x['name']: x for x in items}


class CapabilityEmbedding:
    """Interpretable vector encodings; symbolic compatibility is checked exactly."""
    def __init__(self, problem: dict[str, Any]):
        self.problem = problem
        self.state = problem['initialState']
        self.goal = conditions(problem['goal'])
        self.capabilities = problem['capabilities']
        self.vars = sorted(set(self.state) | set(self.goal) |
            {p['variable'] for c in self.capabilities for p in c.get('preconditions', [])} |
            {e['variable'] for c in self.capabilities for e in c.get('effects', [])})
        self.types = sorted({c.get('type', 'UNKNOWN') for c in self.capabilities} | {'COMPOSITE'})

    def encode_state(self, state):
        return [1.0 if state.get(k) is True else -1.0 if state.get(k) is False else 0.0 for k in self.vars]

    def encode_goal(self, goal):
        g = conditions(goal) if isinstance(goal, list) else goal
        return [1.0 if g.get(k) is True else -1.0 if k in g else 0.0 for k in self.vars]

    def encode_capability(self, c):
        pre, eff = conditions(c.get('preconditions', [])), effects(c.get('effects', []))
        v = [1.0 if pre.get(k) is True else -1.0 if k in pre else 0.0 for k in self.vars]
        v += [1.0 if eff.get(k) is True else -1.0 if k in eff else 0.0 for k in self.vars]
        v += [1.0 if c.get('type', 'UNKNOWN') == t else 0.0 for t in self.types]
        q = c.get('qos', {})
        v += [math.log1p(max(0.0, float(q.get('timeCostMs', 0)))) / 10,
              math.log1p(max(0.0, float(q.get('moneyCost', 0))) * 1000) / 10,
              math.log1p(max(0.0, float(q.get('resourceCost', 0)))) / 10,
              max(0.0, min(1.0, float(q.get('risk', 0)))),
              max(0.0, min(1.0, float(c.get('reliability', 1)))),
              1.0 if c.get('availability', True) else 0.0]
        return v

    @staticmethod
    def similarity(a, b):
        if len(a) != len(b): raise ValueError('Vectors must have equal dimensions')
        na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(y*y for y in b))
        return sum(x*y for x, y in zip(a, b)) / (na*nb) if na and nb else 0.0

    @staticmethod
    def port_compatibility(first, second):
        outs, ins = ports(first.get('outputs', [])), ports(second.get('inputs', []))
        missing = [n for n, p in ins.items() if p.get('required', True) and
                   (n not in outs or outs[n].get('type') != p.get('type'))]
        return not missing, missing

    @staticmethod
    def compatibility(first, second):
        eff, pre = effects(first.get('effects', [])), conditions(second.get('preconditions', []))
        sat = [k for k, v in pre.items() if eff.get(k, object()) == v]
        bad = [k for k, v in pre.items() if k in eff and eff[k] != v]
        unresolved = [k for k in pre if k not in eff]
        ports_ok, missing = CapabilityEmbedding.port_compatibility(first, second)
        return {'compatible': not bad and ports_ok, 'fully_enabled': not bad and not unresolved and ports_ok,
                'satisfied': sat, 'contradicted': bad, 'unresolved': unresolved, 'missing_ports': missing}

    @staticmethod
    def compose(sequence):
        if not sequence: raise ValueError('Provide at least one capability')
        pre, eff = {}, {}
        for c in sequence:
            cp, ce = conditions(c.get('preconditions', [])), effects(c.get('effects', []))
            for k, val in cp.items():
                if k in eff and eff[k] != val:
                    raise ValueError(f"Incompatible sequence: {c['id']} requires {k}={val}; earlier step sets {eff[k]}")
                if k not in eff and k in pre and pre[k] != val: raise ValueError(f'Conflicting initial requirement for {k}')
                if k not in eff: pre[k] = val
            eff.update(ce)
        qos_keys = ('timeCostMs', 'moneyCost', 'resourceCost', 'risk')
        qos = {k: sum(float(c.get('qos', {}).get(k, 0)) for c in sequence) for k in qos_keys}
        rel = math.prod(float(c.get('reliability', 1)) for c in sequence)
        inputs, outputs = {}, {}
        for c in sequence:
            for n, p in ports(c.get('inputs', [])).items(): inputs.setdefault(n, p)
            outputs.update(ports(c.get('outputs', [])))
        inputs = {n:p for n,p in inputs.items() if n not in outputs}
        return {'id':'Composite['+' -> '.join(c['id'] for c in sequence)+']','name':'Composite capability',
                'type':'COMPOSITE','mechanism':'sequential',
                'preconditions':[{'variable':k,'op':'==','expectedValue':v} for k,v in pre.items()],
                'effects':[{'variable':k,'op':'SET','value':v} for k,v in eff.items()],
                'inputs':list(inputs.values()),'outputs':list(outputs.values()),'qos':qos,
                'reliability':rel,'availability':all(c.get('availability',True) for c in sequence),
                'steps':[c['id'] for c in sequence]}

    def goal_relevance(self, c):
        eff = effects(c.get('effects', []))
        return sum(eff.get(k, object()) == v for k,v in self.goal.items()) / len(self.goal) if self.goal else 0.0


def run_experiments(m):
    c = {x['id']:x for x in m.capabilities}
    print('EXPERIMENT 1 - DIRECTIONAL COMPATIBILITY')
    # Assignment's controlled example: one successor is enabled, one contradicted.
    first={'id':'CreateOrder','effects':[{'variable':'Order.exists','op':'SET','value':True}]}
    pay={'id':'MakePayment','preconditions':[{'variable':'Order.exists','op':'==','expectedValue':True}]}
    cancel={'id':'CancelCart','preconditions':[{'variable':'Order.exists','op':'==','expectedValue':False}]}
    print('  CreateOrder -> MakePayment:',m.compatibility(first,pay))
    print('  CreateOrder -> CancelCart:',m.compatibility(first,cancel))
    print('\nEXPERIMENT 2 - COMPOSITION')
    comp=m.compose([c[x] for x in ('CreateOrder','ValidateInventory','MakePayment_API')])
    print(f"  {comp['id']}; reliability={comp['reliability']:.4f}; QoS={comp['qos']}; vector dimension={len(m.encode_capability(comp))}")
    print('\nEXPERIMENT 3 - ALTERNATIVE IMPLEMENTATIONS')
    a,b=c['MakePayment_API'],c['MakePayment_DB']
    print(f"  same effects={effects(a['effects'])==effects(b['effects'])}; full cosine={m.similarity(m.encode_capability(a),m.encode_capability(b)):.4f}; types={a['type']} / {b['type']}")
    print('\nEXPERIMENT 4 - GOAL RELEVANCE')
    for n in ('GenerateInvoice','BrowseCatalog','UpdateWishlist'): print(f'  {n}: {m.goal_relevance(c[n]):.2f}')
    print('\nEXPERIMENT 5 - OPERATIONAL ATTRIBUTES')
    for n in ('MakePayment_API','MakePayment_DB'):
        x=c[n]; print(f"  {n}: cost={x['qos']['moneyCost']}, latency={x['qos']['timeCostMs']}ms, reliability={x['reliability']}, available={x.get('availability',True)}")


def main():
    p=argparse.ArgumentParser(description='Formal capability embedding and composition demo')
    p.add_argument('problem',nargs='?',default='ecommerce_purchase_flow.json',help='formal application JSON file')
    p.add_argument('--vectors',action='store_true',help='print encoded state, goal, and capability vectors')
    p.add_argument('--experiments',action='store_true',help='run all five assignment experiments')
    p.add_argument('--compose',action='store_true',help='print a composite purchase capability')
    a=p.parse_args(); path=Path(a.problem)
    if not path.exists(): p.error(f'Cannot find {path}; run from the project folder or pass a JSON path')
    m=CapabilityEmbedding(json.loads(path.read_text(encoding='utf-8'))); caps={x['id']:x for x in m.capabilities}
    print(f"Problem: {m.problem.get('problemName',path.name)}")
    print(f"Dimensions: state/goal={len(m.vars)}, capability={len(m.encode_capability(next(iter(caps.values()))))}")
    if a.vectors:
        print('State vector:',m.encode_state(m.state)); print('Goal vector: ',m.encode_goal(m.goal))
        for x in m.capabilities: print(x['id']+':',m.encode_capability(x))
    if a.compose:
        seq=[caps[n] for n in ('CreateOrder','ValidateInventory','MakePayment_API','GenerateInvoice') if n in caps]
        print('Composite:',json.dumps(m.compose(seq),indent=2))
    if a.experiments: run_experiments(m)
    if not (a.vectors or a.experiments or a.compose): run_experiments(m)

if __name__ == '__main__': main()
