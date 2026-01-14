# =====================================================
# MARKETPLACE MAPPING LOADER
# =====================================================

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
        self.is_loaded = False
        
    def load(self) -> pd.DataFrame:
        """
        Load marketplace mapping from Excel file.
        Returns empty DataFrame if file doesn't exist.
        """
        # ✅ Check if file exists
        if not self.file_path.exists():
            print(f"⚠️  Marketplace mapping file not found: {self.file_path}")
            self.mapping_df = pd.DataFrame(columns=self.REQUIRED_COLS)
            self.is_loaded = False
            return self.mapping_df
        
        try:
            loader = BaseLoader(self.file_path)
            df = loader.load()
            df = df[self.REQUIRED_COLS]
            
            df["marketplace"] = df["marketplace"].astype(str).str.strip()
            df["transporter"] = df["transporter"].astype(str).str.strip()
            df["go_swift_code"] = df["go_swift_code"].fillna("").astype(str).str.strip()
            
            # ✅ Set index for fast lookup by marketplace
            df = df.set_index("marketplace", drop=False)
            
            self.mapping_df = df
            self.is_loaded = True
            print(f"✅ Loaded {len(df)} marketplace mappings")
            return df
            
        except Exception as e:
            print(f"❌ Error loading marketplace mapping: {str(e)}")
            self.mapping_df = pd.DataFrame(columns=self.REQUIRED_COLS)
            self.is_loaded = False
            return self.mapping_df
    
    def exists(self, marketplace: str) -> bool:
        """Check if marketplace exists in loaded data"""
        if self.mapping_df is None or len(self.mapping_df) == 0:
            return False
        return marketplace in self.mapping_df.index

    def get_mapping(self, marketplace: str) -> dict:
        """Get marketplace mapping as dictionary"""
        if not self.exists(marketplace):
            raise KeyError(f"Marketplace {marketplace} not found in mapping")
        return self.mapping_df.loc[marketplace].to_dict()