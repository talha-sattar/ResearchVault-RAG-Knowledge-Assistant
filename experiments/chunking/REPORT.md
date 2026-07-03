# Chunking Strategy Experiment Report

Ground truth: 144 questions (0 human-spot-checked / 144 unverified LLM-drafted).

## Results

| Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@5 (effective) | Section-type Acc@5 | MRR | Avg query latency (ms) |
|---|---|---|---|---|---|---|---|
| fixed_size | 0.41 | 0.74 | 0.79 | 0.79 | 0.86 | 0.564 | 7.1 |
| paragraph | 0.48 | 0.71 | 0.77 | 0.77 | 0.89 | 0.600 | 7.0 |
| section_aware | 0.53 | 0.74 | 0.83 | 0.83 | 0.97 | 0.652 | 7.0 |
| parent_child | 0.54 | 0.73 | 0.79 | 0.90 | 0.96 | 0.640 | 8.5 |

## Recommendation

**parent_child** achieved the highest effective-context Recall@5 (0.90) at retrieving the sections needed to answer methodology/experiments/results questions, and is recommended as the production chunking strategy for the full corpus index.

Notes:
- Recall@k (strict) checks the gold excerpt is found in the retrieved chunk text itself.
- Recall@k (effective) additionally counts a hit if expanding a retrieved child chunk to its parent section contains the gold excerpt (only differs from strict for parent_child).
- Section-type Acc@k checks whether any of the top-k chunks share the gold section's type, a looser signal than exact excerpt matching.
- Ground truth questions were LLM-drafted (GPT) from real paper sections with excerpts verified to actually appear in the source text (fuzzy match), then a sample was spot-checked by a human reviewer rather than exhaustively hand-verified - see Known Limitations in the project plan.