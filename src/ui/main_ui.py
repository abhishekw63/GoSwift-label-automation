import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import shutil, json
from pathlib import Path
import socket
import os
import sys
import threading

from src.loaders.master_orders_loader import MasterOrdersLoader
from src.loaders.location_master_loader import LocationMasterLoader
from src.loaders.marketplace_mapping import MarketplaceMappingLoader
from src.engine.goswift_engine_builder import GoSwiftBuilder
from src.exporters.goswift_csv_exporter import GoSwiftCSVExporter

from src.schemas.file_schemas import (MARKETPLACE_SCHEMA, LOCATION_SCHEMA, MASTER_SCHEMA)
from src.utils import excel_validator


# =====================================================
# CONSTANTS & COLORS
# =====================================================
PRIMARY_COLOR = "#667eea"
SECONDARY_COLOR = "#764ba2"
SUCCESS_COLOR = "#28a745"
ERROR_COLOR = "#dc3545"
WARNING_COLOR = "#ffc107"
LIGHT_BG = "#f8f9fa"
CARD_BG = "#ffffff"
TEXT_COLOR = "#333333"
LIGHT_TEXT = "#666666"
GRADIENT_START = "#667eea"
GRADIENT_END = "#764ba2"

# =====================================================
# SPLASH SCREEN
# =====================================================

class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Loading...")
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Remove window decorations
        self.attributes('-topmost', True)
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 150
        self.geometry(f"+{x}+{y}")
        
        # Background
        bg_frame = tk.Frame(self, bg=PRIMARY_COLOR)
        bg_frame.pack(fill="both", expand=True)
        
        # Logo/Title
        title = tk.Label(
            bg_frame,
            text="🚀",
            font=("Helvetica", 60),
            bg=PRIMARY_COLOR,
            fg="white"
        )
        title.pack(pady=20)
        
        # App name
        app_name = tk.Label(
            bg_frame,
            text="GoSwift Label Automation",
            font=("Helvetica", 18, "bold"),
            bg=PRIMARY_COLOR,
            fg="white"
        )
        app_name.pack()
        
        # Loading text
        self.status_label = tk.Label(
            bg_frame,
            text="Loading data...",
            font=("Helvetica", 11),
            bg=PRIMARY_COLOR,
            fg="white",
            pady=10
        )
        self.status_label.pack()
        
        # Progress bar (simple animation)
        progress_frame = tk.Frame(bg_frame, bg="white", height=4)
        progress_frame.pack(fill="x", padx=40, pady=20)
        
        self.progress = tk.Frame(progress_frame, bg=SECONDARY_COLOR, height=4)
        self.progress.pack(side="left", fill="x", expand=True)
        
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.update()
    
    def close(self):
        self.destroy()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def internet_check(timeout=3) -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


def check_expiry_date(config_file="config/config.json") -> tuple:
    """Check if the expiry date from config has passed today"""
    try:
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / config_file
        
        if not config_path.exists():
            return True, "No expiry configured"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        expiry_date_str = config.get("expiry_date")
        if not expiry_date_str:
            return True, "No expiry configured"
        
        try:
            expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, f"Invalid date format in config: {expiry_date_str}"
        
        today = datetime.date.today()
        
        if expiry_date < today:
            days_expired = (today - expiry_date).days
            return False, f"❌ License Expired {days_expired} days ago (on {expiry_date})"
        elif expiry_date == today:
            return False, f"❌ License expires TODAY ({expiry_date}) - Please renew!"
        else:
            days_remaining = (expiry_date - today).days
            return True, f"✅ Valid until {expiry_date} ({days_remaining} days remaining)"
    
    except json.JSONDecodeError:
        return False, "Error reading config file"
    except Exception as e:
        return False, f"Error checking expiry: {str(e)}"


# =====================================================
# CUSTOM WIDGETS
# =====================================================

