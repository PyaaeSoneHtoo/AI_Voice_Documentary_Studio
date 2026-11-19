"""
LLM Gateway — FreeLLMAPI Token Engine & Intelligent Failover
Dispatches requests to FreeLLMAPI's OpenAI-compatible endpoint with automatic fallbacks.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

import config

logger = logging.getLogger("DocuStudio.LLM")


class FreeLLMAPIGateway:
    def __init__(
        self,
        base_url: str = config.FREELLMAPI_BASE_URL,
        api_key: str = config.FREELLMAPI_API_KEY,
        default_model: str = config.FREELLMAPI_DEFAULT_MODEL
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

    def check_health(self) -> Tuple[bool, str]:
        """Checks if FreeLLMAPI gateway is online and reachable."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "AIVoiceDocumentaryStudio/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 204):
                    data = json.loads(resp.read().decode("utf-8"))
                    models_count = len(data.get("data", []))
                    return True, f"Online ({models_count} free models available)"
        except Exception as e:
            return False, f"Offline ({e})"
        return False, "Unreachable"

    def chat_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Sends chat completion to FreeLLMAPI (/v1/chat/completions).
        Falls back to direct API keys or heuristic engine if unreachable.
        """
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 1. Attempt FreeLLMAPI primary call
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "AIVoiceDocumentaryStudio/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Generated successfully via FreeLLMAPI ({target_model})")
                return content
        except Exception as e:
            logger.warning(f"FreeLLMAPI call failed ({e}). Attempting secondary fallbacks...")

        # 2. Direct Gemini 3.x Fallback
        if config.GEMINI_API_KEY:
            try:
                logger.info("Attempting direct Google Gemini fallback...")
                content = self._call_gemini_direct(system_prompt, user_prompt, config.GEMINI_API_KEY)
                if content:
                    return content
            except Exception as ge:
                logger.warning(f"Direct Gemini call failed: {ge}")

        # 3. Direct Groq Fallback
        if config.GROQ_API_KEY:
            try:
                logger.info("Attempting direct Groq fallback...")
                content = self._call_groq_direct(system_prompt, user_prompt, config.GROQ_API_KEY)
                if content:
                    return content
            except Exception as gre:
                logger.warning(f"Direct Groq call failed: {gre}")

        raise RuntimeError("All LLM providers unreachable. Please ensure FreeLLMAPI is running or provide an API key.")

    def _call_gemini_direct(self, system: str, user: str, api_key: str) -> str:
        """Calls Google's active Gemini 3.x models directly."""
        active_models = ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-3.7-flash"]
        prompt = f"{system}\n\nTask:\n{user}"

        for m in active_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
                body = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    return res["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                continue
        return ""

    def _call_groq_direct(self, system: str, user: str, api_key: str) -> str:
        """Calls Groq's fast Llama-3 models directly."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        body = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.7
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"]
