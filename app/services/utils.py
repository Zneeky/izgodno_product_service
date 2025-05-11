import re
from typing import Any
from slugify import slugify


def generate_sku(brand: str, model: str, attributes: dict[str, Any]) -> str:
    def normalize(text: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

    brand_part = normalize(brand)
    model_part = normalize(model)

    attr_values_part = "-".join(
        normalize(str(v)) for _, v in sorted(attributes.items())
    )

    return slugify(f"{brand_part} {model_part} {attr_values_part}")