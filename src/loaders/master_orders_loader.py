# =====================================================
# MASTER ORDERS LOADER
# =====================================================

import pandas as pd
from pathlib import Path
from src.loaders.base_loader import BaseLoader

REQUIRED_COLS = [
    "marketplaces",
    "po",
    "location",
    "invoice_value",
    "weight",
    "courier_name",
    'box',
    'invoice_number',
    "ewb",
    "exp_date"
]
import pandas as pd
from pathlib import Path
from src.loaders.base_loader import BaseLoader

class MasterOrdersLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.orders_df = None
        self.is_loaded = False
    
    def load(self) -> pd.DataFrame:
        """
        Load master orders from Excel file.
        Returns empty DataFrame if file doesn't exist.
        """
        # ✅ Check if file exists - if not, return empty DataFrame
        if not self.file_path.exists():
            print(f"⚠️  Master file not found: {self.file_path}")
            self.orders_df = pd.DataFrame(columns=["order_number"] + REQUIRED_COLS)
            self.is_loaded = False
            return self.orders_df
        
        try:
            loader = BaseLoader(self.file_path, sheet_name="OnlineB2B")
            df = loader.load()
            df = df[REQUIRED_COLS]
            
            df = df.rename(columns={
                "po": "order_number",
                "invoice_value": "invoice_value",
                "weight": "weight_kg",
            })

            # Clean invoice values
            df["invoice_value"] = (
                df["invoice_value"]
                .astype(str)
                .str.replace("₹", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            # Convert to numeric (handles invalid values gracefully)
            df["invoice_value"] = pd.to_numeric(
                df["invoice_value"].str.split(".").str[0],
                errors="coerce"
            )
            df["invoice_value"] = df["invoice_value"].fillna(0).astype(int)
            
            # Convert weight to grams
            df['weight_kg'] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)
            df["total_weight_gms"] = (df["weight_kg"] * 1000).astype(int)
            
            # Data type conversions
            df["order_number"] = df["order_number"].astype(str)
            df['invoice_number'] = df['invoice_number'].astype(str)
            
            # Handle EWB
            if df['ewb'].isnull().any():
                df['ewb'] = df['ewb'].fillna('')
            else:
                df['ewb'] = df['ewb'].astype(str)
            
            # Parse expiry date
            df["exp_date"] = pd.to_datetime(df["exp_date"], errors="coerce")
            
            # ✅ Set index for fast lookup
            df = df.set_index("order_number", drop=False)
            
            self.orders_df = df
            self.is_loaded = True
            print(f"✅ Loaded {len(df)} orders from master")
            return df
            
        except Exception as e:
            print(f"❌ Error loading master orders: {str(e)}")
            self.orders_df = pd.DataFrame(columns=["order_number"] + REQUIRED_COLS)
            self.is_loaded = False
            return self.orders_df
    
    def exists(self, order_number: str) -> bool:
        """Check if order exists in loaded data"""
        if self.orders_df is None or len(self.orders_df) == 0:
            return False
        return order_number in self.orders_df.index
    
    def get_order(self, order_number: str) -> dict:
        """Get order as dictionary"""
        if not self.exists(order_number):
            raise KeyError(f"Order number {order_number} not found in master")
        
        # .loc[order_number] gets the row, .to_dict() converts it to dictionary
        return self.orders_df.loc[order_number].to_dict()