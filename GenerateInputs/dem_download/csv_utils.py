# csv_utils.py
import csv

def load_coordinates_from_csv(csv_path, verbose=False):
    """
    Load all coordinates from CSV file
    Returns list of (lat, lon) tuples
    """
    try:
        with open(csv_path, newline="") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            rows = list(reader)

    except FileNotFoundError:
        print(f"Error: The file at {csv_path} was not found.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

    # Debug output
    if verbose:
        print(f"CSV '{csv_path}' opened successfully.")
        print(f"Detected {len(header)} columns: {header}")
        print(f"Detected {len(rows)} data rows (excluding header).")

    # Sanity check
    required = {"lat", "lon"}
    missing = required - set(header)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    
    if verbose:
        print(f"All required columns present: {required}")
        print(f"Loading {len(rows)} coordinate pairs...")

    # Convert all rows to coordinates
    coordinates = []
    for idx, row in enumerate(rows):
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
            coordinates.append((lat, lon))
            
            if verbose:
                print(f"Row {idx}: lat={lat}, lon={lon}")
                
        except ValueError as e:
            print(f"Warning: Skipping row {idx} due to invalid lat/lon: {e}")
            continue
    
    return coordinates

def get_coordinate_by_index(csv_path, index, verbose=False):
    """Get a specific coordinate pair by index"""
    coordinates = load_coordinates_from_csv(csv_path, verbose)
    
    if index >= len(coordinates):
        raise ValueError(f"Index {index} is out of range. CSV has {len(coordinates)} valid coordinate pairs.")
    
    return coordinates[index]
