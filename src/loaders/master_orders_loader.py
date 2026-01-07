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


class MasterOrdersLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.orders_df = None
    
    def load(self) -> pd.DataFrame:
        
        loader = BaseLoader(self.file_path, sheet_name="OnlineB2B")
        df = loader.load()
        df = df[REQUIRED_COLS]
        
        df = df.rename(columns={
            "po": "order_number",
            "invoice_value": "invoice_value",
            "weight": "weight_kg",
        })

        df["invoice_value"] = (
            df["invoice_value"]
            .astype(str)
            .str.replace("₹", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        # Convert invalid / empty values to NaN
        df["invoice_value"] = pd.to_numeric(
            df["invoice_value"].str.split(".").str[0],
            errors="coerce"
        )

        # Fill missing invoice values with 0 (or keep NaN if you prefer)
        df["invoice_value"] = df["invoice_value"].fillna(0).astype(int)
                #what does this line fully do? didnt get it fully
        
        df['weight_kg'] = pd.to_numeric(df["weight_kg"], errors = "coerce").fillna(0)
        df["total_weight_gms"] = (df["weight_kg"] * 1000).astype(int)
        
        df["order_number"] = df["order_number"].astype(str)
        df['invoice_number'] = df['invoice_number'].astype(str)
        
        if df['ewb'].isnull().any():
            df['ewb'] = df['ewb'].fillna('')
        else:
            df['ewb'] = df['ewb'].astype(str)
            
        df["exp_date"] = pd.to_datetime(
                df["exp_date"],
                errors="coerce"
            )

        
        df = df.set_index("order_number", drop=False)

        self.orders_df = df
        return df
    
    def exists(self, order_number: str) -> bool:
        return order_number in self.orders_df.index  #why index here? why we set index in load method?
    
    def get_order(self, order_number: str) -> dict:
        if not self.exists(order_number):
            raise KeyError(f"Order number {order_number} not found in master")
        
        
        return self.orders_df.loc[order_number].to_dict() #what this line do?


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    file_path = PROJECT_ROOT/"data"/ "master_orders" / "master.xlsx"
    
    loader = MasterOrdersLoader(file_path)
    df = loader.load()
    
    print("Total orders loaded:", len(df))
    print(df[:15])
    print(loader.get_order("2883710002790"))