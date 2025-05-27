from app.models.category import Category
from app.models.product_variation import ProductVariation
from app.schemas.product import ParsedProductResponse, ParsedProductWithVariationResponse, ProductBaseModel
from app.services.interfaces.parser_service_interface import IParserService
from app.services.interfaces.llm_service_interface import ILLMService
from app.crud.product_repository import ProductRepository
from app.services.utils import generate_sku
from deep_translator import GoogleTranslator
from rapidfuzz import process, fuzz
from rapidfuzz.fuzz import partial_ratio

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

    def is_similar_attributes(self, attrs1: dict, attrs2: dict, threshold: float = 0.98) -> bool:
        print(f"🔍 Comparing attribute values:\n→ {attrs1}\n→ {attrs2}")

        if not attrs1 or not attrs2:
            return False

        values1 = set(str(v).lower() for v in attrs1.values())
        values2 = set(str(v).lower() for v in attrs2.values())

        common_values = values1.intersection(values2)
        total_values = len(values1.union(values2))

        print(f"🔍 Value match: {len(common_values)}/{total_values} common")
        return (len(common_values) / total_values) >= threshold
    

    async def handle_product_parsing(self, name: str) -> ParsedProductWithVariationResponse:
        # Step 1: Translate entry
        translated_title = self.translate_to_english(name)
        print("🌍 Translated Title:", translated_title)

        # Step 2: Extract product fields using LLM
        fields = await self.llm_service.extract_product_fields(translated_title)
        print("🔍 LLM Raw Output:", fields)
        brand = fields.get("brand")
        model = fields.get("model")
        raw_attributes = fields.get("attributes", {})
        attributes = {k.lower(): v for k, v in raw_attributes.items()}
        category_path = fields.get("category")
        sku = generate_sku(brand, model, attributes)

        # Step 3: Check for existing product
        candidates = await self.repo.get_by_brand_and_model(fields["brand"], fields["model"])
        if candidates:
            print(f"🧩 Found {len(candidates)} candidate products")

            # For now, take the first candidate (you can later implement better disambiguation)
            product = candidates[0]

            # Step 1: Get variations for the matched product
            variations = await self.repo.get_variations_by_product_id(product.id)

            # Step 2: Use LLM or attribute comparison to match variation
            matched_variation = await self.match_variation(fields, variations)

            if matched_variation:
                print("✅ Matched existing variation")
                return ParsedProductWithVariationResponse(
                    product_id=product.id,
                    variation_id=matched_variation.id,
                    brand=brand,
                    model=model,
                    sku=matched_variation.sku,
                    attributes=matched_variation.specs,
                    category_name=product.category.name if product.category else None
                )

            print("➕ Product found, but variation was not recongised.")

        # Step 4: Product doesn't exist — create product and variation
        print("📦 Product does not exist. Let's create it")

        variations = await self.llm_service.get_variations_from_web(brand, model)
        category = await self.get_or_create_category(category_path)


        return ParsedProductWithVariationResponse(
            product_id="11111111-1111-1111-1111-111111111111",
            variation_id= "44444444-4444-4444-4444-444444444444",
            brand= "Apple",
            model= "iPhone 16 Pro",
            attributes= {"storage": "512GB"},
            category_name= "Smartphones"
        )

    

    async def match_variation(self, fields: dict, variations: list[ProductVariation]) -> ProductVariation | None:
        input_specs = {k.lower(): v for k, v in fields.get("attributes", {}).items()}
        input_sku = generate_sku(fields["brand"], fields["model"], input_specs)

        # Step 1: Direct matching (specs or SKU)
        for variation in variations:
            if self.is_similar_attributes(variation.specs, input_specs) or self.is_similar_sku(variation.sku, input_sku):
                print("✅ Found variation via attribute or SKU similarity")
                return variation

        # Step 2: LLM fallback
        llm_result = await self.match_with_llm_candidates_variations(fields, variations)
        if llm_result:
            print("✅ Found variation via LLM")
            # Convert ParsedProductResponse back to ProductVariation reference
            return next((v for v in variations if str(v.id) == str(llm_result.id)), None)

        print("❌ No matching variation found")
        return None

    def is_similar_sku(self, sku1: str, sku2: str, threshold: float = 98.0) -> bool:
        if not sku1 or not sku2:
            return False
        score = partial_ratio(sku1.lower(), sku2.lower())
        print(f"🔍 SKU similarity: {sku1} vs {sku2} → {score}%")
        return score >= threshold

    async def match_with_llm_candidates_variations(self, fields: dict, candidates: list[ProductVariation]) -> ParsedProductResponse | None:
        if not candidates:
            print("⚠️ No variation candidates available for LLM matching.")
            return None

        input_attrs = {k.lower(): v for k, v in fields.get("attributes", {}).items()}

        llm_result = await self.llm_service.llm_match_products(
            new_product={
                "brand": fields.get("brand"),
                "model": fields.get("model"),
                "attributes": input_attrs,
            },
            existing_products=[
                {
                    "id": str(v.id),
                    "brand": v.product.brand,
                    "model": v.product.model,
                    "attributes": v.specs,
                } for v in candidates
            ]
        )

        for match in llm_result:
            if match.get("match") is True:
                matched_id = match.get("matched_id")
                matched_variation = next((v for v in candidates if str(v.id) == matched_id), None)
                if matched_variation:
                    product = matched_variation.product
                    matched_category = await self.repo.get_category_by_id(product.category_id) if product.category_id else None
                    return ParsedProductResponse(
                        id=matched_variation.id,
                        brand=product.brand,
                        model=product.model,
                        sku=matched_variation.sku,
                        attributes=matched_variation.specs,
                        category_name=matched_category.name if matched_category else None
                    )

        return None