from groq import Groq
import httpx
import json
import re
from app.services.interfaces.llm_service_interface import ILLMService
from app.core.config import settings
from app.services.llm_logger import log_llm_decision

class LLMService(ILLMService):
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        #self.model = model model: str = "mistral"

    async def extract_product_fields(self, title: str) -> dict:
        
        prompt = f"""
        You are a product data extraction assistant.

        Your job is to analyze product titles and extract their structured attributes in valid JSON format.

        Your output must include:

        1. **"brand"** – Brand/manufacturer.
        2. **"model"** – Model name
        3. **"category"** – General category like Smartphone, Mobile Phone, Laptop, Monitor, Lotion, Headphone etc. Make sure to use the most common category name.
        4. **"attributes"** – Extract every detail 


        Here is the product title:
        "{title}"

        Return ONLY a valid JSON object:
        {{
        "brand": "...",
        "model": "...", 
        "category": "...",
        "attributes": {{ 
        }}
        }}

        Avoid explanations. 
        Only return the JSON. Do not add any other text or comments. Use only english.
        """

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        content = completion.choices[0].message.content.strip()
        print("🔍 LLM Raw Output:", content)
        return self.extract_json_from_response(content)

    def extract_json_from_response(self, text: str) -> dict:
        import json, re
        try:
            # Extract the JSON block
            json_text = re.search(r'\{.*\}', text, re.DOTALL).group()

            # Fix trailing commas (common LLM issue)
            json_text = re.sub(r',\s*([}\]])', r'\1', json_text)

            return json.loads(json_text)
        except Exception as e:
            print("❌ JSON parsing failed:", text)
            raise ValueError("❌ Could not extract valid JSON.") from e
        
    
    async def llm_match_products(self, new_product: dict, existing_products: list[dict]) -> dict:
        """
        Compares a new product to existing ones and returns a dict indicating match status and matched ID.
        """
        comparison_prompt = f"""
        You are an intelligent product comparison agent.

        You will be given a new product and a list of existing products in the database that share the same brand and model.

        Your job is to decide, for each existing product, whether the new product is effectively the same product.

        Return a valid JSON array of match decisions. Each object must have:
        - `"match"` (true/false)
        - `"matched_id"` (UUID of the existing product)

        Here is the new product:
        {json.dumps(new_product, indent=2)}

        Here are the existing products:
        {json.dumps(existing_products, indent=2)}

        Only return the JSON. No comments. No explanation.
        """

        # using specific model for comparison
        completion = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": comparison_prompt
            }]
        )

        content = completion.choices[0].message.content.strip()
        print("🤖 LLM Match Check Output:", content)
        llm_result = self.extract_json_structued_list(content)
        log_llm_decision(new_product, existing_products, llm_result)
        return llm_result
    
    def extract_json_structued_list(self, text: str) -> dict | list:
        try:
            # 🧹 Strip triple backticks (``` ... ```)
            cleaned = re.sub(r"^```[\s\n]*|[\s\n]*```$", "", text.strip())

            # 🧪 Parse as JSON
            parsed = json.loads(cleaned)

            # ✅ Ensure it's a list of dicts
            if isinstance(parsed, dict):
                return [parsed]  # Single object wrapped in list
            elif isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                return parsed
            else:
                raise ValueError("Expected a list of JSON objects.")
        
        except Exception as e:
            print("❌ Failed to extract valid JSON array:\n", text)
            raise ValueError("❌ Could not extract valid JSON array.") from e