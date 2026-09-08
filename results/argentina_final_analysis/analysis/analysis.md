# 4. Experiments & Results

Generated descriptive results and discussion prompts. Complete the interpretation after the full experiment campaign.

## 4.1 Experimental setup

Three questions: **quality** (final MSE), **speed** (runtime and convergence), and **stability** (variation across independent seeds).

Baseline directory: `elite_one_point_gene_t50_p50_g1000_d3d509753036`. Planned runs/configuration: **5**. Observed baseline seeds: `[1, 2, 3, 4, 5]`.

The main experiment budget means the resources chosen for the final comparisons: a fixed generation limit per run and a planned number of seeds per configuration. Population size is fixed except in its own experiment. This is not a runtime limit and does not guarantee that the GA has converged.

Saved baseline configuration (the random seed varies):

```json
{
  "n_triangles": 50,
  "target_image_path": "/Users/hannahkalager/72.27-Delivery-2/data/flag_100.png",
  "population_size": 50,
  "n_generations": 1000,
  "min_error": null,
  "selection_method": "elite",
  "tournament_size": 3,
  "tournament_probability": 0.75,
  "boltzmann_temperature": 1.0,
  "crossover_method": "one_point",
  "crossover_rate": 0.9,
  "mutation_method": "gene",
  "mutation_rate": 0.05,
  "survival_strategy": "additive",
  "extra": {}
}
```

MSE is averaged over RGB channels after dividing pixel values by 255, so it lies in [0, 1]. Lower is better. Fitness is 1/(1 + MSE); per-run fitness is exported to CSV.

Each comparison changes one saved setting relative to the same baseline. Baseline runs are reused across sections and counted once in the overall comparison.

Curves show median best-so-far MSE with IQR (25th–75th percentile), not a confidence interval. Exception: survival curves show current-generation best MSE so losses remain visible. Generation 0 is initialization. SD uses n−1; SD and IQR are omitted for a single run.

GA time (`ga_elapsed_s`) measures only `run_ga`, including initialization and fitness evaluation. Total time (`elapsed`) includes subprocess startup, image loading, GA, plotting and file output. These are separate metrics; legacy runs have no GA timing. No generation timestamps or evaluation counts were saved, so time-to-target and equal-evaluation convergence cannot be reconstructed.

Generation of best is the first minimum observed MSE. A small value can indicate an early plateau at poor quality, so it is not a speed ranking by itself.

Record hardware, software revision, target image dimensions and execution conditions for the full campaign. New runner outputs store target_sha256; legacy runs lack that hash.

### Data coverage

- Some runs lost earlier best solutions: final MSE describes the returned final population. Survival curves show current-generation best MSE; other convergence comparisons show best-so-far MSE.

### Baseline check: understand the repeated runs first

The baseline figures compare seeds of one configuration. They do not compare selection methods, crossovers, mutations, survival strategies, triangle counts or populations. Those comparisons appear below only when alternatives have been run.

![4.1 Baseline check — progress across seeds](4_1_baseline_seed_convergence.png)

Each line is a different seed using the SAME configuration, not a different method. A falling line means improvement; a flat line means no new best solution. Separated lines show variation between runs.

| Seed | Initial MSE | Final MSE ↓ | GA time (s) | First gen. of best |
| --- | --- | --- | --- | --- |
| 1 | 0.0936385 | 0.0319255 | 22.7643 | 997 |
| 2 | 0.103586 | 0.0276453 | 22.7207 | 995 |
| 3 | 0.10645 | 0.028358 | 22.3799 | 997 |
| 4 | 0.10186 | 0.030149 | 22.5724 | 994 |
| 5 | 0.107457 | 0.0306073 | 22.608 | 1000 |

![4.1 Baseline check — generated images](4_1_baseline_seed_images.png)

All available baseline seeds are shown. They use the same settings; differences arise from the random run. Compare the visible shapes and colours as well as MSE.

## 4.2 Selection methods

