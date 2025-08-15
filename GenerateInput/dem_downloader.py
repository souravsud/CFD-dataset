# GenerateInput/dem_downloader.py
import math
from pathlib import Path
import rasterio
from rasterio import plot
import matplotlib.pyplot as plt
from dem_stitcher.stitcher import stitch_dem

from .csv_utils import load_coordinates_from_csv, get_coordinate_by_index

R = 6_371_000.0  # Earth's mean radius in meters

class DEMDownloader:
    """Handles DEM downloading with configurable options"""
    
    def __init__(self, config):
        self.config = config
    
    def log(self, message):
        """Conditional logging"""
        if self.config.verbose:
            print(message)
    
    def download_single_location(self, lat, lon, index):
        """Download DEM for a single coordinate pair"""
        self.log(f"Downloading DEM for lat={lat}, lon={lon}")
        
        return download_square_dem(
            index = index,
            center_lon=lon,
            center_lat=lat,
            side_km=self.config.side_length_km,
            dem_name=self.config.dem_name,
            dst_ellipsoidal_height=self.config.dst_ellipsoidal_height,
            dst_area_or_point=self.config.dst_area_or_point,
            out_dir=self.config.out_dir,
            verbose=self.config.verbose,
            show_plot=self.config.show_plots
        )
    
    def download_from_csv(self, csv_path):
        """Download DEMs for all locations in CSV"""
        coordinates = load_coordinates_from_csv(csv_path, self.config.verbose)
        
        self.log(f"Processing {len(coordinates)} locations...")
        
        results = []
        for idx, (lat, lon) in enumerate(coordinates):
            try:
                result_file = self.download_single_location(lat, lon)
                results.append((idx, lat, lon, result_file))
                self.log(f"✓ Location {idx+1}/{len(coordinates)} completed")
            except Exception as e:
                self.log(f"✗ Location {idx+1}/{len(coordinates)} failed: {e}")
                results.append((idx, lat, lon, None))
                continue
        
        return results
    
    def download_by_index(self, csv_path, index):
        """Download DEM for a specific CSV row index"""
        lat, lon = get_coordinate_by_index(csv_path, index, self.config.verbose)
        return self.download_single_location(lat, lon, index)

# Utility functions
def format_coord(value: float, is_lat: bool, precision: int = 5) -> str:
    """Format a latitude or longitude into a fixed-width, signed, filesystem-safe string."""
    if is_lat:
        hemi = "N" if value >= 0 else "S"
        width = 2
    else:
        hemi = "E" if value >= 0 else "W"
        width = 3

    abs_val = abs(value)
    deg = int(math.floor(abs_val))
    frac = abs_val - deg
    frac_int = int(round(frac * (10 ** precision)))

    deg_str = f"{deg:0{width}d}"
    frac_str = f"{frac_int:0{precision}d}"

    return f"{hemi}{deg_str}_{frac_str}"

def latlon_offset(lat: float, lon: float, dy_m: float, dx_m: float) -> tuple[float, float]:
    """Move a point northwards by dy_m meters and eastwards by dx_m meters."""
    dlat_rad = dy_m / R
    dlon_rad = dx_m / (R * math.cos(math.radians(lat)))

    new_lat = lat + math.degrees(dlat_rad)
    new_lon = lon + math.degrees(dlon_rad)
    return new_lat, new_lon

def download_square_dem(
    index : int,
    center_lon: float,
    center_lat: float,
    side_km: float,
    dem_name: str = "glo_30",
    dst_ellipsoidal_height: bool = True,
    dst_area_or_point: str = "Point",
    out_dir: str = "out",
    verbose: bool = False,
    show_plot: bool = False,  # Separated from verbose
):
    """Downloads a square DEM crop - your existing function with minor tweaks"""
    
    # Your existing logic here, but with show_plot parameter:
    half = (side_km * 1000) / 2
    
    corners = [
        latlon_offset(center_lat, center_lon, +half, +half),
        latlon_offset(center_lat, center_lon, +half, -half),
        latlon_offset(center_lat, center_lon, -half, -half),
        latlon_offset(center_lat, center_lon, -half, +half),
    ]
    
    lats = [pt[0] for pt in corners]
    lons = [pt[1] for pt in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    bounds = [min_lon, min_lat, max_lon, max_lat]
    
    if verbose:
        print(f"Bounds: {bounds}")

    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    lat_str = format_coord(center_lat, is_lat=True, precision=3)
    lon_str = format_coord(center_lon, is_lat=False, precision=3)
    side_str = f"{int(side_km)}km" if side_km.is_integer() else f"{side_km:.1f}km"
    file_name = f"terrain_{(index+1):04d}_{dem_name}_{lat_str}_{lon_str}_{side_str}.tif"

    X, profile = stitch_dem(
        bounds,
        dem_name=dem_name,
        dst_ellipsoidal_height=dst_ellipsoidal_height,
        dst_area_or_point=dst_area_or_point
    )

    out_file = out_path / file_name

    with rasterio.open(out_file, "w", **profile) as dst:
        dst.write(X, 1)
        dst.update_tags(AREA_OR_POINT=dst_area_or_point)

    # Only plot if explicitly requested
    if show_plot:
        print(f"Plotting DEM: {out_file}")
        fig, ax = plt.subplots(figsize=(6, 6))
        plot.show(X, transform=profile["transform"], ax=ax)
        ax.set_title(f"{dem_name.upper()} crop: {side_km} km square")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        plt.show()

    print(f"Saved DEM to: {out_file.resolve()}")
    return str(out_file.resolve())
