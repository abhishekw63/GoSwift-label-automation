# =====================================================
# LOCATION MASTER LOADER
# =====================================================

LOCATION_COLS = [
    "marketplace",
    "location",
    "customer_name",
    "address",
    "pincode",
    "city",
    "state",
]

import pandas as pd
from pathlib import Path
from src.loaders.base_loader import BaseLoader

class LocationMasterLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.location_df = None
        self.is_loaded = False
        
    def load(self) -> pd.DataFrame:
        """
        Load location master from Excel file.
        Returns empty DataFrame if file doesn't exist.
        """
        # ✅ Check if file exists
        if not self.file_path.exists():
            print(f"⚠️  Location master file not found: {self.file_path}")
            self.location_df = pd.DataFrame(columns=LOCATION_COLS)
            self.is_loaded = False
            return self.location_df
        
        try:
            loader = BaseLoader(self.file_path, sheet_name="Raw Data")
            df = loader.load()
            df = df[LOCATION_COLS]
            
            df = df.rename(columns={
                "customer_name": "customer_name",
                "address": "customer_address",
                "pincode": "customer_pincode",
                "city": "customer_city",
                "state": "customer_state",
                "marketplace": "marketplace",
                "location": "location",
            })
            
            df['customer_pincode'] = (
                pd.to_numeric(df['customer_pincode'], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
            )
            
            # ✅ Set index for fast lookup by location
            df = df.set_index("location", drop=False)
            
            self.location_df = df
            self.is_loaded = True
            print(f"✅ Loaded {len(df)} locations")
            return df
            
        except Exception as e:
            print(f"❌ Error loading location master: {str(e)}")
            self.location_df = pd.DataFrame(columns=LOCATION_COLS)
            self.is_loaded = False
            return self.location_df
        
    def exists(self, location: str) -> bool:
        """Check if location exists in loaded data"""
        if self.location_df is None or len(self.location_df) == 0:
            return False
        return location in self.location_df.index
    
    def get_location(self, location: str) -> dict:
        """Get location as dictionary"""
        if not self.exists(location):
            raise KeyError(f"Location {location} not found in location master")
        return self.location_df.loc[location].to_dict()