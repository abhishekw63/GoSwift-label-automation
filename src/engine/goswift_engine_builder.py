import pandas as pd

# -------------------------------
# GoSwift Output Schema
# -------------------------------
GOSWIFT_COLUMNS = [
    "order_number",
    "customer_ID",
    "customer_company_name",
    "customer_gst_in",
    "customer_name",
    "customer_address",
    "customer_pincode",
    "customer_city",
    "customer_state",
    "customer_number",
    "customer_email",
    "delivery_type",
    "b2b_order_channel",
    "b2b_order_channel_other",
    "total_weight_gms",
    "invoice_number",
    "order_invoice_amount",
    "product_description",
    "ewaybill_number",
    "sender_gst_in",
    "pickup_location_name",
    "box_type",
    "number_of_boxes",
    "l_cms",
    "w_cms",
    "h_cms",
    "seller_courier_choice",
    "service_type",
    "is_rtv_shipment",
    "is_appointment_based",
    "appointment_date",
    "appointment_time (HHMM)",
    "appointment_id",
    "purchase_order_number",
    "purchase_order_expiry_date",
]

# -------------------------------
# Static / Fixed Values
# -------------------------------
STATIC_VALUES = {
    "customer_ID": "",
    "customer_gst_in": "",
    "customer_email": "",
    "delivery_type": "",
    "b2b_order_channel_other": "",
    "sender_gst_in": "",
    "pickup_location_name": "RENEE Cosmetics Pvt. Ltd. B2B",
    "box_type": 1,
    "l_cms": 10,
    "w_cms": 10,
    "h_cms": 10,
    "service_type": "SURFACE",
    "is_rtv_shipment": "FALSE",
    "is_appointment_based": "TRUE",
    "appointment_date": "",
    "appointment_time (HHMM)": "",
    "appointment_id": "",
    "purchase_order_number": "",
    "purchase_order_expiry_date": "",
    "product_description": "Cosmetics",
    "customer_number": "9999999999",
}

# -------------------------------
# Helper
# -------------------------------
def safe(value, default=""):
    """Convert NaN / None to safe value"""
    return default if pd.isna(value) else value

import pandas as pd

from datetime import date
from datetime import datetime


def format_date_for_goswift(d):
    """
    Convert date to DD-MM-YYYY format string for GoSwift
    This is safer than Excel serial numbers for API uploads
    """
    if isinstance(d, date):
        return d.strftime("%d-%m-%Y")
    
    return ""


# -------------------------------
# GoSwift Builder
# -------------------------------
class GoSwiftBuilder:
    def __init__(self, master_orders, location_master, marketplace_mapping):
        self.master_orders = master_orders
        self.location_master = location_master
        self.marketplace_mapping = marketplace_mapping

    def build_row(self, order_number: str) -> dict:
        # 1️⃣ Validate Order
        if not self.master_orders.exists(order_number):
            raise KeyError(f"Order number {order_number} not found in master orders")

        order = self.master_orders.get_order(order_number)

        location = order.get("location")
        marketplace = order.get("marketplaces")

        # 2️⃣ Validate Location & Marketplace
        if not self.location_master.exists(location):
            raise KeyError(f"Location '{location}' not found in location master")

        if not self.marketplace_mapping.exists(marketplace):
            raise KeyError(f"Marketplace '{marketplace}' not found in marketplace mapping")

        loc = self.location_master.get_location(location)
        market = self.marketplace_mapping.get_mapping(marketplace)

        # 3️⃣ Start row with static defaults
        row = dict(STATIC_VALUES)

        raw_box = order.get("box") 
        if pd.isna(raw_box) or raw_box == "":
            raise ValueError(f"Invalid box count for order {order_number}: '{raw_box}'")
        else:
            print(f"Raw box value for order {order_number}: '{raw_box}'")
            row["number_of_boxes"] = int(raw_box)

        raw_exp = order.get('exp_date')
        row['purchase_order_expiry_date'] = format_date_for_goswift(raw_exp)
        
        # 4️⃣ Order-level fields
        row.update({
            "order_number": order_number,
            "invoice_number": safe(order.get("invoice_number")),
            "order_invoice_amount": int(order.get("invoice_value", 0)),
            "total_weight_gms": int(order.get("total_weight_gms", 0)),
            "purchase_order_number": order_number,
        })

        # 5️⃣ Location-based fields
        row.update({
            "customer_company_name": safe(loc.get("customer_name")),
            "customer_name": safe(loc.get("customer_name")),
            "customer_address": safe(loc.get("customer_address")),
            "customer_pincode": safe(loc.get("customer_pincode")),
            "customer_city": safe(loc.get("customer_city")),
            "customer_state": safe(loc.get("customer_state")),
        })

        # 6️⃣ Marketplace-based fields
        row.update({
            "b2b_order_channel": safe(market.get("go_swift_code")),
            "seller_courier_choice": safe(market.get("transporter")),
        })

        # 7️⃣ E-Way Bill logic
        ewb = order.get("ewb", "")
        row["ewaybill_number"] = "" if str(ewb) in ("0", "nan", "") else str(ewb)

        # 8️⃣ Enforce GoSwift column order
        final_row = {col: row.get(col, "") for col in GOSWIFT_COLUMNS}

        return final_row
        
