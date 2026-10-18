import json
from pathlib import Path

from experiments.phase03_baseline_composition import main


def test_experiment2_generates_expected_results():
    main()
    path = Path('results/baseline_v1_1/phase03_baseline_composition.json')
    assert path.exists()
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['chain_count'] == 2
    chains = {c['chain_id']: c for c in data['chains']}
    assert chains['purchase_success_chain']['chain_length'] == 7
    assert chains['cancel_and_release_chain']['chain_length'] == 3
    assert 0.0 <= chains['purchase_success_chain']['final_vector_consistency'] <= 1.0
    assert 0.0 <= chains['cancel_and_release_chain']['final_vector_consistency'] <= 1.0
    assert chains['purchase_success_chain']['final_goal_alignment'] > 0.9
    assert chains['purchase_success_chain']['final_reliability'] > 0.0
