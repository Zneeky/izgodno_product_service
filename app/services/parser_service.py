def parse_product_name(name: str) -> dict:
    # Dummy example of parsing logic — expand later
    result = {
        "brand": "Samsung" if "Samsung" in name else None,
        "model": "S21" if "S21" in name else None,
        "storage": "128GB" if "128" in name else None,
        "color": "Black" if "Black" in name else None,
        "serial_number": None
    }
    return result
