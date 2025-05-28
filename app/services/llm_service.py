from groq import Groq
import httpx
import json
import re

from openai import OpenAI
from regex import match
from app.services.interfaces.llm_service_interface import ILLMService
from app.core.config import settings
from app.services.llm_logger import log_llm_decision

class LLMService(ILLMService):
    def __init__(self):
        self.groq = Groq(api_key=settings.GROQ_API_KEY)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.groq_model = settings.GROQ_MODEL
        self.openai_model = settings.OPENAI_MODEL
        #self.model = model model: str = "mistral"

    async def extract_product_fields(self, title: str) -> dict:
        
        prompt = f"""
        You are a product data extraction assistant.

        Your job is to analyze product titles and extract their structured attributes in valid JSON format.

        Your output must include:

        1. **"brand"** – Brand/manufacturer.
        2. **"model"** – Model name
        3. **"category"** – General category like Smartphone, Mobile Phone, Laptop, Monitor, Lotion, Headphones etc.
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

        completion = self.groq.chat.completions.create(
            model=self.groq_model,
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
        response = self.groq.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": comparison_prompt
            }]
        )

        content = response.choices[0].message.content.strip()
        print("🤖 LLM Match Check Output:", content)
        llm_result = self.extract_json_structued_list(content)
        log_llm_decision(new_product, existing_products, llm_result)
        return llm_result
    
    def extract_json_structued_list(self, text: str) -> dict | list:
        try:
            # 🧹 Strip triple backticks (``` ... ```)
            cleaned = re.search(r"\[.*\]", text.strip(), re.DOTALL)
            cleaned = cleaned.group(0) if cleaned else text.strip()
            cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
            print("🧹 Cleaned JSON text:", cleaned)

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
    
        
    async def get_variations_from_web(self, brand: str, model: str) -> list[dict]:
        """
         Uses OpenAI GPT-4o with web browsing to discover real product variations online.
        """

        prompt = f"""
        You are a product research assistant with access to the web.

        Your task is to **find all real-world variations** of the following product:  
        → **{brand} {model}**

        A **variation** is a specific version of the same product that differs in an attribute that significantly affects its price or performance (e.g., storage size, RAM, processor, screen size, included accessories). Do **not** treat color, minor design tweaks, or packaging as separate variations unless they directly impact the product’s value.
        Use your reasoning to determine the **smallest set of meaningful variations**. Only return distinct configurations where a buyer would pay a significantlly different price.

        Sources to consult:
        - Official product pages (search for "{brand}")
        - Retailers like Emag.bg, Ozone.bg, Amazon.com, BestBuy, Target, Walmart, Notino, Sephora, etc.
        - Product comparison/review sites 

        Return a JSON array of objects, each representing a variation, keep the variation amount as low as possible
        - objects with two keys:
        • `"name"`: The title of the variation, including brand
        • `"variation"`:  the specific differentiating part that distinguishes this variation from the others
        [
            {{
                "name": "...",
                "variation": "..."
            }},
        ...
        ]

        Return **only** the JSON. No explanations, just pure JSON. Respond in English.
        """

        response = self.openai.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            tools=[
                {
                    "type": "web_search_preview",
                    "user_location": {
                        "type": "approximate",
                        "country": "BG",
                        "city": "Sofia"
                    },
                    "search_context_size": "medium"
                }
            ],
            temperature=0.1
        )

        content = response.output_text
        print("🌐 GPT-4o Discovered Variations:\n", content)

        return self.extract_json_structued_list(content)