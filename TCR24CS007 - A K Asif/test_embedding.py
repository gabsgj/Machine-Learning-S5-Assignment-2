import itertools,json,random,unittest
from pathlib import Path
import numpy as np
from embedding import FactoredEmbedding,similarity
from experiments import oracle,states,run_sequence
class Tests(unittest.TestCase):
    def setUp(self):
        self.problems=json.loads(Path(__file__).with_name('dataset.json').read_text())['problems']
        self.p=self.problems[0];self.m=FactoredEmbedding(self.p);self.c=self.p['capabilities']
    def test_required_pattern_and_types(self):
        self.assertTrue(self.m.compatibility(self.c[0],self.c[1])['guaranteed'])
        self.assertFalse(self.m.compatibility(self.c[0],self.c[3])['existential'])
        self.assertFalse(self.m.compatibility(self.c[0],self.c[6])['io_compatible'])
        with self.assertRaises(ValueError):self.m.compose([self.c[0],self.c[6]])
    def test_overwrite_and_guard_regression(self):
        p=self.problems[2];m=FactoredEmbedding(p);e=m.compose(p['capabilities'][:3])
        self.assertEqual(e.effects['stage'],'DEPLOYED')
        self.assertEqual(e.guards['stage'],{'RAW'})
        self.assertEqual(e.guards['credentials'],{True})
        self.assertEqual(e.guards['environment'],{'PROD'})
        self.assertTrue(m.goal_satisfied(e,p['initial_state'],p['goal']))
        self.assertFalse(m.goal_satisfied(e,{**p['initial_state'],'credentials':False},p['goal']))
        with self.assertRaises(ValueError):m.compose(p['capabilities'][:3][::-1])
    def test_associativity(self):
        for p in self.problems:
            m=FactoredEmbedding(p);a,b,c=p['capabilities'][:3]
            l=m.compose([m.compose([a,b]),c]);r=m.compose([a,m.compose([b,c])])
            np.testing.assert_allclose(l.values,r.values)
            self.assertIs(m.encode(l),l)
    def test_operational_gates_and_numeric_constraint(self):
        c=self.c[9];s=self.p['initial_state']
        with self.assertRaises(ValueError):self.m.execute(c,{**s,'quantity':0},self.p['available_resources'],{'cart_id':'valid'})
        with self.assertRaises(ValueError):self.m.execute(self.c[0],s,[],{'cart_id':'valid'})
        with self.assertRaises(ValueError):self.m.execute(self.c[0],s,self.p['available_resources'],{})
        with self.assertRaises(ValueError):self.m.execute({**self.c[0],'available':False},s,self.p['available_resources'],{'cart_id':'valid'})
    def test_schema_identity_and_impossible(self):
        a=self.m.encode(self.c[0]);b=self.m.encode(self.c[4]);self.assertEqual(similarity(a,b),1)
        self.assertFalse(np.array_equal(a.values,b.values))
        other=self.problems[1];m=FactoredEmbedding(other)
        with self.assertRaises(ValueError):similarity(a,m.encode(other['capabilities'][0]))
        with self.assertRaises(ValueError):self.m.compose([])
        with self.assertRaises(ValueError):self.m.compose([self.c[0],self.c[3]])
    def test_seeded_generated_compositions(self):
        # Stronger than fixed-chain tests: 80 arbitrary three-step guard/write cases.
        rng=random.Random(503);p=self.problems[2];m=FactoredEmbedding(p);universe=states(p)
        for _ in range(80):
            caps=[]
            for j in range(3):
                c=json.loads(json.dumps(p['capabilities'][0]));c['inputs']=[];c['outputs']=[];c['constraints']=[]
                keys=rng.sample(m.names,2);c['preconditions']=[dict(var=k,op=rng.choice(['eq','ne']),value=rng.choice(m.domains[k])) for k in keys]
                c['effects']={k:rng.choice(m.domains[k]) for k in rng.sample(m.names,2)};caps.append(c)
            expected=[run_sequence(caps,s,p) for s in universe]
            try:composite=m.compose(caps)
            except ValueError:
                self.assertTrue(all(s is None for s in expected));continue
            for s,out in zip(universe,expected):
                try:actual=m.apply(composite,s)
                except ValueError:actual=None
                self.assertEqual(actual,out)
    def test_numeric_only_roundtrip_composition(self):
        for p in self.problems:
            m=FactoredEmbedding(p);original=[m.encode(c) for c in p['capabilities'][:3]]
            decoded=[m.from_vector(e.values.copy()) for e in original]
            for a,b in zip(original,decoded):np.testing.assert_array_equal(a.values,b.values)
            np.testing.assert_allclose(m.compose(original).values,m.compose(decoded).values)
            with self.assertRaises(ValueError):m.from_vector([1,2,3])
    def test_external_contract_intersection(self):
        a=json.loads(json.dumps(self.c[0]));b=json.loads(json.dumps(self.c[0]))
        # Repeated external requirements are merged, not silently overwritten.
        a['inputs'][0]['required']=False;b['inputs'][0]['required']=True
        e=self.m.compose([a,b]);self.assertEqual(len(e.metadata['inputs']),1)
        self.assertTrue(e.metadata['inputs'][0]['required'])
if __name__=='__main__':unittest.main()
