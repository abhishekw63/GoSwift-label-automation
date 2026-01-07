import pandas as pd
from pathlib import Path
from src.loaders.base_loader import BaseLoader

REQUIRED_COLS = [
    "marketplace",
    "location",
    "customer_name",
    "address",
    "pincode",
    "city",
    "state",
]

class LocationMasterLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.location_df = None
        
    def load(self) -> pd.DataFrame:
        loader = BaseLoader(self.file_path, sheet_name="Raw Data")
        df = loader.load()
        df = df[REQUIRED_COLS]
        
        df = df.rename(columns={
            "customer_name": "customer_name",
            "address": "customer_address",
            "pincode": "customer_pincode",
            "city": "customer_city",
            "state": "customer_state",
            "marketplace": "marketplace",
            "location": "location",
        })
        
        df['customer_pincode'] = pd.to_numeric(df['customer_pincode'], errors="coerce").fillna(0).astype(int).astype(str)
        
        df = df.set_index("location", drop = False) #what does this do?
        
        self.location_df: pd.DataFrame = df
        return df
        
    
    def exists(self, location: str) -> bool:
        return location in self.location_df.index
    
    def get_location(self, location: str) -> dict:
        if not self.exists(location):
            raise KeyError(f"Location {location} not found in location master")
        return self.location_df.loc[location].to_dict()
    
    
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root /  "data" / "tester_data" / "location_master.xlsx"
    loader = LocationMasterLoader(file_path) 
    df = loader.load()
    
    print(f"Total locations loaded: {len(df)}")
    print(loader.get_location("NOI IM1"))