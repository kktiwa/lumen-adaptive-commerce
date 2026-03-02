import gradio as gr
from typing import Callable

def build_ui(run_fn: Callable):
    with gr.Blocks(title="Iteration 1 – Adaptive Product Search") as demo:
        gr.Markdown("## 🔍 Adaptive Product Search Generator")

        with gr.Row():
            with gr.Column():
                user_budget = gr.Dropdown(["Budget", "Midrange", "Premium"], label="User Budget")
                user_style = gr.Dropdown(["Minimal", "Bold", "Sleek", "Earthy"], label="Style Preference")
                user_interest = gr.Textbox(label="Interest")

            with gr.Column():
                product_name = gr.Textbox(label="Product Name")
                product_category = gr.Textbox(label="Category")
                product_price = gr.Number(label="Price")
                product_features = gr.Textbox(label="Features (comma-separated)")

        btn = gr.Button("Generate")
        output = gr.JSON(label="Adaptive Output")

        btn.click(
            fn=run_fn,
            inputs=[
                user_budget, user_style, user_interest,
                product_name, product_category, product_price, product_features
            ],
            outputs=output
        )

    return demo