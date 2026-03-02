from .workflow import graph
from .ui import build_ui
from .product_types import UserProfile, Product

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

    return final["generated"]

if __name__ == "__main__":
    ui = build_ui(run_engine)
    ui.launch()