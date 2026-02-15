# GenerateInput/dem_downloader.py
import math
from pathlib import Path
import rasterio
from rasterio import plot
from rasterio.merge import merge
import matplotlib.pyplot as plt
from dem_stitcher.stitcher import stitch_dem
import requests
import tempfile
import geopandas as gpd
from shapely.geometry import Polygon
import windkit as wk
import numpy as np
import os

from .reproject_raster import save_utm_metadata, reproject_raster_to_utm, get_utm_crs

R = 6_371_000.0  # Earth's mean radius in meters

class DEMDownloader:
    """Handles DEM downloading with configurable options"""
    
    def __init__(self, config):
        self.config = config
    
    def log(self, message):
        """Conditional logging"""
        if self.config.verbose:
            print(message)
    
    def download_single_location(self, lat, lon, index, out_dir):
        """Download DEM for a single coordinate pair"""
        self.log(f"Downloading DEM for lat={lat}, lon={lon}")
        
        return download_square_data(
            index=index,
            center_lon=lon,
            center_lat=lat,
            side_km=self.config.side_length_km,
            include_roughness_map=self.config.include_roughness_map,
            dem_name=self.config.dem_name,
            dst_ellipsoidal_height=self.config.dst_ellipsoidal_height,
            dst_area_or_point=self.config.dst_area_or_point,
            out_dir=out_dir,
            verbose=self.config.verbose,
            show_plot=self.config.show_plots,
            save_raw=self.config.save_raw_files
        )

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

def create_output_dir(lat: float, lon: float, index: int, root_folder: str) -> str:
    #Save folder for each location
    lat_str = format_coord(lat, is_lat=True, precision=3)
    lon_str = format_coord(lon, is_lat=False, precision=3)
    folder_name = f"terrain_{(index+1):04d}_{lat_str}_{lon_str}"
    download_path = os.path.join(root_folder, folder_name)
    
    if os.path.exists(download_path):
        return None
    else:
        os.makedirs(download_path)
        return download_path

def latlon_offset(lat: float, lon: float, dy_m: float, dx_m: float) -> tuple[float, float]:
    """Move a point northwards by dy_m meters and eastwards by dx_m meters."""
    dlat_rad = dy_m / R
    dlon_rad = dx_m / (R * math.cos(math.radians(lat)))

    new_lat = lat + math.degrees(dlat_rad)
    new_lon = lon + math.degrees(dlon_rad)
    return new_lat, new_lon

def stitch_tiles(tiles, version, year, bounds):
    tmp = tempfile.TemporaryDirectory()
    paths = []
    for tile in tiles:
        url = (
            f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
            f"{version}/{year}/map/ESA_WorldCover_10m_{year}_{version}_{tile}_Map.tif"
        )
        r = requests.get(url)
        if r.status_code == 200:
            p = Path(tmp.name) / f"{tile}.tif"
            p.write_bytes(r.content)
            paths.append(str(p))
    if not paths:
        raise ValueError("No WorldCover tiles downloaded")
    ds = [rasterio.open(p) for p in paths]
    mosaic, transform = merge(ds)
    prof = ds[0].profile.copy()
    prof.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform)
    for d in ds: d.close()

    # crop
    with rasterio.open(tmp.name + "/mosaic.tif", "w", **prof) as dst:
        dst.write(mosaic)
    with rasterio.open(tmp.name + "/mosaic.tif") as src:
        win = rasterio.windows.from_bounds(*bounds, src.transform)
        data = src.read(1, window=win)
        tf = src.window_transform(win)
        prof.update(height=data.shape[0], width=data.shape[1], transform=tf)
    return data, prof

def _calculate_bounds(side_km, center_lat,center_lon):
    
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

    return bounds, corners

