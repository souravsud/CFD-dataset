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

Install `terrain-fetcher` from its separate repository before running input generation:

```bash
pip install git+https://github.com/souravsud/terrain-fetcher.git@main
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

## Submodules

Initialise all Git submodules after cloning:

```bash
git submodule update --init --recursive
```

The submodules provide:

| Submodule | Purpose |
|-----------|---------|
| `terrain-fetcher` | Downloads DEMs and roughness rasters |
| `terrain_following_mesh_generator` | Generates 3D terrain-following meshes |
| `ABL_BC_generator` | Creates ABL inlet boundary conditions |
| `taskManager` | Manages OpenFOAM cases and HPC submission |
