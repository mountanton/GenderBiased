import requests
import json
from google import genai
import os
from anthropic import Anthropic


class LLMs:

# --- Example Usage ---

    def deepseek(self, text: str, model: str, key: str, temperature: int, max_tokens: int) -> str:
        """
        Calls DeepSeek chat completion API
        """
        url = "https://api.deepseek.com/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ],
            # Added temperature and max tokens
            "temperature": temperature,      
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                content = (
                    data["choices"][0]["message"]["content"]
                    .replace("```", "")
                    .replace("sparql", "")
                )
                return content
            else:
                print(f"Error: {response.status_code}")
                try:
                    error_message = response.json()["error"]["message"]
                    return f"Failed: {error_message}"
                except Exception:
                    return f"Failed: {response.text}"

        except Exception as e:
            return f"Failed to fetch answer from DeepSeek: {str(e)}"

    def chatgpt(self, text: str, model: str, key: str, temperature: int, max_tokens: int) -> str:
        """
        Calls OpenAI Chat Completion API (GPT-4o etc.)
        """
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ],
            "temperature": temperature,
            "max_completion_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                content = (
                    data["choices"][0]["message"]["content"]
                    .replace("```", "")
                    .replace("sparql", "")
                )
                return content
            else:
                print(f"Error: {response.status_code}")
                try:
                    error_message = response.json()["error"]["message"]
                    return f"Failed: {error_message}"
                except Exception:
                    return f"Failed: {response.text}"

        except Exception as e:
            return f"Failed to fetch answer from OpenAI: {str(e)}"
        

    def gemini(self, text: str, model: str, key: str, temperature: int, max_tokens: int) -> str:
        """
        Calls Google Gemini API using the genai SDK
        """
        
        # Initialize the client with the provided API key
        client = genai.Client(api_key=key)

        try:
            # Generate content based on the provided model and text
            response = client.models.generate_content(
                model=model,
                contents=text,
                config={
                    "temperature": temperature,          # Added temperature and max tokens
                    "max_output_tokens": max_tokens
                }
            )

            # The SDK returns a response object; extract the text
            if response and response.text:
                # Clean up the response similar to the DeepSeek logic
                content = (
                    response.text
                )
                return content
            else:
                return "Failed: No content returned in the response."

        except Exception as e:
            # Catch SDK-specific or connection errors
            return f"Failed to fetch answer from Gemini: {str(e)}"



    def claude(self, text: str, model: str, key: str, temperature: int, max_tokens: int) -> str:
        """
        Calls Anthropic Messages API (Claude models)
        """
        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()

                # Claude returns content as a list of blocks
                content = "".join(
                    block.get("text", "")
                    for block in data.get("content", [])
                    if block.get("type") == "text"
                )

                content = (
                    content.replace("```", "")
                    .replace("sparql", "")
                )

                return content

            else:
                print(f"Error: {response.status_code}")
                try:
                    error_message = response.json().get("error", {}).get("message", "")
                    return f"Failed: {error_message}"
                except Exception:
                    return f"Failed: {response.text}"

        except Exception as e:
            return f"Failed to fetch answer from Claude: {str(e)}"
