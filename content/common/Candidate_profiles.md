# Candidate model profiles
These are candidate implementations offered for this exercise. An ensemble or neural network can also be trained with supervision. The four procurement labels below distinguish the four implementations in this comparison.

| Procurement label | Inference latency | Compute and operational cost | Interpretability | Robustness | Transparency and explanation |
| --- | --- | --- | --- | --- | --- |
| Supervised single model (logistic regression or a shallow decision tree) | Low | Low CPU demand; no accelerator | Coefficients or short decision paths are inspectable | Moderate; coverage depends on labeled patterns represented in training | A reviewer can examine model terms or a path directly |
| Unsupervised anomaly detector (isolation or clustering) | Low to moderate | Low to moderate CPU demand; fitting needs no outcome labels | Low to moderate; anomaly scores are indirectly related to specific causes | Can respond to unfamiliar patterns; normal changes can also look unusual | Individual flags commonly need further analysis |
| Ensemble (boosted trees or random forest) | Moderate | Moderate CPU demand for multiple trees | Moderate; aggregate importance describes overall patterns | Aggregation can reduce sensitivity to noise; performance still depends on training coverage | Individual decisions generally need post-hoc analysis for review |
| Deep learning model (multilayer network) | Moderate to high on CPU | High for the candidate at peak load; accelerator capacity may be needed | Low; internal representations are distributed | Can capture subtle patterns given representative data; behavior can change under shift | Post-hoc tools can approximate influential factors; complete traceability is difficult |

Latency and cost describe these candidate profiles. Neither table entries nor the client briefs are measured deployment benchmarks.
