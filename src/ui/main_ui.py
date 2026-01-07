import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import shutil, json
from pathlib import Path
import socket

from src.loaders.master_orders_loader import MasterOrdersLoader
from src.loaders.location_master_loader import LocationMasterLoader
from src.loaders.marketplace_mapping import MarketplaceMappingLoader
from src.engine.goswift_engine_builder import GoSwiftBuilder
from src.exporters.goswift_csv_exporter import GoSwiftCSVExporter

from src.schemas.file_schemas import (MARKETPLACE_SCHEMA, LOCATION_SCHEMA,MASTER_SCHEMA)
from src.utils import excel_validator


def internet_check(timeout=3) -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


class GoSwiftUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GoSwift Label Automation")
        self.root.geometry("620x730")   # ✅ FIXED
        self.root.resizable(False, False)

        self.project_root = Path(__file__).resolve().parents[2]

        self._build_ui()
        self._load_engine()

    # ---------------- ENGINE ----------------
    def _load_engine(self):
        try:
            self.master_orders = MasterOrdersLoader(
                self.project_root / "data" / "master_orders" / "master.xlsx"
            )
            self.master_orders.load()

            meta = self._read_meta("master_orders", "master_meta.json")
            if meta:
                self.master_status.config(
                    text=f"Master Last Updated: {meta}",
                    fg="green"
                )

            self.location_master = LocationMasterLoader(
                self.project_root / "data" / "location_master" / "location_master.xlsx"
            )
            self.location_master.load()

            meta = self._read_meta("location_master", "location_master_meta.json")
            if meta:
                self.location_master_status.config(
                    text=f"Location Master Last Updated: {meta}",
                    fg="green"
                )

            self.marketplace_mapping = MarketplaceMappingLoader(
                self.project_root / "data" / "marketplace_mapping" / "marketplace_mapping.xlsx"
            )
            self.marketplace_mapping.load()

            meta = self._read_meta("marketplace_mapping", "marketplace_mapping_meta.json")
            if meta:
                self.marketplace_mapping_status.config(
                    text=f"Marketplace Mapping Last Updated: {meta}",
                    fg="green"
                )

            self.builder = GoSwiftBuilder(
                self.master_orders,
                self.location_master,
                self.marketplace_mapping
            )

            self.exporter = GoSwiftCSVExporter(
                self.builder,
                self.project_root / "output"
            )

        except Exception as e:
            messagebox.showerror("Startup Error", str(e))
            self.root.destroy()

    def _read_meta(self, folder, filename):
        path = self.project_root / "data" / folder / filename
        if path.exists():
            with open(path) as f:
                return json.load(f).get("last_updated")
        return None

    # ---------------- UI ----------------
    def _build_ui(self):
        tk.Label(
            self.root,
            text="GoSwift Label Automation",
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)

        self.internet_status = tk.Label(self.root, text="Checking internet...", fg="blue")
        self.internet_status.pack()
        self._update_internet_status()

        frame = tk.LabelFrame(self.root, text="Order Numbers (one per line)")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_input = scrolledtext.ScrolledText(frame, height=12)
        self.text_input.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(
            self.root,
            text="Generate GoSwift CSV",
            font=("Arial", 12),
            command=self._generate_csv
        ).pack(pady=10)

        # ---------- MASTER ----------
        self.master_status = tk.Label(self.root, text="Master Last updated: Not uploaded", fg="grey")
        self.master_status.pack(pady=3)

        tk.Button(
            self.root,
            text="Upload Master Orders",
            command=self._upload_master
        ).pack(pady=3)

        # ---------- LOCATION ----------
        self.location_master_status = tk.Label(
            self.root,
            text="Location Master Last updated: Not uploaded",
            fg="grey"
        )
        self.location_master_status.pack(pady=3)

        tk.Button(
            self.root,
            text="Upload Location Master",
            command=self._upload_location_master
        ).pack(pady=3)

        # ---------- MARKETPLACE ----------
        self.marketplace_mapping_status = tk.Label(
            self.root,
            text="Marketplace Mapping Last updated: Not uploaded",
            fg="grey"
        )
        self.marketplace_mapping_status.pack(pady=3)

        tk.Button(
            self.root,
            text="Upload Marketplace Mapping",
            command=self._upload_marketplace_mapping
        ).pack(pady=3)

    # ---------------- ACTIONS ----------------
    def _update_internet_status(self):
        if internet_check():
            self.internet_status.config(text="Internet: Online", fg="green")
        else:
            self.internet_status.config(text="Internet: Offline", fg="red")

    def _generate_csv(self):
        raw = self.text_input.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Input Error", "Enter at least one order number")
            return

        orders = [o.strip() for o in raw.splitlines() if o.strip()]
        try:
            path = self.exporter.export(orders)
            messagebox.showinfo("Success", f"CSV generated at:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _upload_master(self):
        self._upload_generic(
            "master_orders", "master.xlsx", "master_metadata.json", self.master_status
        )

    def _upload_location_master(self):
        self._upload_generic(
            "location_master", "location_master.xlsx", "location_master_meta.json",
            self.location_master_status
        )

    def _upload_marketplace_mapping(self):
        self._upload_generic(
            "marketplace_mapping", "marketplace_mapping.xlsx",
            "marketplace_mapping_meta.json", self.marketplace_mapping_status
        )

    def _upload_generic(self, folder, dest_file, meta_file, label):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        
        if folder == "master_orders":
            schema = MASTER_SCHEMA
        elif folder == "location_master":
            schema = LOCATION_SCHEMA
        elif folder == "marketplace_mapping":
            schema = MARKETPLACE_SCHEMA
        else:
            messagebox.showerror("Internal Error", "Unknown upload type")
            return
        
        ok, error = excel_validator.validate_excel(
            Path(file_path),
            schema["sheet"],
            schema["columns"]
        )

        if not ok:
            messagebox.showerror("Invalid Excel File", error)
            return   # ⛔ STOP HERE


        try:
            dest = self.project_root / "data" / folder / dest_file
            shutil.copy(file_path, dest)

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            meta_path = self.project_root / "data" / folder / meta_file
            with open(meta_path, "w") as f:
                json.dump({"last_updated": now}, f)

            label.config(text=f"Last Updated: {now}", fg="green")
            messagebox.showinfo("Upload Success", f"{folder.replace('_',' ').title()} updated")

            self._load_engine()

        except Exception as e:
            messagebox.showerror("Upload Error", str(e))


def main():
    root = tk.Tk()
    GoSwiftUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
