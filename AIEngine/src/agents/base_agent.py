from typing import Dict, Tuple
import requests
import json

class Agent:
    def __init__(self, name: str, api_token: str):
        self.name = name
        self.api_token = api_token
        self.api_url = "https://api.unify.ai/v0/chat/completions"
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def get_completion(self, messages, system_prompt=None) -> str:
        try:
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            json_input = {
                "messages": messages,
                "model": "gpt-4o-mini@openai",
                "max_tokens": 1024,
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(self.api_url, json=json_input, headers=self.headers)
            response.raise_for_status()
            
            try:
                response_json = response.json()
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON response: {e}")
                print(f"Raw response: {response.text}")
                return "I apologize, but I'm having trouble processing the response. Could you please try again?"
            
            if 'choices' not in response_json:
                print(f"Unexpected response structure: {response_json}")
                return "I apologize, but I received an unexpected response. Could you please try again?"
            
            if not response_json['choices'] or 'message' not in response_json['choices'][0]:
                print(f"No valid choices in response: {response_json}")
                return "I apologize, but I didn't receive a valid response. Could you please try again?"
            
            return response_json['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return "I apologize, but I'm having trouble connecting to the service. Could you please try again later?"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "I apologize, but something went wrong. Could you please try again?"
    
    def get_structured_completion(self, messages, system_prompt=None, output_format=None) -> Dict:
        try:
            if system_prompt:
                if output_format:
                    system_prompt += f"\n\nRespond with a JSON object in the following format: {output_format}"
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            json_input = {
                "messages": messages,
                "model": "gpt-4o-mini@openai",
                "max_tokens": 1024,
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(self.api_url, json=json_input, headers=self.headers)
            response.raise_for_status()
            
            try:
                response_json = response.json()
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON response: {e}")
                return {"error": "Failed to decode response"}
            
            if 'choices' not in response_json or not response_json['choices']:
                return {"error": "No choices in response"}
            
            content = response_json['choices'][0]['message']['content']
            
            # Try to extract JSON from the content
            try:
                # Find JSON object in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > 0:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
                else:
                    print("No JSON object found in response.")
                    return {"response": content}
            except json.JSONDecodeError:
                print("Failed to parse JSON from response")
                return {"response": content}
        except Exception as e:
            print(f"Error in get_structured_completion: {e}")
            return {"error": str(e)}
