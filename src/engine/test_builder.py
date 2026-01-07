from pathlib import Path

from src.loaders.master_orders_loader import MasterOrdersLoader
from src.loaders.location_master_loader import LocationMasterLoader
from src.loaders.marketplace_mapping import MarketplaceMappingLoader
from src.engine.goswift_engine_builder import GoSwiftBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]

master_loader = MasterOrdersLoader(
    PROJECT_ROOT / "data" / "master_orders" / "master.xlsx"
)
location_loader = LocationMasterLoader(
    PROJECT_ROOT / "data" / "location_master" / "location_master.xlsx"
)
mapping_loader = MarketplaceMappingLoader(
    PROJECT_ROOT / "data" / "marketplace_mapping" / "marketplace_mapping.xlsx"
)

master_loader.load()
location_loader.load()
mapping_loader.load()

builder = GoSwiftBuilder(
    master_loader,
    location_loader,
    mapping_loader
)


row = builder.build_row("FBSWN07404651")

print("\n--- GoSwift Row ---")
for k, v in row.items():
    print(f"{k:30} : {v}")
