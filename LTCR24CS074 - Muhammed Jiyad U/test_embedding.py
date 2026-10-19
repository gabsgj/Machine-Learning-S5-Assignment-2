import unittest,json
from pathlib import Path
import numpy as np
from embedding import Embedding,similarity
class Tests(unittest.TestCase):
    def setUp(self):
        self.p=json.loads(Path(__file__).with_name('dataset.json').read_text())['problems'][0]
        self.m=Embedding(self.p);self.c=self.p['capabilities'];self.s=self.p['initial_state']
    def test_compatibility_and_typed_ports(self):
        self.assertTrue(self.m.compatibility(self.c[0],self.c[1])['guaranteed'])
        self.assertFalse(self.m.compatibility(self.c[0],self.c[3])['existential'])
        self.assertFalse(self.m.compatibility(self.c[0],self.c[7])['io_compatible'])
        with self.assertRaises(ValueError):self.m.compose([self.c[0],self.c[7]])
    def test_constraints_and_missing_inputs(self):
        c=self.c[8]
        with self.assertRaises(ValueError):self.m.execute(c,{**self.s,'quantity':0},self.p['available_resources'],{'request':'valid'})
        with self.assertRaises(ValueError):self.m.execute(c,self.s,[],{'request':'valid'})
        with self.assertRaises(ValueError):self.m.execute(c,self.s,self.p['available_resources'],{})
        c={**c,'available':False}
        with self.assertRaises(ValueError):self.m.execute(c,self.s,self.p['available_resources'],{'request':'valid'})
    def test_order_and_associativity(self):
        e=[self.m.encode(c) for c in self.c[:3]]
        a=self.m.compose([self.m.compose(e[:2]),e[2]])
        b=self.m.compose([e[0],self.m.compose(e[1:])])
        np.testing.assert_allclose(a.vector,b.vector)
        self.assertEqual(self.m.goal_score(a,self.s,self.p['goal']),1)
        reverse=self.m.compose(e[::-1])
        self.assertEqual(self.m.goal_score(reverse,self.s,self.p['goal']),0)
        self.assertFalse(np.array_equal(a.transition,reverse.transition))
    def test_identity_and_schema(self):
        a=self.m.encode(self.c[0]);b=self.m.encode(self.c[4])
        self.assertAlmostEqual(similarity(a,b),1)
        self.assertFalse(np.array_equal(a.vector,b.vector))
        other=json.loads(Path(__file__).with_name('dataset.json').read_text())['problems'][1]
        with self.assertRaises(ValueError):similarity(a,Embedding(other).encode(other['capabilities'][0]))
    def test_empty_invalid_sequences(self):
        with self.assertRaises(ValueError):self.m.compose([])
        with self.assertRaises(ValueError):self.m.compose([self.c[0],self.c[3]])
if __name__=='__main__':unittest.main()
