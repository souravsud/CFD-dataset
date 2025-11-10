import os
from fetchData import download_raster_data, create_output_dir, DownloadConfig
from inlet_profile_generator import generate_inlet_data_workflow, ABLConfig
from fetchData.csv_utils import load_coordinates_from_csv
from fetchData.parameter_generation import generate_directions
from terrain_following_mesh_generator import terrain_mesh as tm

def main():
    SECTORS = 16
    
    root_folder = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(root_folder, "coords.csv")
    data_folder = os.path.join(root_folder, "Data_test")
    download_folder = os.path.join(data_folder, "downloads")
    
    # Configure download settings ONCE
    download_config = DownloadConfig(
                                        side_length_km=50,
                                        include_roughness_map=True,
                                        save_raw_files=True,
                                        verbose=True,
                                        show_plots=True
                                    )
    mesh_config = tm.load_config("terrain_config.yaml")
    inletBC_config = ABLConfig()
    terrain_mesh_pipeline = tm.TerrainMeshPipeline()
    
    # Read CSV
    coordinates = load_coordinates_from_csv(csv_path, verbose=True)
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