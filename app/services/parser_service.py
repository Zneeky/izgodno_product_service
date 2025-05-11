from app.models.category import Category
from app.schemas.product import ParsedProductResponse, ProductBaseModel
from app.services.interfaces.parser_service_interface import IParserService
from app.services.interfaces.llm_service_interface import ILLMService
from app.crud.product_repository import ProductRepository
from app.services.utils import generate_sku
from deep_translator import GoogleTranslator
from rapidfuzz import process, fuzz

from uuid import UUID

NEW_CATEGORY_PARENT_ID = UUID("cf8384df-f073-477f-b2fb-e5643eeb974e")

class ParserService(IParserService):
    def __init__(self, repo: ProductRepository, llm_service: ILLMService):
        self.repo = repo
        self.llm_service = llm_service

    def translate_to_english(self, text: str) -> str:
        return GoogleTranslator(source='bg', target='en').translate(text)
    
    async def find_best_category_match(self, llm_category: str) -> Category | None:
        llm_category = llm_category.lower().strip()  # 🔽 normalize input

        # Step 1: Get all categories from DB
        all_categories = await self.repo.get_all_categories()

        # Step 2: Build full paths (e.g., "Electronics > Phones > Smartphones")
        def build_path(cat: Category) -> str:
            path = [cat.name]
            current = cat.parent
            while current:
                path.insert(0, current.name.lower())
                current = current.parent
            return " > ".join(path)

        path_map = {build_path(cat): cat for cat in all_categories}
        name_map = {cat.name.lower(): cat for cat in all_categories}

        # Step 3: Fuzzy match against both sets
        best_path_match = process.extractOne(llm_category, path_map.keys(), scorer=fuzz.token_sort_ratio)
        best_name_match = process.extractOne(llm_category, name_map.keys(), scorer=fuzz.token_sort_ratio)

        # Step 4: Choose the higher score
        best_path, path_score = best_path_match[0], best_path_match[1] if best_path_match else ("", 0)
        best_name, name_score = best_name_match[0], best_name_match[1] if best_name_match else ("", 0)

        print(f"🔍 Path match: '{best_path}' ({path_score}) | Name match: '{best_name}' ({name_score})")

        # Step 5: Return best if above threshold
        if name_score >= 85:
            return name_map[best_name]
        elif path_score > 70:
            return path_map[best_path]
            
        return None
    
    async def get_or_create_category(self, category_path: str) -> Category:
        # Step 1: Try matching
        matched = await self.find_best_category_match(category_path)
        if matched:
            return matched

        print(f"⚠️ No good match for '{category_path}', creating new category...")

        levels = [level.strip() for level in category_path.split(">")]
        parent = await self.repo.get_category_by_id(NEW_CATEGORY_PARENT_ID)

        for level in levels:
            existing = await self.repo.get_category_by_name(level, parent_id=parent.id if parent else None)
            if existing:
                parent = existing
            else:
                parent = await self.repo.create_category(name=level, parent_id=parent.id if parent else None)

        return parent

    def is_similar_attributes(self, attrs1: dict, attrs2: dict, threshold: float = 0.95) -> bool:
        print(f"🔍 Comparing attribute values:\n→ {attrs1}\n→ {attrs2}")

        if not attrs1 or not attrs2:
            return False

        values1 = set(str(v).lower() for v in attrs1.values())
        values2 = set(str(v).lower() for v in attrs2.values())

        common_values = values1.intersection(values2)
        total_values = len(values1.union(values2))

        print(f"🔍 Value match: {len(common_values)}/{total_values} common")
        return (len(common_values) / total_values) >= threshold
    

    async def handle_product_parsing(self, name: str) -> ParsedProductResponse:
        # Step 1: Translate entry
        translated_title = self.translate_to_english(name)
        print("🌍 Translated Title:", translated_title)

        # Step 2: Extract product fields using LLM
        fields = await self.llm_service.extract_product_fields(translated_title)
        print("🔍 LLM Raw Output:", fields)

        # Step 3: Generate SKU
        sku = str(generate_sku(fields.get("brand"), fields.get("model"), fields.get("attributes", {})))
        print("🔑 Generated SKU:", sku)

        # Step 4: Check for existing product
        candidates = await self.repo.get_by_brand_and_model(fields["brand"], fields["model"])
        for existing in candidates:
            if self.is_similar_attributes(existing.attributes, {k.lower(): v for k, v in fields.get("attributes", {}).items()}):
                matched_category = await self.repo.get_category_by_id(existing.category_id) if existing.category_id else None
                return ParsedProductResponse(
                    id=existing.id,
                    brand=existing.brand,
                    model=existing.model,
                    sku=existing.sku,
                    attributes=existing.attributes,
                    category_name=matched_category.name
                )

        # Step 5: Find best category match
        matched_category = await self.get_or_create_category(fields.get("category"))
        print("🏷️ Matched Category:", matched_category.name if matched_category else "None")
        
        parsed_product = ProductBaseModel(
            name = f"{fields.get('brand')} {fields.get('model')}",
            brand = fields.get("brand"),
            model = fields.get("model"),
            attributes = {k.lower(): v for k, v in fields.get("attributes", {}).items()},
            category_id = matched_category.id if matched_category else None,  # required!
            sku = sku,
        )

        # Step 6: Save new product if it doesn't exist
        created = await self.repo.create(parsed_product, matched_category.id, matched_category.name)
        return created