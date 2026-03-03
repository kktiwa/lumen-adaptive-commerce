from common.config import settings, initialize_arize_tracing

# Initialize Arize tracing BEFORE importing workflow
initialize_arize_tracing(settings)

from .workflow import graph
from .ui import build_ui
from .product_types import UserProfile, Product
import json
import re

def json_to_html(data: dict) -> str:
    """Convert product JSON data to HTML."""
    if isinstance(data, dict):
        # Extract fields from the JSON
        header = data.get("Header", data.get("header", "Product Title"))
        subheader = data.get("Subheader", data.get("subheader", ""))
        tagline = data.get("Tagline", data.get("tagline", ""))
        summary = data.get("Summary", data.get("summary", ""))
        visual_cues = data.get("Visual cues", data.get("visual_cues", ""))
        cta = data.get("CTA", data.get("cta", "Shop Now"))
        metatags = data.get("Metatags", data.get("metatags", []))
        social_proof = data.get("Social proof", data.get("social_proof", ""))
        hyperlink = data.get("Hyperlink label", data.get("hyperlink_label", ""))
        
        # Format metatags if it's a list
        metatags_html = ""
        if metatags:
            if isinstance(metatags, list):
                metatags_html = " ".join([f'<span class="tag">{tag}</span>' for tag in metatags])
            else:
                metatags_html = f'<span class="tag">{metatags}</span>'
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: white;">
            <div style="border-bottom: 3px solid #f0f0f0; padding-bottom: 20px; margin-bottom: 20px;">
                <h1 style="margin: 0 0 10px 0; font-size: 32px; color: #1a1a1a;">{header}</h1>
                {f'<h2 style="margin: 0 0 10px 0; font-size: 20px; color: #666; font-weight: 500;">{subheader}</h2>' if subheader else ''}
                {f'<p style="margin: 0; font-size: 16px; color: #999; font-style: italic;">{tagline}</p>' if tagline else ''}
            </div>
            
            {f'<div style="margin-bottom: 20px;"><p style="font-size: 16px; line-height: 1.6; color: #333;">{summary}</p></div>' if summary else ''}
            
            {f'<div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-left: 4px solid #007bff; border-radius: 4px;"><p style="margin: 0; color: #333;">{visual_cues}</p></div>' if visual_cues else ''}
            
            {f'<div style="margin-bottom: 20px;"><p style="margin: 5px 0; font-size: 14px; color: #666;"><strong>Social Proof:</strong> {social_proof}</p></div>' if social_proof else ''}
            
            {f'<div style="margin-bottom: 20px;"><div style="display: flex; flex-wrap: wrap; gap: 10px;">{metatags_html}</div></div>' if metatags_html else ''}
            
            <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; text-align: center;">
                <a href="#" style="display: inline-block; background: white; color: #667eea; padding: 12px 32px; text-decoration: none; font-weight: 600; border-radius: 4px; font-size: 16px;">{cta}</a>
                {f'<p style="margin-top: 10px; color: white; font-size: 12px;">{hyperlink}</p>' if hyperlink else ''}
            </div>
        </div>
        """
        return html
    else:
        return f"<p>{str(data)}</p>"

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
        if isinstance(parsed, dict):
            # Convert to HTML
            return json_to_html(parsed)
        else:
            return json_to_html({"result": str(parsed)})
    except json.JSONDecodeError:
        # Return as-is with the raw text
        return json_to_html({"description": generated_text})

if __name__ == "__main__":
    ui = build_ui(run_engine)
    ui.launch(share=True)