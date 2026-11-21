import logging
import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


class Prompt(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


def _demo_reply(message: str) -> str:
    normalized = message.lower()
    if "tomato" in normalized:
        return "For tomatoes, keep soil evenly moist, provide full sun, and harvest when fully colored. Protect against frost and check leaves weekly for pests."
    if "price" in normalized:
        return "Set a fair price by comparing local market averages, transport costs, expected yield, and crop quality. PejaMarket analytics can help track sales."
    if "stock" in normalized:
        return "Keep stock levels accurate after each harvest or sale. Update inventory promptly so customers only see produce that is available."
    return "Welcome to PejaMarket! I can help with crop care, pricing, inventory, and order planning."


@router.post("/assistant")
def assistant(prompt: Prompt):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=300,
                system="You are PejaMarket's helpful farm marketplace assistant. Give concise practical advice.",
                messages=[{"role": "user", "content": prompt.message}],
            )
            return {"reply": response.content[0].text, "provider": "anthropic"}
        except Exception as exc:
            logger.warning(
                "Anthropic farm-assistant request failed (%s); using the demo response",
                type(exc).__name__,
            )
    reply = _demo_reply(prompt.message)
    return {"reply": reply, "provider": "demo"}


class ProductDescriptionRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=150)
    category: str = Field(min_length=2, max_length=80)
    qualities: str = Field(default="", max_length=500)
    farming_method: str = Field(default="", max_length=500)


@router.post("/product-description")
def product_description(payload: ProductDescriptionRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    details = " ".join(part for part in [payload.qualities.strip(), payload.farming_method.strip()] if part)
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = (
                f"Write a one-paragraph English marketplace description for {payload.product_name}. "
                f"Category: {payload.category}. "
                f"Only use these supplied facts: {details or 'No additional facts supplied.'} "
                "Do not invent certifications, methods, or health benefits."
            )
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=180,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"description": response.content[0].text, "provider": "anthropic"}
        except Exception as exc:
            logger.warning(
                "Anthropic product-description request failed (%s); using the demo response",
                type(exc).__name__,
            )
    description = f"{payload.product_name.strip()}."
    if details:
        description = f"{description} {details}"
    return {
        "description": description,
        "provider": "demo",
    }


class CategorySuggestionRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=1000)


@router.post("/category-suggestion")
def category_suggestion(payload: CategorySuggestionRequest):
    text = f"{payload.product_name} {payload.description}".lower()
    if any(word in text for word in ("milk", "cheese", "yogurt", "egg")):
        category, unit = "Dairy Products", "package"
    elif any(word in text for word in ("apple", "pear", "berry", "fruit", "plum")):
        category, unit = "Fruits", "kg"
    elif any(word in text for word in ("wheat", "flour", "grain", "corn")):
        category, unit = "Grains", "kg"
    elif any(word in text for word in ("bread", "jam", "honey", "preserve", "homemade")):
        category, unit = "Homemade Products", "package"
    else:
        category, unit = "Vegetables", "kg"
    return {
        "category": category,
        "unit": unit,
        "title": payload.product_name,
        "provider": "demo",
    }


@router.post("/chat")
def chat(payload: Prompt):
    result = assistant(payload)
    return {"reply": result["reply"], "provider": result["provider"]}
