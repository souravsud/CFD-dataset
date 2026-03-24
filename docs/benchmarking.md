# Benchmarking

Two notebooks are provided in the `benchmarking/` directory for validation and performance studies.

## Parallelisation Benchmark

**Notebook:** `benchmarking/parallelisation_benchmark.ipynb`

Strong-scaling study: runs a fixed mesh problem with a varying number of CPU cores to characterise parallel efficiency and speedup.

```bash
jupyter notebook benchmarking/parallelisation_benchmark.ipynb
```

## Grid Independence Test

**Notebook:** `benchmarking/grid_independence_test.ipynb`

Mesh independence study: runs the same case at multiple mesh resolutions to verify that the solution has converged and is not sensitive to grid refinement.

```bash
jupyter notebook benchmarking/grid_independence_test.ipynb
```
