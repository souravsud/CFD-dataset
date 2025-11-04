import os
from fetchData import download_raster_data, DownloadConfig
from fetchData.csv_utils import load_coordinates_from_csv

def main():
    root_folder = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(root_folder, "coords.csv")
    data_folder = os.path.join(root_folder, "Data")
    download_folder = os.path.join(data_folder, "downloads")
    
    # Configure download settings ONCE
    config = DownloadConfig(
        dem_name="glo_30",
        dst_ellipsoidal_height=False,
        dst_area_or_point="Point",
        side_length_km=50,
        include_roughness_map=True,
        save_raw_files=True,  # Enable for debugging
        out_dir=download_folder,
        verbose=True,
        show_plots=False
    )
    
    # Read CSV
    coordinates = load_coordinates_from_csv(csv_path, verbose=True)
    print(f"Starting complete pipeline for {len(coordinates)} locations...")
    print("Starting batch download of DEM tiles")
    
    results = []
    for i, (lat, lon) in enumerate(coordinates):
        try:
            # Only pass dynamic variables!
            dem_file, roughness_file = download_raster_data(
                lat=lat,
                lon=lon,
                index=i,
                config=config
            )
            
            print(f"✓ DEM downloaded: {dem_file}")
            if roughness_file:
                print(f"✓ Roughness map downloaded: {roughness_file}")
            
            results.append((i, dem_file, roughness_file))
            
        except Exception as e:
            print(f"✗ Failed row {i}: {e}")
            results.append((i, None, None))
    
    successful = len([r for r in results if r[1] is not None])
    print(f"\nPipeline completed! Downloaded {successful}/{len(coordinates)} locations successfully.") 
    return results

if __name__ == "__main__":
    main()