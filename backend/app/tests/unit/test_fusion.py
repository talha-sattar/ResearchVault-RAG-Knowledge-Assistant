from app.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_rewards_items_ranked_highly_in_multiple_lists():
    dense = ["a", "b", "c", "d"]
    sparse = ["b", "a", "e", "f"]
    fused = reciprocal_rank_fusion([dense, sparse])
    fused_ids = [item_id for item_id, _ in fused]

    # "a" and "b" appear near the top of both lists, so should outrank items unique to one list.
    assert fused_ids[0] in ("a", "b")
    assert fused_ids[1] in ("a", "b")
    assert set(fused_ids) == {"a", "b", "c", "d", "e", "f"}


def test_rrf_scores_are_sorted_descending():
    fused = reciprocal_rank_fusion([["x", "y", "z"]])
    scores = [score for _, score in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_handles_empty_rankings():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
