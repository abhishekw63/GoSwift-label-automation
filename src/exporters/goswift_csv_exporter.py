import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List

from src.engine.goswift_engine_builder import (
    GoSwiftBuilder,
    GOSWIFT_COLUMNS
)


class GoSwiftCSVExporter:
    def __init__(self, builder: GoSwiftBuilder, output_dir: Path):
        self.builder = builder
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True) #explain this line
    
    def export(self, order_numbers: List[str]) -> Path:
        rows = []
        failed_orders = []
        for order_number in order_numbers:
            try:
                row = self.builder.build_row(order_number)
                rows.append(row)
            except Exception as e:
                print(f"Failed to process order :{order_number} due to {e}")
            
        if not rows:
            raise RuntimeError("No valid orders found. CSV not generated.")
        
        df = pd.DataFrame(rows)
        
        df = df.reindex(columns=GOSWIFT_COLUMNS) # what does this line do?

        timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        file_path = self.output_dir / f"GoSwift_{timestamp}.csv"
        
        df.to_csv(file_path, index=False) #what does index=False do?
        print(f"\n Go Swift CSV Exported Successfully at {file_path} with {len(rows)} orders\n")
        
        if failed_orders:
            print(f"Failed to process the following orders: {', '.join(failed_orders)}")
        
        return file_path
    