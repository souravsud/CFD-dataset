import os
import sys
import csv
from config import Config
from dem_download import download_dem
from dem_download.csv_utils import get_coordinate_by_index
from dem_download.dem_downloader import format_coord

dem_processing_path = os.path.join(os.path.dirname(__file__), 'dem_processing')
sys.path.insert(0, dem_processing_path)
from dem_processing import process_dem_files, generate_directions

def main():
    """Main pipeline for generating CFD terrain datasets."""
    root_folder = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(root_folder, Config.CSV_FILENAME)
    data_folder = os.path.join(root_folder, Config.DATA_FOLDER)
    download_folder = os.path.join(data_folder, Config.DOWNLOAD_FOLDER)
    save_folder = os.path.join(data_folder, Config.TERRAIN_SAVE_FOLDER)

    # Count rows in CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        row_count = len(list(reader))
    
    print(f"Starting complete pipeline for {row_count} locations...")
    print("Starting batch download of DEM tiles")

    results = []
    for i in range(row_count):
        try:
            # Download DEM tile
            dem_file = download_dem(
                csv_path=csv_path,
                row_index=i,
                dem_name=Config.DEM_NAME,
                dst_ellipsoidal_height=Config.DST_ELLIPSOIDAL_HEIGHT,
                dst_area_or_point=Config.DST_AREA_OR_POINT, 
                side_length_km=Config.DOWNLOAD_SIDE_LENGTH_KM,
                out_dir=download_folder,
                verbose=Config.VERBOSE_DOWNLOAD,
                show_plots=Config.SHOW_PLOTS_DOWNLOAD
            )
            print(f"✓ DEM downloaded: {dem_file}")
            
            # Prepare output folder
            lat, lon = get_coordinate_by_index(csv_path, i, verbose=False)
            lat_str = format_coord(lat, is_lat=True, precision=3)
            lon_str = format_coord(lon, is_lat=False, precision=3)
            folder_name = f"terrain_{(i+1):04d}_{lat_str}_{lon_str}"
            folder_path = os.path.join(save_folder, folder_name)

            if os.path.exists(folder_path):
                print(f"Alert: Terrain already exists: {folder_name}")
                results.append((i, dem_file, 'skipped'))
                continue
                
            os.makedirs(folder_path)
            print(f"Created new directory: {folder_name}")
            
            # Process terrain for each direction
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
                    crop_size_km=Config.PROCESS_CROP_SIZE_KM,
                    output_dir=path,
                    debug_mode=Config.DEBUG_PROCESS,
                    verbose=Config.VERBOSE_PROCESS
                )
                print(f"✓ STL created: {stl_file}")
            
            results.append((i, dem_file, stl_file))
            
        except Exception as e:
            print(f"✗ Failed row {i}: {e}")
            # Use local variable if defined, otherwise None
            dem = locals().get('dem_file', None)
            results.append((i, dem, None))
    
    successful = len([r for r in results if r[2] is not None and r[2] != 'skipped'])
    skipped = len([r for r in results if r[2] == 'skipped'])
    print(f"\nPipeline completed! Processed {successful} locations successfully, skipped {skipped}.")
    
    return results

if __name__ == "__main__":
    main()