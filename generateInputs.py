import os
import sys
import csv
from fetchData import download_dem
from fetchData.csv_utils import load_coordinates_from_csv, get_coordinate_by_index
from fetchData.download_raster import format_coord

dem_processing_path = os.path.join(os.path.dirname(__file__), 'dem_processing')
sys.path.insert(0, dem_processing_path)
#from dem_processing import process_dem_files, generate_directions, ProcessConfig

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
            
        except Exception as e:
            print(f"✗ Failed row {i}: {e}")
            results.append((i, None, None))
    print(f"\nPipeline completed! Processed {len([r for r in results if r[2]])} locations successfully.")
    
    return results

if __name__ == "__main__":
    main()