class ModernButton(tk.Button):
    """Modern button with shadow and hover effects"""
    def __init__(self, parent, text="", command=None, color=PRIMARY_COLOR, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=self._lighten_color(color),
            activeforeground="white",
            bd=0,
            highlightthickness=0,
            **kwargs
        )
        self.color = color
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=self._lighten_color(self.color))
    
    def _on_leave(self, event):
        self.config(bg=self.color)
    
    @staticmethod
    def _lighten_color(color):
        """Lighten a hex color for hover effect"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = min(255, int(r * 1.15))
        g = min(255, int(g * 1.15))
        b = min(255, int(b * 1.15))
        return f"#{r:02x}{g:02x}{b:02x}"


class StatusCard(tk.Frame):
    """Modern status card with icon support"""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg=CARD_BG, relief=tk.FLAT, **kwargs)
        self.config(
            highlightbackground="#e8eef7",
            highlightthickness=2,
            bd=0
        )
        
        # Title
        title_label = tk.Label(
            self,
            text=title,
            font=("Helvetica", 10, "bold"),
            bg=CARD_BG,
            fg=TEXT_COLOR
        )
        title_label.pack(anchor="w", padx=12, pady=(10, 5))
        
        # Status label
        self.status_label = tk.Label(
            self,
            text="Loading...",
            font=("Helvetica", 9),
            bg=CARD_BG,
            fg=LIGHT_TEXT,
            wraplength=250
        )
        self.status_label.pack(anchor="w", padx=12, pady=(0, 10))
    
    def set_status(self, text, color):
        self.status_label.config(text=text, fg=color)


class GradientFrame(tk.Frame):
    """Frame with gradient background"""
    def __init__(self, parent, color1=GRADIENT_START, color2=GRADIENT_END, **kwargs):
        super().__init__(parent, **kwargs)
        self.color1 = color1
        self.color2 = color2
        
        self.bind("<Configure>", self._draw_gradient)
    
    def _draw_gradient(self, event):
        width = event.width
        height = event.height
        
        limit = width
        (r1, g1, b1) = int(self.color1[1:3], 16), int(self.color1[3:5], 16), int(self.color1[5:7], 16)
        (r2, g2, b2) = int(self.color2[1:3], 16), int(self.color2[3:5], 16), int(self.color2[5:7], 16)
        
        for i in range(limit):
            ratio = i / limit
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            tk.Frame(self, bg=color, height=height, width=1).place(x=i, y=0)


# =====================================================
# MAIN UI CLASS
# =====================================================

class GoSwiftUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GoSwift Label Automation")
        self.root.geometry("700x750")
        self.root.resizable(True, True)
        self.root.minsize(700, 650)
        self.root.config(bg=LIGHT_BG)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 350
        y = (self.root.winfo_screenheight() // 2) - 375
        self.root.geometry(f"+{x}+{y}")
        
        self.project_root = Path(__file__).resolve().parents[2]
        self.splash = None
        
        # Check expiry date BEFORE building UI
        expiry_valid, expiry_msg = check_expiry_date()
        if not expiry_valid:
            messagebox.showerror(
                "License Expired",
                f"{expiry_msg}\n\nThe application cannot run.",
                parent=self.root
            )
            self.root.destroy()
            return
        
        self._build_ui()
        self._load_engine_async()
    
    # ============ ENGINE ============
    def _load_engine_async(self):
        """Load engine in background with splash screen"""
        self.splash = SplashScreen(self.root)
        
        def load():
            try:
                self.splash.update_status("📊 Loading Master Orders...")
                self.master_orders = MasterOrdersLoader(
                    self.project_root / "data" / "master_orders" / "master.xlsx"
                )
                self.master_orders.load()
                meta = self._read_meta("master_orders", "master_meta.json")
                
                self.splash.update_status("📍 Loading Location Master...")
                self.location_master = LocationMasterLoader(
                    self.project_root / "data" / "location_master" / "location_master.xlsx"
                )
                self.location_master.load()
                meta = self._read_meta("location_master", "location_master_meta.json")
                
                self.splash.update_status("🛍️ Loading Marketplace Mapping...")
                self.marketplace_mapping = MarketplaceMappingLoader(
                    self.project_root / "data" / "marketplace_mapping" / "marketplace_mapping.xlsx"
                )
                self.marketplace_mapping.load()
                
                self.splash.update_status("⚙️ Initializing engine...")
                self.builder = GoSwiftBuilder(
                    self.master_orders,
                    self.location_master,
                    self.marketplace_mapping
                )

                self.exporter = GoSwiftCSVExporter(
                    self.builder,
                    self.project_root / "output"
                )
                
                self.root.after(0, self._on_engine_loaded)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Startup Error", str(e)))
                self.root.after(0, self.root.destroy)
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _on_engine_loaded(self):
        """Called when engine finishes loading"""
        self.splash.close()
        self._update_ui_status()
        self.expiry_label.config(text="✅ Ready", fg=SUCCESS_COLOR)
    
    def _update_ui_status(self):
        """Update status cards after loading"""
        # Master Orders
        meta = self._read_meta("master_orders", "master_meta.json")
        if meta:
            self.master_card.set_status(f"✅ {meta}", SUCCESS_COLOR)
        elif self.master_orders.is_loaded:
            self.master_card.set_status("✅ Data loaded", SUCCESS_COLOR)
        else:
            self.master_card.set_status("⚠️ No data - Please upload", WARNING_COLOR)

        # Location Master
        meta = self._read_meta("location_master", "location_master_meta.json")
        if meta:
            self.location_card.set_status(f"✅ {meta}", SUCCESS_COLOR)
        elif self.location_master.is_loaded:
            self.location_card.set_status("✅ Data loaded", SUCCESS_COLOR)
        else:
            self.location_card.set_status("⚠️ No data - Please upload", WARNING_COLOR)

        # Marketplace Mapping
        meta = self._read_meta("marketplace_mapping", "marketplace_mapping_meta.json")
        if meta:
            self.marketplace_card.set_status(f"✅ {meta}", SUCCESS_COLOR)
        elif self.marketplace_mapping.is_loaded:
            self.marketplace_card.set_status("✅ Data loaded", SUCCESS_COLOR)
        else:
            self.marketplace_card.set_status("⚠️ No data - Please upload", WARNING_COLOR)

    def _read_meta(self, folder, filename):
        path = self.project_root / "data" / folder / filename
        if path.exists():
            with open(path) as f:
                data = json.load(f).get("last_updated", "")
                return data.split(" ")[0] if data else ""
        return None

    # ============ UI ============
    def _build_ui(self):
        # ===== HEADER (Gradient) =====
        header = GradientFrame(
            self.root,
            color1=PRIMARY_COLOR,
            color2=SECONDARY_COLOR,
            height=80
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="🚀 GoSwift Label Automation",
            font=("Helvetica", 18, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            padx=20
        )
        title.pack(pady=15)
        
        # ===== STATUS BAR =====
        status_bar = tk.Frame(self.root, bg=LIGHT_BG, height=35)
        status_bar.pack(fill="x", padx=15, pady=10)
        status_bar.pack_propagate(False)
        
        self.internet_status = tk.Label(
            status_bar,
            text="🔍 Checking...",
            font=("Helvetica", 9),
            bg=LIGHT_BG,
            fg="blue"
        )
        self.internet_status.pack(side="left")
        self._update_internet_status()
        
        self.expiry_label = tk.Label(
            status_bar,
            text="Loading license...",
            font=("Helvetica", 9),
            bg=LIGHT_BG,
            fg="blue"
        )
        self.expiry_label.pack(side="right")
        
        # ===== SCROLLABLE MAIN CONTENT =====
        canvas = tk.Canvas(self.root, bg=LIGHT_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=LIGHT_BG)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=12, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ===== INPUT SECTION =====
        input_label = tk.Label(
            scrollable_frame,
            text="📋 Order Numbers (one per line)",
            font=("Helvetica", 11, "bold"),
            bg=LIGHT_BG,
            fg=TEXT_COLOR
        )
        input_label.pack(anchor="w", pady=(0, 8))
        
        input_frame = tk.Frame(scrollable_frame, bg=CARD_BG, relief=tk.FLAT)
        input_frame.pack(fill="both", padx=0, pady=(0, 12))
        input_frame.config(highlightbackground="#e8eef7", highlightthickness=2)
        
        self.text_input = scrolledtext.ScrolledText(
            input_frame,
            height=7,
            font=("Courier", 10),
            bg="white",
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            padx=12,
            pady=12,
            insertbackground=PRIMARY_COLOR
        )
        self.text_input.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Generate button
        ModernButton(
            scrollable_frame,
            text="✨ Generate GoSwift CSV",
            command=self._generate_csv,
            color=SECONDARY_COLOR
        ).pack(pady=12, fill="x", padx=0)
        
        # ===== DATA SOURCES SECTION =====
        sources_label = tk.Label(
            scrollable_frame,
            text="📁 Data Sources",
            font=("Helvetica", 11, "bold"),
            bg=LIGHT_BG,
            fg=TEXT_COLOR
        )
        sources_label.pack(anchor="w", pady=(15, 8))
        
        # Master Orders
        self.master_card = StatusCard(scrollable_frame, "📊 Master Orders")
        self.master_card.pack(fill="x", pady=5, padx=0)
        ModernButton(
            scrollable_frame,
            text="Upload Master Orders",
            command=self._upload_master,
            color=PRIMARY_COLOR
        ).pack(pady=3, fill="x", padx=0)
        
        # Location Master
        self.location_card = StatusCard(scrollable_frame, "📍 Location Master")
        self.location_card.pack(fill="x", pady=5, padx=0)
        ModernButton(
            scrollable_frame,
            text="Upload Location Master",
            command=self._upload_location_master,
            color=PRIMARY_COLOR
        ).pack(pady=3, fill="x", padx=0)
        
        # Marketplace Mapping
        self.marketplace_card = StatusCard(scrollable_frame, "🛍️ Marketplace Mapping")
        self.marketplace_card.pack(fill="x", pady=5, padx=0)
        ModernButton(
            scrollable_frame,
            text="Upload Marketplace Mapping",
            command=self._upload_marketplace_mapping,
            color=PRIMARY_COLOR
        ).pack(pady=3, fill="x", padx=0)

    # ============ ACTIONS ============
    def _update_internet_status(self):
        if internet_check():
            self.internet_status.config(text="🌐 Online", fg=SUCCESS_COLOR)
        else:
            self.internet_status.config(text="🌐 Offline", fg=ERROR_COLOR)
        
        self.root.after(5000, self._update_internet_status)

    def _generate_csv(self):
        raw = self.text_input.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Input Error", "Enter at least one order number")
            return

        orders = [o.strip() for o in raw.splitlines() if o.strip()]
        try:
            path = self.exporter.export(orders)
            
            response = messagebox.askyesno(
        "✅ CSV Generated",
        f"CSV generated successfully!\n\n{path}\n\nDo you want to open the folder?"
    )
            
            if response:
                self._open_folder(path)
            
            self.text_input.delete("1.0", tk.END)
            
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))
    
    def _open_folder(self, file_path):
            """Open folder containing the file"""
            try:
                folder = Path(file_path).parent
                if os.name == 'nt':
                    os.startfile(folder)
                elif os.name == 'posix':
                    import subprocess
                    subprocess.Popen([
                        'open' if sys.platform == 'darwin' else 'xdg-open',
                        folder
                    ])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def _upload_master(self):
        self._upload_generic(
            "master_orders", "master.xlsx", "master_meta.json", self.master_card
        )

    def _upload_location_master(self):
        self._upload_generic(
            "location_master", "location_master.xlsx", "location_master_meta.json",
            self.location_card
        )

    def _upload_marketplace_mapping(self):
        self._upload_generic(
            "marketplace_mapping", "marketplace_mapping.xlsx",
            "marketplace_mapping_meta.json", self.marketplace_card
        )

    def _upload_generic(self, folder, dest_file, meta_file, card_widget):
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
            messagebox.showerror("❌ Invalid Excel File", error)
            return

        try:
            dest = self.project_root / "data" / folder / dest_file
            shutil.copy(file_path, dest)

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            meta_path = self.project_root / "data" / folder / meta_file
            with open(meta_path, "w") as f:
                json.dump({"last_updated": now}, f)

            card_widget.set_status(f"✅ {now.split(' ')[0]}", SUCCESS_COLOR)
            messagebox.showinfo("✅ Success", f"{folder.replace('_', ' ').title()} updated")

            self._load_engine_async()

        except Exception as e:
            messagebox.showerror("❌ Upload Error", str(e))


def main():
    root = tk.Tk()
    GoSwiftUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()