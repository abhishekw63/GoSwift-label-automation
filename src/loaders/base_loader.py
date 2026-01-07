import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

PROJECT_ROOT = Path(__file__).resolve().parents[2] #what does this parents do and why [2]?


USE_COLS = [
    "Marketplaces",
    "PO",
    "Location",
    "Invoice Number",
    "Invoice Value",
    "Weight",
    "Courier Name",
    "Box"
]


class BaseLoader:
    def __init__(self, file_path: Path, sheet_name: [str] = None):  #file_path: Path what does this mean?
        self.file_path = file_path
        self.sheet_name = sheet_name

        
    def load(self) -> pd.DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found at {self.file_path}")

        
        if self.file_path.suffix.lower() in [".xlsx", ".xls"]:
            
            if self.sheet_name:
                print(f"-> Loading sheet: {self.sheet_name}")
                log_1 = datetime.now()
                df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
                log_2 = datetime.now()
                print(f"-> Time taken to load sheet {self.sheet_name}: {log_2 - log_1}")
                print(f"-> Loaded {len(df)} rows from {self.sheet_name}")
                print("=" * 40 + "\n")
                
            else:
                df = pd.read_excel(self.file_path)
        elif self.file_path.suffix.lower() == ".csv":
            df = pd.read_csv(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")

        df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]
        df.columns = self.__normalize_columns(df.columns)

        return df

    
    @staticmethod #why static method?
    def __normalize_columns(columns):
        return (
            pd.Index(columns).str.strip().str.lower().str.replace(" ","_").str.replace("/","_")
        ) #what oes this return do?


if __name__ == "__main__":
    file_path = PROJECT_ROOT / "data" / "tester_data" / "sample_data.xlsx"
    loader = BaseLoader(file_path)
    df = loader.load()
    print(df.columns.tolist())
    
    