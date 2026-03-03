from .workflow import graph
from .ui import build_ui
from .product_types import UserProfile, Product
import json
import re

def run_engine(
    user_budget, user_style, user_interest,
    product_name, product_category, product_price, product_features
):
    user: UserProfile = {
        "budget": user_budget,
        "style_preference": user_style,
        "interest": user_interest,
    }

    product: Product = {
        "name": product_name,
        "category": product_category,
        "price": product_price,
        "features": [f.strip() for f in product_features.split(",")],
    }

    final = graph.invoke({
        "user_profile": user,
        "product": product
    })

    # Get the generated text
    generated_text = final.get("generated", "")
    
    if not generated_text:
        return {"error": "No response generated"}
    
    # Ensure it's a string
    generated_text = str(generated_text)
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', generated_text, re.DOTALL)
    if json_match:
        generated_text = json_match.group(1)
    
    # Try to parse as JSON
    try:
        parsed = json.loads(generated_text)
        return parsed if isinstance(parsed, dict) else {"result": parsed}
    except json.JSONDecodeError:
        # Return as-is with the raw text
        return {"description": generated_text}

if __name__ == "__main__":
    ui = build_ui(run_engine)
    ui.launch(share=True)