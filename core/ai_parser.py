"""
AI Product Parser Module
Handles product analysis via LM Studio or cloud APIs.
Extracts title, description, price, condition from product photos.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    HIGH = "high"      # > 0.85 - Can auto-post
    MEDIUM = "medium"  # 0.6-0.85 - Review recommended
    LOW = "low"        # < 0.6 - Needs manual review


@dataclass
class ProductAnalysis:
    """Structured output from AI parser"""
    title: str
    description: str
    price: Optional[float]
    condition: str
    category: str
    confidence: float
    needs_review: bool = False
    notes: list[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        if self.confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class LMStudioClient:
    """LM Studio API client - OpenAI-compatible interface"""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url.rstrip("/")
        logger.info(f"Initialized LM Studio client at {base_url}")
    
    def analyze_product(
        self, 
        image_path: str, 
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 256
    ) -> ProductAnalysis:
        """Analyze a product image and extract details"""
        
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Convert image to base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        model = model or self._get_primary_model()
        
        prompt = """You are an expert product listing assistant. Analyze this product photo and extract the following information in JSON format ONLY (no markdown, no explanations):

{
    "title": "concise product title under 80 characters",
    "description": "detailed description including brand, model, condition, any flaws or wear, dimensions if visible",
    "price": 99.99,
    "condition": "new|like new|excellent|good|fair|poor",
    "category": "books|dvd|clothing|collectibles|electronics|other",
    "confidence": 0.85,
    "notes": ["any observations that might affect sale"]
}

Rules:
- Be accurate and factual based ONLY on what you can see in the image
- If price is not visible, estimate a reasonable market value or set to null
- Condition should reflect actual state (look for wear, damage, etc.)
- Confidence should be 0.0-1.0 based on how clear/visible the product details are
- Include notes about any issues like profanity, unclear text, missing parts

Respond with valid JSON only."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a precise product extraction assistant. Return ONLY valid JSON."},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "url": f"data:image/jpeg;base64,{image_data}"}
                    ]
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            extracted_json = json.loads(result["choices"][0]["message"]["content"])
            
            # Validate and create ProductAnalysis object
            analysis = ProductAnalysis(
                title=extracted_json.get("title", "Untitled Item"),
                description=extracted_json.get("description", ""),
                price=float(extracted_json.get("price")) if extracted_json.get("price") else None,
                condition=extracted_json.get("condition", "unknown"),
                category=extracted_json.get("category", "other"),
                confidence=float(extracted_json.get("confidence", 0.5)),
                notes=extracted_json.get("notes", [])
            )
            
            # Flag for review if low confidence
            analysis.needs_review = analysis.confidence < 0.75
            
            logger.info(f"Analyzed {Path(image_path).name}: confidence={analysis.confidence:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed for {image_path}: {e}")
            raise


class ProductParser:
    """Main parser class with fallback logic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.lmstudio_client = LMStudioClient(
            base_url=config.get("lmstudio_url", "http://localhost:1234/v1")
        )
        
        # Model configuration
        self.models = {
            "primary": config.get("models", {}).get("primary", "llava-next-nearest-34b"),
            "fast": config.get("models", {}).get("fast", "qwen2.5-vl-7b-instruct")
        }
        
        # Parameters
        self.params = {
            "temperature": config.get("parameters", {}).get("temperature", 0.3),
            "max_tokens": config.get("parameters", {}).get("max_tokens", 256)
        }
    
    def analyze(self, image_path: str) -> ProductAnalysis:
        """Main analysis method with fallback"""
        
        try:
            # Try primary model first (more accurate)
            logger.info(f"Using primary model: {self.models['primary']}")
            return self.lmstudio_client.analyze_product(
                image_path, 
                model=self.models["primary"],
                temperature=self.params["temperature"],
                max_tokens=self.params["max_tokens"]
            )
        except Exception as e:
            logger.warning(f"Primary model failed ({e}), trying fallback")
            
            try:
                # Fallback to faster/smaller model
                logger.info(f"Using fast model: {self.models['fast']}")
                return self.lmstudio_client.analyze_product(
                    image_path, 
                    model=self.models["fast"],
                    temperature=self.params["temperature"],
                    max_tokens=self.params["max_tokens"]
                )
            except Exception as e2:
                logger.error(f"Both models failed: {e}, {e2}")
                
                # Return a placeholder for manual review
                return ProductAnalysis(
                    title="Image Failed to Process",
                    description=str(e) + str(e2),
                    price=None,
                    condition="unknown",
                    category="other",
                    confidence=0.1,
                    needs_review=True,
                    notes=["AI analysis failed - manual review required"]
                )


def create_parser(config: Dict[str, Any]) -> ProductParser:
    """Factory function to create parser from config"""
    return ProductParser(config.get("ai_parser", {}))
