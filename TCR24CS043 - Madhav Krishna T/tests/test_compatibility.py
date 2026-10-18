from src.evaluation import binary_metrics, rank_auc


def test_binary_metrics_perfect_case():
    metrics = binary_metrics([True, True, False, False], [True, True, False, False])
    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_rank_auc_perfect_ordering():
    assert rank_auc([True, True, False, False], [0.9, 0.8, 0.2, 0.1]) == 1.0
