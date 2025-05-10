from groq import Groq
import httpx
import json
import re
from app.services.interfaces.llm_service_interface import ILLMService
from app.core.config import settings

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