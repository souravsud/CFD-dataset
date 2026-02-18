# CFD Dataset Generator

A Python pipeline for generating CFD (Computational Fluid Dynamics) terrain datasets from Digital Elevation Models (DEMs).

## Overview

This tool automates the process of:
1. **Downloading DEM tiles** for specified geographic coordinates
2. **Processing terrain data** into STL mesh files
3. **Generating multiple rotations** of terrain for wind direction simulation
4. **Batch processing** multiple locations from a CSV file

## Features

- Downloads high-resolution DEM data (30m resolution) using the GLO-30 dataset
- Processes terrain with sophisticated boundary smoothing for CFD analysis
- Generates rotated terrain meshes for different wind directions
- Supports batch processing of multiple locations
- Includes terrain visualization and debugging capabilities

## Directory Structure

```
CFD-dataset/
├── generateInputs.py          # Main entry point
├── coords.csv                  # Input coordinates (lat, lon)
├── GenerateInputs/             # Main package
│   ├── generateInputs.py       # Core pipeline implementation
│   ├── config.py               # Configuration parameters
│   ├── coords.csv              # Coordinates for processing
│   ├── dem_download/           # DEM download functionality
│   │   ├── dem_downloader.py
│   │   ├── csv_utils.py
│   │   └── download_config.py
│   └── dem_processing/         # DEM processing and terrain generation
│       ├── dem_processor.py
│       ├── terrain_smoothing.py
│       ├── geo_utils.py
│       ├── csv_utils.py
│       ├── debug_utils.py
│       ├── meta_data_process.py
│       ├── process_config.py
│       └── randomDirections.py
└── Data/                       # Output directory (created automatically)
    ├── downloads/              # Downloaded DEM files
    └── terrain_input/          # Processed terrain files
```

## Usage

### 1. Prepare Input Coordinates

Create or edit `coords.csv` with your locations:

```csv
lat,lon
39.71121111,-7.73483333
```

Each row represents a location where terrain data will be generated.

### 2. Run the Pipeline

```bash
python generateInputs.py
```

Or run from the GenerateInputs directory:

```bash
cd GenerateInputs
python generateInputs.py
```

### 3. Output Structure

The pipeline creates organized output directories:

```
Data/terrain_input/
└── terrain_0001_39.711N_7.735W/
    ├── rotatedTerrain_000_deg/
    │   └── terrain.stl
    ├── rotatedTerrain_045_deg/
    │   └── terrain.stl
    └── ...
```

## Configuration

Edit `GenerateInputs/config.py` to customize processing parameters:

```python
class Config:
    # Download parameters
    DEM_NAME = "glo_30"                 # DEM dataset name
    DOWNLOAD_SIDE_LENGTH_KM = 50        # Download area size
    
    # Processing parameters
    PROCESS_CROP_SIZE_KM = 31           # Final terrain size
    DEBUG_PROCESS = True                # Enable debug visualization
    VERBOSE_PROCESS = True              # Verbose output
```

## Processing Details

### DEM Download
- Uses GLO-30 dataset (30m resolution)
- Downloads 50km x 50km tiles around each coordinate
- Handles coordinate transformations and projections

### Terrain Processing
- Crops to 31km x 31km final size
- Applies sophisticated boundary smoothing:
  - 30km computational domain
  - 8km area of interest (AOI)
  - Cosine-based transition zones for smooth boundaries
- Generates STL meshes suitable for CFD simulations

### Rotation Generation
- Generates multiple terrain rotations
- Supports both random and systematic direction sampling
- Default: systematic angles for complete wind rose coverage

## Requirements

The pipeline requires the following Python packages:
- numpy
- pandas
- rasterio
- geopandas
- matplotlib
- scipy
- trimesh (for STL generation)

## Error Handling

The pipeline includes robust error handling:
- Skips locations that already have processed terrain
- Continues processing remaining locations if one fails
- Reports success/failure for each location at the end

## Notes

- First run will download DEM tiles (may take time depending on network)
- Subsequent runs for the same location will skip processing if output exists
- Check the `Data/` directory for all outputs
- Debug mode saves visualization plots for quality control
