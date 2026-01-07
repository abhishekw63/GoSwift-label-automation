import pandas as pd
from pathlib import Path
from src.loaders.base_loader import BaseLoader


class MarketplaceMappingLoader:
    REQUIRED_COLS = [
        "marketplace",
        "transporter",
        "go_swift_code"
    ]

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.mapping_df = None
        
    def load(self) -> pd.DataFrame:
        loader = BaseLoader(self.file_path)
        df = loader.load()
   
        df = df[self.REQUIRED_COLS]
        
        df["marketplace"] = df["marketplace"].astype(str).str.strip()
        df["transporter"] = df["transporter"].astype(str).str.strip()
        df["go_swift_code"] = df["go_swift_code"].fillna("").astype(str).str.strip()
                
        df = df.set_index("marketplace", drop=False)
        
        self.mapping_df = df
        return df
    
    def exists(self, marketplace: str) -> bool:
        return marketplace in self.mapping_df.index

    def get_mapping(self, marketplace: str) -> dict:
        if not self.exists(marketplace):
            raise KeyError(f"Marketplace {marketplace} not found in mapping")
        return self.mapping_df.loc[marketplace].to_dict()
    
    
    
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / "data" / "tester_data" / "marketplace_mapping.xlsx"
    loader = MarketplaceMappingLoader(file_path)
    df = loader.load()

    print(f"total marketplace mapping loaded;{len(df)}")
    print(loader.get_mapping("Blinkit"))
