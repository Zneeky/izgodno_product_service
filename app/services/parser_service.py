import json
import re
from slugify import slugify
from app.models.category import Category
from app.models.product_variation import ProductVariation
from app.schemas.product import ParsedProductResponse, ParsedProductWithVariationResponse, ProductBaseModel, ProductPriceOut
from app.services.interfaces.crawling_service_interface import ICrawlingService
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
    def __init__(self, repo: ProductRepository, llm_service: ILLMService, crawling_service: ICrawlingService):
        self.repo = repo
        self.llm_service = llm_service
        self.crawling_service = crawling_service

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
        brand = fields.get("brand")
        model = fields.get("model")
        category_path = fields.get("category")

        # Step 3: Check for existing product
        candidates = await self.repo.get_by_brand_and_model(fields["brand"], fields["model"])
        if candidates:
            print(f"🧩 Found {len(candidates)} candidate products")

            # For now, take the first candidate (you can later implement better disambiguation)
            product = candidates[0]

            # Get variations for the matched product
            variations = await self.repo.get_variations_by_product_id(product.id)

            # Use LLM or attribute comparison to match variation
            matched_variation = await self.match_variation(fields, variations)

            if matched_variation:
                print("✅ Matched existing variation")
                return ParsedProductWithVariationResponse(
                    product_id = product.id,
                    variation_id = matched_variation.id,
                    brand = brand,
                    model = model,
                    sku = matched_variation.sku,
                    variation = matched_variation.variation_key,
                    category_name = product.category.name if product.category else None,
                    category_id = product.category.id
                )

            print("➕ Product found, but variation was not recongised.")

        # Step 4: Product doesn't exist — create product and variation
        print("📦 Product does not exist. Let's create it")

        variations = await self.llm_service.get_variations_from_web(brand, model)
        category = await self.get_or_create_category(category_path)

        # Create the base Product
        new_product = await self.repo.create_product(
            brand = brand,
            model = model,
            category_id = category.id,
            category_name = category.name
        )

         # Create each variation in the DB
        created_variations = []
        for var in variations:
            variation = await self.repo.create_variation(
                product_id = new_product.id,
                variation_name = var["name"],
                variation_key = var["variation"].lower(),
                sku=slugify(var["name"], lowercase=True)
            )
            created_variations.append(variation)

        print(f"✅ Created {len(created_variations)} variations for product")
        for v in created_variations:
            print(f"  - Variation: {v.variation_name} (SKU: {v.sku})")
        
        return ParsedProductWithVariationResponse(
            product_id = new_product.id,
            variation_id = created_variations[0].id,
            brand = new_product.brand,
            model = new_product.model,
            variation = created_variations[0].variation_key,
            category_name = category.name if category else None,
            category_id = category.id
        )

    async def parse_product_and_find_best_offer(self, product_data: ParsedProductWithVariationResponse):
        offer_results_db = await self.repo.get_recent_prices_for_variation(product_data.variation_id)
        if offer_results_db:
            print(f"🗃️ Found {len(offer_results_db)} recent offers in DB for variation {product_data.variation_id}")
            return [ProductPriceOut.model_validate(offer) for offer in offer_results_db]
        
        brand = product_data.brand
        model = product_data.model
        variation = product_data.variation
        category_id = product_data.category_id
        query = f"{brand} {model} {variation}"

        # Step 1: Call crawling service to get data from different websites
        search_results = await self.read_sample_data_from_file("productOffers.json") # await self.crawling_service.crawl_all_search_pages(category_id, query)
        
        matching_results = []
        domain_grouped_data = {}

        for result in search_results:
            domain = result.get('domain')
            products = result.get('extracted_data', [])

            for product in products:
                item = product.get('item')
                item_page_url = product.get('item_page_url')
                price = product.get('item_current_price')
                price_currency = product.get('price_currency')
                image_url = product.get('item_image_url')

                # Step 3: Extract and compare product info
                match_found = self.extract_and_compare_words(
                    brand=brand,
                    model=model,
                    variation=variation,
                    item=item,
                    item_page_url=item_page_url,
                    item_image_url=image_url
                )

                if match_found:
                    product_entry = {
                        "item": item,
                        "item_current_price": price,
                        "item_image_url": image_url,
                        "item_page_url": item_page_url,
                        "price_currency": price_currency
                    }

                    # Group under the domain
                    if domain not in domain_grouped_data:
                        domain_grouped_data[domain] = []

                    print(product_entry)
                    domain_grouped_data[domain].append(product_entry)

        # Step 4: Convert grouped data to List[DomainData] format
        matching_results = [
            {
                "domain": domain,
                "extracted_data": products
            }
            for domain, products in domain_grouped_data.items()
        ]

        original_product = {
            "brand": brand,
            "model": model,
            "variation": variation
        }

        best_offers = await self.llm_service.choose_best_offer_per_domain(
            original_product = original_product,
            offers = matching_results
        )

        await self.repo.save_best_offers_to_db(best_offers, product_data.variation_id)
        return best_offers

    async def match_variation(self, fields: dict, variations: list[ProductVariation]) -> ProductVariation | None:
        brand = fields.get("brand", "").lower().strip()
        model = fields.get("model", "").lower().strip()
        expected_full = f"{brand} {model}"

        # Step 1: Direct matching (specs or SKU)
        for v in variations:
            name = (v.variation_name or "").lower().strip()
            if name == expected_full:
                print("✅ Exact variation_name match:", v.variation_name)
                return v
        
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
                    "variation_name": v.variation_name,
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
                        category_name=matched_category.name if matched_category else None
                    )

        return None
    

    def normalize_text(self, text: str) -> str:
        """
        Normalize the text by removing special characters, converting to lowercase,
        and splitting into words. Returns an empty list if text is None.
        """
        if not text:
            return []

        # Remove any special characters or punctuation that might interfere with matching
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # Convert the text to lowercase
        text = text.lower()

        # Split the text into individual words
        return text.split()

    def normalize_url(self, url: str) -> list[str]:
        """
        Normalize URL by splitting on slashes, dashes, and underscores.
        Returns a list of cleaned, lowercase tokens.
        """
        # Remove protocol (e.g., https://)
        url = re.sub(r'^https?://', '', url)
        
        # Replace slashes, dashes, and underscores with spaces
        url = re.sub(r'[\/\-_]', ' ', url)
        
        # Remove non-alphanumeric characters (except spaces)
        url = re.sub(r'[^a-zA-Z0-9\s]', '', url)
        
        # Convert to lowercase and split into tokens
        return url.lower().split()
    
    def extract_and_compare_words(self, brand: str, model: str, variation: str, item: str, item_page_url: str, item_image_url: str = None) -> bool:
        """
        Extract and compare the words in the product name (item) and URL (item_page_url) to check for the presence of
        the brand, model, and variation.
        """
        # Combine and normalize
        reference_text = f"{brand} {model} {variation}"
        normalized_reference = self.normalize_text(reference_text)  # ['apple', 'iphone', '16', 'pro', '128gb']
        # Normalize both the item (product name) and item_page_url (URL)
        normalized_item = self.normalize_text(item)
        normalized_item_url = self.normalize_url(item_page_url)
        normalized_item_image_url = self.normalize_url(item_image_url or "")  # safe fallback for None

        combined_tokens = set(normalized_item + normalized_item_url + normalized_item_image_url)
        # Check if every token from reference appears in either the item or URL
        for token in normalized_reference:
            if token not in combined_tokens:
                print(f"❌ Token '{token}' not found in item or URLs")
                print(f"  - Tokens: {combined_tokens}")
                return False

        return True
    
    async def read_sample_data_from_file(self, file_path: str):
        """
        Reads sample data from a file (e.g., JSON) for testing purposes.
        Returns a JSON formatted response with processed data.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        final_result = []

        for result in data.get("results", []):
            domain = result.get("domain")
            if not isinstance(domain, str):
                print(f"⚠️ Skipping invalid domain: {domain}")
                continue

            extracted_data = []
            for product in result.get("extracted_data", []):
                item = product.get("item")
                item_current_price = product.get("item_current_price")
                item_page_url = product.get("item_page_url")
                item_image_url = product.get("item_image_url", "N/A")

                # Skip if any of the required fields are missing or empty
                if not all([item, item_current_price, item_page_url]):
                    continue

                extracted_data.append({
                    "item": item,
                    "item_current_price": item_current_price,
                    "item_image_url": item_image_url,
                    "item_page_url": item_page_url,
                    "price_currency": product.get("price_currency", "N/A")
                })

            # Only add domain entry if it has at least one valid product
            if extracted_data:
                final_result.append({
                    "domain": domain,
                    "extracted_data": extracted_data
                })

        return final_result
