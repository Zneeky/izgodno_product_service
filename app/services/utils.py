import re
def generate_sku(brand: str, model: str) -> str:
    def normalize(text: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

    brand_part = normalize(brand)
    model_part = normalize(model)
    return f"{brand_part}-{model_part}"