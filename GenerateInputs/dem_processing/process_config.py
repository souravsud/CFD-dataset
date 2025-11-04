# config.py
import os
import csv

class ProcessConfig:
    def __init__(self, csv_path=None, row_index=0, verbose=True, debug=True):
        """
        Initialize config with CSV data
        
        Args:
            csv_path: Path to CSV file with lat/lon data
            row_index: Which row from CSV to use (0-based)
            verbose: Whether to print debug info
        """
        self.verbose = verbose 
        # Load center coordinates from CSV if provided
        if csv_path:
            self.center_lat, self.center_lon = self._load_coordinates_from_csv(csv_path, row_index, verbose)     
            self.tower_locations = None
            self.tower_names = None
        else:
            # Default fallback values
            self.center_lat = 39.71121111
            self.center_lon = -7.73483333
            # Tower info
            self.tower_locations = [
                                    (39.70596389, -7.74371389),
                                    (39.71121111, -7.73483333),
                                    (39.71360278, -7.73038333)
                                    ]
            self.tower_names = ["Tower_1", "Tower_2", "Tower_3"]
            # Processing parameters
            self.rotation_deg = 45
            self.final_crop_km = 31
        
        # File paths - these will be set relative to the project root
        self.input_file = None  # Will be set by master script
        self.output_folder_final = None  # Will be set by master script
        
        # Debug flags
        self.debug_mode = debug
    
    def _load_coordinates_from_csv(self, csv_path, row_index, verbose):
        """Load lat/lon from CSV file - uses your existing logic"""
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
            print(f"Processing {len(rows)} rows...")

        # Check if row_index is valid
        if row_index >= len(rows):
            raise ValueError(f"Row index {row_index} is out of range. CSV has {len(rows)} rows.")
        
        # Get the specified row
        row = rows[row_index]
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
            
            if verbose:
                print(f"Loaded coordinates from row {row_index}: lat={lat}, lon={lon}")
            
            return lat, lon
        
        except ValueError as e:
            raise ValueError(f"Invalid lat/lon values in row {row_index}: {e}")
    
    def set_paths(self, input_file, output_folder):
        """Set file paths - called by master script"""
        self.input_file = input_file
        self.output_folder_final = output_folder
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
