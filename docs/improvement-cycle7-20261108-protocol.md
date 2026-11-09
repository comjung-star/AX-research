# Cycle7: negative sampling control for neural scoring

Cycle6 neural models put no working-transfer positives in Top5 despite decreasing training loss. A concrete alternative explanation is sampling bias: comparing every positive with only DenseTop20 negatives teaches low cosine as a positive signal while never penalizing promotion of easy irrelevant bottom cases.

Keep both cycle6 neural architectures, features,5query folds, seed, optimizer,100epochs and label policy unchanged. Change only negative sampling to all judged negatives among112 cases. Include all positives, query-average pairwise loss, no repeat replication during training, no hyperparameter change or early stopping. Keep all cycle6 unsupervised baselines exactly reproduced. Report neural single/multi against E and Dense under3 frozen label versions. Preserve cycle6 as a negative result and cycle7 as a separate artifact/source. No paid calls, new embeddings, test access or label changes.

The neural result is still an exploratory model on already inspected20queries with shared cases. An apparent fix to a sampling defect does not prove final superiority. Check the sample construction and evaluate model direction on synthetic pairs as well as actual query-held-out outcomes.
