# CFD Dataset Pipeline

An automated pipeline for generating terrain-aware Computational Fluid Dynamics (CFD) wind-flow datasets across multiple geographic locations. The pipeline covers the entire workflow from downloading geospatial data through to submitting simulations on an HPC cluster.

## Overview

Given a list of (latitude, longitude) coordinates, the pipeline:

1. **Downloads** high-resolution Digital Elevation Model (DEM) and land-cover rasters
2. **Generates** terrain-following meshes for each location and wind direction
3. **Creates** Atmospheric Boundary Layer (ABL) inlet profiles for OpenFOAM
4. **Builds** OpenFOAM case directories and runs local meshing
5. **Submits** CFD simulations to a SLURM-based HPC cluster
6. **Monitors** job status and retrieves results

## Repository Structure

```
CFD-dataset/
├── coords.csv                          # Input: list of (lat, lon) coordinates
├── generateInputs.py                   # Main orchestration script
├── environment.yml                     # Conda environment specification
├── configs/                            # YAML configuration files
│
├── notebooks/                          # Interactive workflow notebooks
│   ├── input_generation_dashboard.ipynb
│   ├── pipeline_dashboard.ipynb
│   └── pipeline_monitor.ipynb
│
├── benchmarking/                       # Validation and performance notebooks
│   ├── parallelisation_benchmark.ipynb
│   └── grid_independence_test.ipynb
│
└── docs/                               # Topic-specific documentation
    ├── setup.md
    ├── usage.md
    ├── output_structure.md
    └── benchmarking.md
```

## Quick Start

1. **Set up the environment** — see [docs/setup.md](docs/setup.md)
2. **Run the pipeline** — see [docs/usage.md](docs/usage.md)
3. **Understand the outputs** — see [docs/output_structure.md](docs/output_structure.md)
4. **Run benchmarks** — see [docs/benchmarking.md](docs/benchmarking.md)

## License

See [LICENSE](LICENSE) for details.
