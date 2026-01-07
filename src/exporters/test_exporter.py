from pathlib import Path

from src.loaders.master_orders_loader import MasterOrdersLoader
from src.loaders.location_master_loader import LocationMasterLoader
from src.loaders.marketplace_mapping import MarketplaceMappingLoader
from src.engine.goswift_engine_builder import GoSwiftBuilder
from src.exporters.goswift_csv_exporter import GoSwiftCSVExporter

PROJECT_ROOT = Path(__file__).resolve().parents[2]

master_orders = MasterOrdersLoader(
    PROJECT_ROOT / "data" / "master_orders" / "master.xlsx"
)
master_orders.load()

location_master = LocationMasterLoader(
    PROJECT_ROOT / "data" / "location_master" / "location_master.xlsx"
)
location_master.load()

marketplace_mapping = MarketplaceMappingLoader(
    PROJECT_ROOT / "data" / "marketplace_mapping" / "marketplace_mapping.xlsx"
)
marketplace_mapping.load()

builder = GoSwiftBuilder(
    master_orders=master_orders,
    location_master=location_master,
    marketplace_mapping=marketplace_mapping
)


exporter =GoSwiftCSVExporter(
    builder=builder,
    output_dir=PROJECT_ROOT / "output"
)

orders = [
    "FBSWN07404651",
    "FBPWN07373172",
    "CPDPO219563"
]

exporter.export(orders)