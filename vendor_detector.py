"""
vendor_detector.py — LLM-powered vendor detection
Extracts vendor/tool name from a use case description.
Falls back to keyword matching if LLM detection is inconclusive.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from vendor_kb import VENDOR_KB, detect_vendor

load_dotenv()

DETECTION_PROMPT = """You are an AI governance specialist.
Read the following AI use case description and identify if it mentions
a specific AI vendor, platform, or tool.

Known vendors to look for:
- Microsoft: Copilot, Azure OpenAI, Microsoft 365 Copilot, Copilot Cowork, GitHub Copilot
- AWS: Amazon Bedrock, SageMaker, Comprehend Medical, HealthLake, HealthScribe
- Salesforce: Health Cloud, Einstein AI, Einstein GPT, Agentforce, Einstein Copilot

Respond with ONLY this JSON:
{
  "detected": true or false,
  "vendor_key": "microsoft" or "aws" or "salesforce" or null,
  "vendor_display": "exact name as mentioned in the text" or null,
  "confidence": "high" or "medium" or "low"
}"""


def detect_vendor_llm(use_case: str) -> dict:
    """
    Use LLM to detect vendor from use case description.
    Falls back to keyword matching on failure.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": DETECTION_PROMPT},
                {"role": "user",   "content": f"Use case:\n{use_case}"},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result
    except Exception:
        # Fallback to keyword matching
        vendor_key = detect_vendor(use_case)
        if vendor_key:
            vendor = VENDOR_KB[vendor_key]
            return {
                "detected":       True,
                "vendor_key":     vendor_key,
                "vendor_display": vendor["display_name"],
                "confidence":     "medium",
            }
        return {"detected": False, "vendor_key": None, "vendor_display": None, "confidence": "low"}


def get_all_vendor_options() -> list[dict]:
    """Return list of vendor options for the dropdown."""
    options = [{"key": None, "label": "None / Custom"}]
    for key, vendor in VENDOR_KB.items():
        options.append({
            "key":   key,
            "label": vendor["display_name"],
        })
    return options
