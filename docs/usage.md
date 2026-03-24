# Usage

## 1. Define Input Coordinates

Edit `coords.csv` with the latitude and longitude of each site:

```csv
lat,lon
39.71121111,-7.73483333
```

## 2. Configurations

Edit the files in `configs/` to customise pipeline behaviour:

| File | Purpose |
|------|---------|
| `configs/terrain_config.yaml` | Domain and mesh parameters |
| `configs/terrain_fetcher_config.yaml` | DEM/roughness map download behaviour |
| `configs/abl_bc_config.yaml` | ABL inlet profile and OpenFOAM boundary conditions |
| `configs/taskmanager_config.yaml` | Job management on the HPC cluster |

Refer to the individual package repositories for detailed parameter descriptions.

## 3. Generate Terrain Inputs

**Option A — Script (single run):**

```bash
python generateInputs.py
```

**Option B — Notebook (recommended for batch processing and resuming):**

```bash
jupyter notebook notebooks/input_generation_dashboard.ipynb
```

For each coordinate and wind direction the pipeline:
- Downloads a DEM and roughness raster (controlled by `configs/terrain_fetcher_config.yaml`)
- Rotates and crops the terrain
- Generates terrain surface mesh and blockMesh dictionary file
- Creates ABL inlet boundary condition files
- Writes a `pipeline_metadata.json` summary

## 4. Create Cases and Submit to HPC

```bash
jupyter notebook notebooks/pipeline_dashboard.ipynb
```

Steps covered in this notebook:
1. Build OpenFOAM case directories from `pipeline_metadata.json` files
2. Run local meshing (since blockMesh is a serial operation) using parallel Python workers (one process per case)
3. Rsync cases to the HPC cluster
4. Submit SLURM jobs and record status in `case_status.json`

## 5. Monitor and Retrieve Results

```bash
jupyter notebook notebooks/pipeline_monitor.ipynb
```

Polls SLURM job statuses and fetches simulation outputs when jobs complete.
