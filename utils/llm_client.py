import requests
from openai import OpenAI

class SimpleLLMClient:
    def __init__(self):
        self.openai_key = ""
        self.gemini_key = ""
    
    def setup_keys(self, openai_key, gemini_key):
        self.openai_key = openai_key
        self.gemini_key = gemini_key
    
    def generate_response(self, model, context, temperature=0.1):
        """Generate response using selected model"""
        if model == "Gemini 2.0 Flash" and self.gemini_key:
            return self._generate_gemini(context, temperature)
        elif "GPT" in model and self.openai_key:
            return self._generate_openai(context, model, temperature)
        else:
            return "⚠️ Please configure API keys to use AI models."
    
    def _generate_gemini(self, context, temperature):
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.gemini_key
            }
            
            prompt = f"""You are a GTI SOP Assistant. Answer based ONLY on the provided documentation.

CONTEXT:
{context}

Provide a clear, specific answer based only on the information above. If the information is not in the context, say so clearly."""
            
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return f"Error: {response.status_code} - {response.text}"
            
        except Exception as e:
            return f"Error calling Gemini: {str(e)}"
    
    def _generate_openai(self, context, model, temperature):
        try:
            client = OpenAI(api_key=self.openai_key)
            
            model_map = {
                "GPT-4": "gpt-4",
                "GPT-4 Mini": "gpt-4o-mini"
            }
            
            response = client.chat.completions.create(
                model=model_map.get(model, "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a GTI SOP Assistant. Answer based ONLY on provided documentation."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=1000,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"