def _generate_filename(index,center_lat, center_lon,out_dir,side_km, source, prefix):
    
    out_path = Path(out_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    lat_str = format_coord(center_lat, is_lat=True, precision=3)
    lon_str = format_coord(center_lon, is_lat=False, precision=3)
    side_str = f"{side_km:.0f}km" if side_km % 1 == 0 else f"{side_km:.1f}km"
    file_name = f"{prefix}_{(index+1):04d}_{source}_{lat_str}_{lon_str}_{side_str}.tif"
    
    out_file = out_path / file_name
    
    return out_file
        
def _plot_map(data, profile, side_km, plot_name,out_dir):
    
    print(f"Plotting {plot_name} map")
    fig, ax = plt.subplots(figsize=(6, 6))
    if plot_name == "Terrain":
        cmap= "viridis"
    elif plot_name == "Roughness":
        cmap = "tab20"
    plot.show(data, transform=profile["transform"], ax=ax, cmap=cmap)
    ax.set_title(f"{plot_name} {side_km}km square")
    ax.set_xlabel("Eastings (m)")
    ax.set_ylabel("Northings (m)")
    
    out_dir = Path(out_dir)
    filename = f"{plot_name.lower().replace(' ', '_')}_map.png" # Optional: Replace spaces with underscores
    filepath = out_dir / filename
    plt.savefig(filepath)
    
def download_square_data(
        index: int,
        center_lon: float,
        center_lat: float,
        side_km: float,
        include_roughness_map: bool = False,
        dem_name: str = "glo_30",
        dst_ellipsoidal_height: bool = True,
        dst_area_or_point: str = "Point",
        out_dir: str = "out",
        verbose: bool = False,
        show_plot: bool = False,
        save_raw: bool = False,
    ) -> tuple[str, str | None]:

    bounds, corners = _calculate_bounds(side_km, center_lat, center_lon)
    
    if verbose: 
        print(f"Bounds (lat/lon): {bounds}")
    
    # Determine UTM CRS once for both DEM and roughness
    utm_crs = get_utm_crs(center_lon, center_lat)
    
    if verbose:
        print(f"Target UTM CRS: {utm_crs}")
    
    dem_out_file = _generate_filename(index, center_lat, center_lon, out_dir, side_km, dem_name, "terrain")
    
    # ===== DEM PROCESSING =====
    if verbose:
        print("Downloading DEM data...")
    
    data, profile = stitch_dem(
        bounds,
        dem_name=dem_name,
        dst_ellipsoidal_height=dst_ellipsoidal_height,
        dst_area_or_point=dst_area_or_point
    )
    
    if verbose:
        print(f"Original DEM CRS: {profile['crs']}")
    
    # NEW: Save raw file if requested
    if save_raw:
        raw_dem_file = dem_out_file.parent / f"{dem_out_file.stem}_raw.tif"
        with rasterio.open(raw_dem_file, "w", **profile) as dst:
            dst.write(data, 1)
            dst.update_tags(AREA_OR_POINT=dst_area_or_point)
        print(f"Saved raw DEM (EPSG:4326) to: {raw_dem_file.resolve()}")
    
    # Reproject to UTM
    data_utm, profile_utm = reproject_raster_to_utm(data, profile, utm_crs, verbose)
    
    # Save UTM version
    with rasterio.open(dem_out_file, "w", **profile_utm) as dst:
        dst.write(data_utm, 1)
        dst.update_tags(AREA_OR_POINT=dst_area_or_point)
    
    print(f"Saved terrain elevation map (UTM) to: {dem_out_file.resolve()}")
    
    # Save metadata
    save_utm_metadata(dem_name, dem_out_file, center_lat, center_lon, profile_utm)
    
    if show_plot:
        _plot_map(data_utm, profile_utm, side_km, "Terrain", out_dir)
    
    # ===== ROUGHNESS MAP PROCESSING =====
    if include_roughness_map:
        rmap_out_file = _generate_filename(index, center_lat, center_lon, out_dir, side_km, "worldcover", "roughness")
        
        if verbose:
            print("Downloading roughness map data...")
        
        # Load grid and select tiles
        grid_url = (
            "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
            "v100/2020/esa_worldcover_2020_grid.geojson"
        )
        grid = gpd.read_file(grid_url)
        aoi = Polygon([(lon, lat) for lat, lon in corners])
        tiles = grid[grid.intersects(aoi)].ll_tile.tolist()
        
        if verbose: 
            print(f"Tiles to download: {tiles}")
        
        version = "v100"
        year = 2020
        
        # Download & stitch
        data_lc, profile_lc = stitch_tiles(tiles, version, year, bounds)
        
        land_cover_table = "GWA4"
        lct = wk.get_landcover_table(land_cover_table)
        
        source = grid_url+ "," + version + "," + str(year) + ","+ land_cover_table
        if verbose: 
            print("Converting WorldCover classes to aerodynamic roughness length (z0)...")
        
        lc_code_to_z0 = {
            lc_id: params.get('z0') 
            for lc_id, params in lct.items() 
            if params is not None and 'z0' in params
        }
        z0_data = np.vectorize(lc_code_to_z0.get)(data_lc)
        
        # Update profile for float data
        profile_lc.update(dtype=rasterio.float32, count=1)
        
        # NEW: Save raw roughness file if requested
        if save_raw:
            raw_rmap_file = rmap_out_file.parent / f"{rmap_out_file.stem}_raw.tif"
            with rasterio.open(raw_rmap_file, "w", **profile_lc) as dst:
                dst.write(z0_data.astype(np.float32), 1)
            print(f"Saved raw roughness map (EPSG:4326) to: {raw_rmap_file.resolve()}")
        
        # Reproject roughness map to UTM (same CRS as DEM)
        z0_data_utm, profile_z0_utm = reproject_raster_to_utm(
            z0_data.astype(np.float32), 
            profile_lc, 
            utm_crs, 
            verbose
        )
        
        # Save UTM version
        with rasterio.open(rmap_out_file, "w", **profile_z0_utm) as dst:
            dst.write(z0_data_utm, 1)
        
        print(f"Saved roughness map (UTM) to: {rmap_out_file.resolve()}")
        
        # Save metadata for roughness map
        save_utm_metadata(source, rmap_out_file, center_lat, center_lon, profile_z0_utm)
        
        if show_plot:
            _plot_map(z0_data_utm, profile_z0_utm, side_km, "Roughness", out_dir)
    
    return str(dem_out_file.resolve()), str(rmap_out_file.resolve()) if include_roughness_map else None
    

if __name__ == "__main__":
    

    file = download_square_data(index=0,
                                center_lon=-7.73483333,        # sample longitude
                                center_lat=39.71121111,      # sample latitude
                                side_km=50,
                                include_roughness_map= True,
                                out_dir = "out",
                                verbose= False,
                                show_plot = True,
                            )
