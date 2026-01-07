import pandas as pd
from pathlib import Path


def validate_excel(file_path: Path, sheet_name: str, required_columns: set):
    try:
        xls = pd.ExcelFile(file_path)
        
        if isinstance(sheet_name, str) and sheet_name not in xls.sheet_names:
            return False, f"Required sheet '{sheet_name}' not found in the Excel file.\n Available sheets: {xls.sheet_names}"
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("/", "_")
        )
        
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        return True, None
    
    except Exception as e:
        return False, f"Excel validation failed due to error: {e}"
    