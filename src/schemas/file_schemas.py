MASTER_SCHEMA = {
    "sheet": "OnlineB2B",
    "columns": {
        "marketplaces",
        "po",
        "location",
        "invoice_value",
        "weight",
        "courier_name",
        "box"
    }
}

LOCATION_SCHEMA = {
    "sheet": "Raw Data",
    "columns": {
        "marketplace",
        "location",
        "customer_name",
        "address",
        "pincode",
        "city",
        "state"
    }
}

MARKETPLACE_SCHEMA = {
    "sheet": 0,   # first sheet
    "columns": {
        "marketplace",
        "transporter",
        "go_swift_code"
    }
}
