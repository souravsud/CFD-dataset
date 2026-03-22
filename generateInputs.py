import os
from copy import deepcopy
from dataclasses import asdict
import yaml
from terrain_fetcher import download_raster_data, create_output_dir, load_config
from abl_bc_generator import (
    generate_inlet_data_workflow,
    ABLConfig,
    AtmosphericConfig,
    TurbulenceConfig,
    MeshConfig,
    OpenFOAMConfig,
)
from terrain_fetcher.csv_utils import load_coordinates_from_csv
import terrain_mesh as tm


def generate_directions(sectors: int) -> list[int]:
    """Generate evenly spaced wind directions in degrees over [0, 360)."""
    if sectors <= 0:
        raise ValueError("sectors must be > 0")
    step = 360.0 / sectors
    return [int(round(i * step)) % 360 for i in range(sectors)]


def _deep_update(base: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_abl_config(yaml_path: str) -> ABLConfig:
    """Load ABLConfig from YAML, merging with package defaults."""
    cfg_dict = asdict(ABLConfig())

    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as fh:
            file_cfg = yaml.safe_load(fh) or {}
        if not isinstance(file_cfg, dict):
            raise ValueError(f"Expected YAML mapping at root: {yaml_path}")
        cfg_dict = _deep_update(cfg_dict, file_cfg)

    return ABLConfig(
        atmospheric=AtmosphericConfig(**cfg_dict.get("atmospheric", {})),
        turbulence=TurbulenceConfig(**cfg_dict.get("turbulence", {})),
        mesh=MeshConfig(**cfg_dict.get("mesh", {})),
        openfoam=OpenFOAMConfig(**cfg_dict.get("openfoam", {})),
    )

def main():
    SECTORS = 16
    
    root_folder = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(root_folder, "coords.csv")
    fetcher_config_path = os.path.join(root_folder, "configs", "terrain_fetcher_config.yaml")
    abl_config_path = os.path.join(root_folder, "configs", "abl_bc_config.yaml")
    data_folder = os.path.join(root_folder, "Data")
    download_folder = os.path.join(data_folder, "downloads")
    
    # Configure download settings from shared YAML config.
    download_config = load_config(fetcher_config_path)
    mesh_config = tm.load_config(os.path.join(root_folder, "configs", "terrain_config.yaml"))
    inletBC_config = load_abl_config(abl_config_path)
    terrain_mesh_pipeline = tm.TerrainMeshPipeline()
    
    # Read CSV
    coordinates = load_coordinates_from_csv(csv_path, verbose=True)
    print(f"Using terrain fetcher config: {fetcher_config_path}")
    print(f"Using ABL BC config: {abl_config_path}")
    print(f"Starting complete pipeline for {len(coordinates)} locations...")
    print("Starting batch download of DEM tiles")
    
    results = []
    for i, (lat, lon) in enumerate(coordinates):
        try:
            #Save folder for each location
            download_path = create_output_dir(lat, lon, i, download_folder)
            if download_path is None:
                print(f"✓ Terrain already exists! Skipping index {(i+1):04d} ( Lat:{lat:.3f}, Lon:{lon:.3f})")
                results.append((i, None, None))
                continue

            dem_file, roughness_file = download_raster_data(
                                                            lat=lat,
                                                            lon=lon,
                                                            index=i,
                                                            out_dir=download_path,
                                                            config=download_config
                                                        )
            
            print(f"✓ DEM downloaded: {dem_file}")
            if roughness_file:
                print(f"✓ Roughness map downloaded: {roughness_file}")
            
            #processing and mesh generation
            directions = generate_directions(SECTORS)
            for direction in directions:
                mesh_config["terrain_config"].rotation_deg = direction
                inletBC_config.flow_dir_deg = direction
                
                subdir = f"rotatedTerrain_{direction:03d}_deg"
                path = os.path.join(download_path, subdir)
                os.makedirs(path, exist_ok=True)

                terrain_iterations = terrain_mesh_pipeline.run(
                                                    dem_path=dem_file,
                                                    rmap_path=roughness_file,
                                                    output_dir=path,
                                                    **mesh_config
                                                )
                profiles = generate_inlet_data_workflow(path , inletBC_config)
            
            results.append((i, dem_file, roughness_file,terrain_iterations))
            
        except Exception as e:
            print(f"✗ Failed row {i}: {e}")
            results.append((i, None, None, None))
    
    successful = len([r for r in results if r[1] is not None])
    print(f"\nPipeline completed! Downloaded {successful}/{len(coordinates)} locations successfully.") 
    return results

if __name__ == "__main__":
    main()