![4.2 Selection methods — convergence](4_2_selection_convergence.png)

Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), not a confidence interval. Lower curves mean better solutions at that generation. n = number of runs; generation speed is not wall-clock speed. 

![4.2 Selection methods — quality and stability](4_2_selection_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltzmann | 5 | 0.0379757 | 0.0379809 | 0.00207541 | 0.00148542 | 22.5577 | 5 | 23.2136 | 5 | 996 |
| elite | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| ranking | 5 | 0.0282181 | 0.0281362 | 0.00255816 | 0.00412024 | 23.1419 | 5 | 23.8549 | 5 | 1000 |
| roulette | 5 | 0.0379757 | 0.0379809 | 0.00207541 | 0.00148542 | 22.5637 | 5 | 23.2198 | 5 | 996 |
| tournament_deterministic | 5 | 0.0276592 | 0.0264916 | 0.00242742 | 0.00373972 | 22.9513 | 5 | 23.5903 | 5 | 1000 |
| tournament_probabilistic | 5 | 0.0307001 | 0.0306405 | 0.00173307 | 0.00159779 | 24.3749 | 5 | 25.0528 | 5 | 999 |
| universal | 5 | 0.028032 | 0.029327 | 0.00309811 | 0.00326872 | 22.551 | 5 | 23.2206 | 5 | 996 |

**Analysis prompts:** Compare selection pressure and exploration using both the curves and final distributions. Do the seeds support the same tendency? These metrics do not directly measure diversity.

Write your interpretation here, citing measured differences and uncertainty.

## 4.3 Crossover methods

![4.3 Crossover methods — convergence](4_3_crossover_convergence.png)

Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), not a confidence interval. Lower curves mean better solutions at that generation. n = number of runs; generation speed is not wall-clock speed. 

