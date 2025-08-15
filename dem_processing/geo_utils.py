from pyproj import Transformer
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
import rasterio
import os

def print_debug(message, debug=False):
    if debug:
        print(message)

def get_utm_crs(longitude, latitude):
    """
    Determine the appropriate UTM CRS for given coordinates.
    """
    # Calculate UTM zone
    utm_zone = int((longitude + 180) / 6) + 1
    
    # Determine hemisphere
    if latitude >= 0:
        epsg_code = 32600 + utm_zone  # Northern hemisphere
    else:
        epsg_code = 32700 + utm_zone  # Southern hemisphere
    
    return CRS.from_epsg(epsg_code)

def reproject_to_utm(debug, input_path, output_path=None):
    """
    Reproject a DEM from geographic coordinates to UTM projection.
    """
    with rasterio.open(input_path) as src:
        # Get the center coordinates to determine UTM zone
        bounds = src.bounds
        center_lon = (bounds.left + bounds.right) / 2
        center_lat = (bounds.bottom + bounds.top) / 2
        
        # Get appropriate UTM CRS
        dst_crs = get_utm_crs(center_lon, center_lat)
        
        print_debug(f"Reprojecting to {dst_crs}", debug)
        
        # Calculate transform and new dimensions
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        
        # Define output profile
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        
        if output_path is None:
            # Create temporary file name
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_utm.tif"
        
        # Reproject and save
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear)
        
        print_debug(f"UTM reprojection saved to: {output_path}", debug)
        return output_path, dst_crs
    
def latlon_to_utm(lat, lon, utm_crs):
    """
    Convert lat/lon coordinates to UTM coordinates.
    """
    # Create transformer from WGS84 to UTM
    transformer = Transformer.from_crs(CRS.from_epsg(4326), utm_crs, always_xy=True)
    utm_x, utm_y = transformer.transform(lon, lat)
    return utm_x, utm_y