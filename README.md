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
├── terrain_config.yaml                 # Mesh and domain configuration
├── generateInputs.py                   # Main orchestration script
├── environment.yml                     # Conda environment specification
│
├── terrain-fetcher (external package)  # Downloads DEMs and roughness rasters
├── terrain_following_mesh_generator/   # Generates 3D terrain-following meshes (submodule)
├── ABL_BC_generator/                   # Creates ABL inlet boundary conditions (submodule)
├── taskManager/                        # Manages OpenFOAM cases and HPC submission (submodule)
│
├── input_generation_dashboard.ipynb    # Interactive batch input generation
├── pipeline_dashboard.ipynb            # Case creation, meshing, and HPC submission
├── pipeline_monitor.ipynb              # Job monitoring and result retrieval
├── parallelisation_benchmark.ipynb     # Strong-scaling benchmark
└── grid_independence_test.ipynb        # Mesh independence study
```

## Prerequisites

### Software

- [Conda](https://docs.conda.io/) (for environment management)
- [OpenFOAM](https://www.openfoam.com/) (for local meshing and case setup)
- [SLURM](https://slurm.schedmd.com/) workload manager (on the HPC cluster)
- SSH/rsync access to the HPC cluster (configured in `~/.ssh/config`)

### Python Environment

Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate cfd-dataset
```

Install `terrain-fetcher` from its separate repository before running input generation:

```bash
pip install git+https://github.com/souravsud/terrain-fetcher.git@main
```

Key Python dependencies include:

| Package | Purpose |
|---------|---------|
| `dem_stitcher` | Download and stitch DEM tiles |
| `rasterio` / `pyproj` / `geopandas` | Geospatial processing |
| `pyvista` | 3D mesh visualisation |
| `numpy` / `scipy` | Numerical computation |
| `pyyaml` | YAML configuration parsing |
| `windkit` | Wind resource calculations |

### Submodules

Initialise all Git submodules after cloning:

```bash
git submodule update --init --recursive
```

## Usage

### 1. Define Input Coordinates

Edit `coords.csv` with the latitude and longitude of each site:

```csv
lat,lon
39.71121111,-7.73483333
```

### 2. Configurations

Edit `configs/terrain_config.yaml` to set domain and mesh parameters, `configs/terrain_fetcher_config.yaml` to control DEM/roughness map download behaviour, `configs/abl_bc_config.yaml` to control ABL inlet profile and OpenFOAM boundary-condition and `configs/taskmanager_config.yaml` to setup the job management in the HPC cluster. Refer to individual repos for more info.

### 3. Generate Terrain Inputs

**Option A — Script (single run):**

```bash
python generateInputs.py
```

**Option B — Notebook (recommended for batch processing and resuming):**

```bash
jupyter notebook input_generation_dashboard.ipynb
```

For each coordinate and wind direction the pipeline:
- Downloads a DEM and roughness raster (controlled by `configs/terrain_fetcher_config.yaml`)
- Rotates and crops the terrain
- Generates terrain surface mesh and  blockMesh dictionary file
- Creates ABL inlet boundary condition files
- Writes a `pipeline_metadata.json` summary

### 4. Create Cases and Submit to HPC

```bash
jupyter notebook pipeline_dashboard.ipynb
```

Steps covered in this notebook:
1. Build OpenFOAM case directories from `pipeline_metadata.json` files
2. Run local meshing (since blockMesh is a serial operation) using parallel Python workers (one process per case)
3. Rsync cases to the HPC cluster
4. Submit SLURM jobs and record status in `case_status.json`

### 5. Monitor and Retrieve Results

```bash
jupyter notebook pipeline_monitor.ipynb
```

Polls SLURM job statuses and fetches simulation outputs when jobs complete.

## Output Structure

```
Data/downloads/
└── terrain_0001_N39_71500_W007_73500/
    ├── terrain_0001_glo_30_N39_71500_W007_73500_50km.tif   # DEM raster
    ├── terrain_0001_glo_30_*.json                           # Download metadata
    └── rotatedTerrain_000_deg/
        ├── blockMeshDict
        ├── pipeline_metadata.json
        └── [mesh and boundary-condition files]

openFoamCases/
└── case_0001_terrain_0001_dir_000/
    ├── 0/              # Initial conditions
    ├── constant/       # Physical properties
    ├── system/         # Numerical schemes and solver settings
    └── case_status.json
```

## Benchmarking

Two notebooks are provided for validation and performance studies:

| Notebook | Purpose |
|----------|---------|
| `parallelisation_benchmark.ipynb` | Scaling study — fixed mesh, varying core count |
| `grid_independence_test.ipynb` | Mesh independence study — multiple resolutions to verify convergence |

## License

See [LICENSE](LICENSE) for details.