![4.3 Crossover methods — quality and stability](4_3_crossover_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| one_point | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| two_point | 5 | 0.0301618 | 0.0295114 | 0.00267375 | 0.00384651 | 22.9628 | 5 | 23.7041 | 5 | 999 |
| uniform | 5 | 0.0231604 | 0.0235088 | 0.00196266 | 0.00126024 | 23.1481 | 5 | 23.789 | 5 | 998 |

**Analysis prompts:** Compare quality, convergence and spread. Relate observations to how each operator preserves or recombines the ordered triangle genes and their drawing order.

Write your interpretation here, citing measured differences and uncertainty.

## 4.4 Number of triangles

![4.4 Number of triangles — quality and stability](4_4_triangles_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

![4.4 Number of triangles — computational cost](4_4_triangles_ga_runtime.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Compare typical runtime and its spread.

![4.4 Number of triangles — visual quality](4_4_triangles_images.png)

Each configuration shows the run closest to its median final MSE. Compare shapes, colours and detail with the target; MSE alone does not measure recognizability.

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 5 | 0.0237897 | 0.0243702 | 0.00293177 | 0.00338809 | 12.5401 | 5 | 13.171 | 5 | 996 |
| 50 | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| 100 | 5 | 0.0346091 | 0.0338125 | 0.00321389 | 0.00351001 | 41.2885 | 5 | 41.9815 | 5 | 999 |

**Analysis prompts:** Compare the MSE improvement with additional runtime and visible differences. More triangles increase representational capacity and the search space. The displayed run is closest to median final MSE, not chosen as the best-looking image.

Write your interpretation here, citing measured differences and uncertainty.

## 4.5 Population size

![4.5 Population size — quality and stability](4_5_population_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

![4.5 Population size — computational cost](4_5_population_ga_runtime.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Compare typical runtime and its spread.

![4.5 Population size — convergence](4_5_population_convergence.png)

Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), not a confidence interval. Lower curves mean better solutions at that generation. n = number of runs; generation speed is not wall-clock speed. 

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| 100 | 5 | 0.0209263 | 0.0203423 | 0.00109133 | 0.0017704 | 44.7271 | 5 | 45.4274 | 5 | 1000 |
| 200 | 5 | 0.0151877 | 0.0147273 | 0.00426566 | 0.00641113 | 89.0384 | 5 | 89.7979 | 5 | 999 |

**Analysis prompts:** Compare quality gains with runtime and convergence. Equal generations are not an equal computational budget when population size changes; larger populations process more candidates.

Write your interpretation here, citing measured differences and uncertainty.

## 4.6 Survival strategies

![4.6 Survival strategies — convergence](4_6_survival_convergence.png)

Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), not a confidence interval. Lower curves mean better solutions at that generation. n = number of runs; generation speed is not wall-clock speed. Current-generation best, not best-so-far: increases reveal lost quality; the median can hide losses in individual runs.

![4.6 Survival strategies — quality and stability](4_6_survival_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| additive | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| exclusive | 5 | 0.0533009 | 0.0528459 | 0.00119183 | 0.00172817 | 23.5466 | 5 | 24.2396 | 5 | 839 |

**Analysis prompts:** Compare additive (parents and offspring compete) with exclusive (only offspring survive). Does retaining parents improve final quality and consistency? Compare median GA time too. These curves show current-generation best MSE: exclusive may lose an earlier best solution. The median can hide individual losses; inspect per-seed histories and best_observed_mse in runs.csv. These measurements do not establish population diversity.

Write your interpretation here, citing measured differences and uncertainty.

## 4.7 Mutation methods

![4.7 Mutation methods — convergence](4_7_mutation_convergence.png)

Each colour is one configuration. Line = median across seeds; shading = middle 50% (IQR), not a confidence interval. Lower curves mean better solutions at that generation. n = number of runs; generation speed is not wall-clock speed. 

![4.7 Mutation methods — quality and stability](4_7_mutation_final_mse.png)

Each dot is one run (seed). Box = middle 50%; line inside = median. Whiskers extend to observations within 1.5 × IQR; all runs are shown as dots. Lower boxes indicate better quality; shorter boxes indicate less variation.

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete | 5 | 0.0472635 | 0.0472663 | 0.00175261 | 0.00190843 | 23.0005 | 5 | 23.6684 | 5 | 559 |
| gene | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| multigene | 5 | 0.00524106 | 0.0065421 | 0.00212068 | 0.00316717 | 23.4787 | 5 | 24.1426 | 5 | 1000 |
| uniform | 5 | 0.00571993 | 0.00515072 | 0.00119956 | 0.00144579 | 23.5529 | 5 | 24.2082 | 5 | 999 |

**Analysis prompts:** Compare convergence, final quality, seed variation and GA runtime with all other settings fixed. The same numerical mutation rate does not imply the same amount of mutation: gene can change one triangle per individual; multigene tests a random subset; uniform tests every triangle; complete perturbs every triangle when triggered for an individual. Each selected triangle has one coordinate or colour component changed. Relate results to these differences without claiming that diversity was measured directly.

Write your interpretation here, citing measured differences and uncertainty.

## 4.8 Overall comparison

| Configuration | n | Median MSE ↓ | Mean MSE ↓ | Sample SD | IQR | Median GA time (s) ↓ | GA timed n | Median total time (s) | Total timed n | Median gen. of best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltzmann_one_point_gene_t50_p50_g1000_7ea994f1e294 | 5 | 0.0379757 | 0.0379809 | 0.00207541 | 0.00148542 | 22.5577 | 5 | 23.2136 | 5 | 996 |
| elite_one_point_gene_t50_p50_g1000_d3d509753036 | 5 | 0.030149 | 0.029737 | 0.00173158 | 0.00224932 | 22.608 | 5 | 23.3037 | 5 | 997 |
| ranking_one_point_gene_t50_p50_g1000_70b89f0f2bd7 | 5 | 0.0282181 | 0.0281362 | 0.00255816 | 0.00412024 | 23.1419 | 5 | 23.8549 | 5 | 1000 |
| roulette_one_point_gene_t50_p50_g1000_4aab039e7d74 | 5 | 0.0379757 | 0.0379809 | 0.00207541 | 0.00148542 | 22.5637 | 5 | 23.2198 | 5 | 996 |
| tournament_deterministic_one_point_gene_t50_p50_g1000_2f9f07a94022 | 5 | 0.0276592 | 0.0264916 | 0.00242742 | 0.00373972 | 22.9513 | 5 | 23.5903 | 5 | 1000 |
| tournament_probabilistic_one_point_gene_t50_p50_g1000_b3de1d2f5ab0 | 5 | 0.0307001 | 0.0306405 | 0.00173307 | 0.00159779 | 24.3749 | 5 | 25.0528 | 5 | 999 |
| universal_one_point_gene_t50_p50_g1000_fbc97141c7a2 | 5 | 0.028032 | 0.029327 | 0.00309811 | 0.00326872 | 22.551 | 5 | 23.2206 | 5 | 996 |
| elite_two_point_gene_t50_p50_g1000_34c544b6bde4 | 5 | 0.0301618 | 0.0295114 | 0.00267375 | 0.00384651 | 22.9628 | 5 | 23.7041 | 5 | 999 |
| elite_uniform_gene_t50_p50_g1000_cf90f39932df | 5 | 0.0231604 | 0.0235088 | 0.00196266 | 0.00126024 | 23.1481 | 5 | 23.789 | 5 | 998 |
| elite_one_point_gene_t20_p50_g1000_cf20acdfaf93 | 5 | 0.0237897 | 0.0243702 | 0.00293177 | 0.00338809 | 12.5401 | 5 | 13.171 | 5 | 996 |
| elite_one_point_gene_t100_p50_g1000_90c81bc172ec | 5 | 0.0346091 | 0.0338125 | 0.00321389 | 0.00351001 | 41.2885 | 5 | 41.9815 | 5 | 999 |
| elite_one_point_gene_t50_p100_g1000_6ed7167af499 | 5 | 0.0209263 | 0.0203423 | 0.00109133 | 0.0017704 | 44.7271 | 5 | 45.4274 | 5 | 1000 |
| elite_one_point_gene_t50_p200_g1000_016662187939 | 5 | 0.0151877 | 0.0147273 | 0.00426566 | 0.00641113 | 89.0384 | 5 | 89.7979 | 5 | 999 |
| elite_one_point_gene_t50_p50_g1000_c65538566291 | 5 | 0.0533009 | 0.0528459 | 0.00119183 | 0.00172817 | 23.5466 | 5 | 24.2396 | 5 | 839 |
| elite_one_point_complete_t50_p50_g1000_33630d663cb9 | 5 | 0.0472635 | 0.0472663 | 0.00175261 | 0.00190843 | 23.0005 | 5 | 23.6684 | 5 | 559 |
| elite_one_point_multigene_t50_p50_g1000_a7a255ad520f | 5 | 0.00524106 | 0.0065421 | 0.00212068 | 0.00316717 | 23.4787 | 5 | 24.1426 | 5 | 1000 |
| elite_one_point_uniform_t50_p50_g1000_b2d3afb3cff4 | 5 | 0.00571993 | 0.00515072 | 0.00119956 | 0.00144579 | 23.5529 | 5 | 24.2082 | 5 | 999 |

- Quality: lowest median final MSE: **elite_one_point_multigene_t50_p50_g1000_a7a255ad520f** (0.00524106).

- Speed: lowest median GA runtime: **elite_one_point_gene_t20_p50_g1000_cf20acdfaf93** (12.5401).

- Stability: lowest final-MSE IQR: **elite_uniform_gene_t50_p50_g1000_cf90f39932df** (0.00126024).

These are descriptive leaders among available configurations, not evidence of a universal winner or statistical significance. See coverage warnings before drawing conclusions. Low variability can mean consistently poor results; assess stability alongside quality.

**Analysis prompts:** Which configuration suits each objective? How large are quality gains relative to runtime and seed variation? Combining preferred settings from individual-factor experiments requires a separate validation experiment.
