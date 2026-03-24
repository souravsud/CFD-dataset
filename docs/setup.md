# Setup

## Software Prerequisites

- [Conda](https://docs.conda.io/) (for environment management)
- [OpenFOAM](https://www.openfoam.com/) (for local meshing and case setup)
- [SLURM](https://slurm.schedmd.com/) workload manager (on the HPC cluster)
- SSH/rsync access to the HPC cluster (configured in `~/.ssh/config`)

## Python Environment

Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate cfd-dataset
```

Key Python dependencies:

| Package | Purpose |
|---------|---------|
| `dem_stitcher` | Download and stitch DEM tiles |
| `rasterio` / `pyproj` / `geopandas` | Geospatial processing |
| `pyvista` | 3D mesh visualisation |
| `numpy` / `scipy` | Numerical computation |
| `pyyaml` | YAML configuration parsing |
| `windkit` | Wind resource calculations |

## Pipeline Packages

All pipeline dependencies are installed automatically by `environment.yml` (via pip). The key packages and their Python import names are:

| Package (GitHub) | Import name | Purpose |
|------------------|-------------|---------|
| [`terrain-fetcher`](https://github.com/souravsud/terrain-fetcher) | `terrain_fetcher` | Downloads DEMs and roughness rasters |
| [`terrain_following_mesh_generator`](https://github.com/souravsud/terrain_following_mesh_generator) | `terrain_mesh` | Generates 3D terrain-following meshes |
| [`ABL_BC_generator`](https://github.com/souravsud/ABL_BC_generator) | `abl_bc_generator` | Creates ABL inlet boundary conditions |
| [`taskManager`](https://github.com/souravsud/taskManager) | `taskmanager` | Manages OpenFOAM cases and HPC submission |

Running `conda env create -f environment.yml` installs all of the above.
