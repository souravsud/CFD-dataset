# Output Structure

After running the pipeline, outputs are organised as follows:

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

## Key Files

| File | Description |
|------|-------------|
| `pipeline_metadata.json` | Summary of all inputs generated for a terrain/direction combination |
| `case_status.json` | SLURM job status for each submitted case |
| `blockMeshDict` | OpenFOAM block mesh dictionary auto-generated from the terrain mesh |
