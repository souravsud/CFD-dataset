import os
import sys
import csv
from GenerateInput import download_dem
from GenerateInput.csv_utils import load_coordinates_from_csv, get_coordinate_by_index
from GenerateInput.dem_downloader import format_coord

dem_processing_path = os.path.join(os.path.dirname(__file__), 'dem_processing')
sys.path.insert(0, dem_processing_path)
from dem_processing import process_dem_files, generate_directions, ProcessConfig

def main():
    
    root_folder = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(root_folder, "coords.csv")
    data_folder = os.path.join(root_folder, "Data")
    download_folder = os.path.join(data_folder, "downloads")
    save_folder = os.path.join(data_folder, "terrain_input")

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        row_count = len(list(reader))
    
    print(f"Starting complete pipeline for {row_count} locations...")
    print("Starting batch download of DEM tiles")

    
    results = []
    for i in range(row_count):
        try:
            dem_file = download_dem(
                                    csv_path=csv_path,
                                    row_index=i,
                                    dem_name="glo_30",
                                    dst_ellipsoidal_height=False,
                                    dst_area_or_point="Point", 
                                    side_length_km=50,
                                    out_dir=download_folder,
                                    verbose=True,
                                    show_plots=False
                                )
            print(f"✓ DEM downloaded: {dem_file}")
            
            lat, lon = get_coordinate_by_index(csv_path, i, verbose=False)
            lat_str = format_coord(lat, is_lat=True, precision=3)
            lon_str = format_coord(lon, is_lat=False, precision=3)
            folder_name = f"terrain_{(i+1):04d}_{lat_str}_{lon_str}"
            folder_path = os.path.join(save_folder, folder_name)

            if not os.path.exists(folder_path):
                process = True
                os.makedirs(folder_path)
                print(f"Created new directory: {folder_name}")
            else:
                print(f"Alert: Terrain already exists: {folder_name}")
                process = False
                
            if process:
                directions = generate_directions(absolute_random=False)
                for direction in directions:
                    subdir = f"rotatedTerrain_{direction:03d}_deg"
                    path = os.path.join(folder_path, subdir)
                    os.makedirs(path, exist_ok=True)
                    stl_file = process_dem_files(
                                            dem_file=dem_file,
                                            csv_path=csv_path,
                                            row_index=i,
                                            rotation_deg=direction,
                                            crop_size_km=31,
                                            output_dir=path,
                                            debug_mode=False
                                        )
                    print(f"✓ STL created: {stl_file}")
            
            results.append((i, dem_file, stl_file))
            
        except Exception as e:
            print(f"✗ Failed row {i}: {e}")
            results.append((i, None, None))
    print(f"\nPipeline completed! Processed {len([r for r in results if r[2]])} locations successfully.")
    
    return results

if __name__ == "__main__":
    main()