"""Gradio UI for conversational chat"""
import gradio as gr
from .chat_app import ConversationalChatEngine
from .user_preferences import get_available_profiles

# Global engine instance
engine = None

def initialize_chat(profile_id: str):
    """Initialize chat with selected profile"""
    global engine
    engine = ConversationalChatEngine(profile_id)
    profile = engine.get_user_profile()
    
    profile_info = f"""
    **Profile Loaded**
    - Budget: {profile['budget']}
    - Interests: {', '.join(profile['interests'])}
    - Eco-friendly: {profile['preferences'].get('eco_friendly', False)}
    - Premium: {profile['preferences'].get('premium', False)}
    
    Ask me anything about what you're looking for!
    """
    
    return profile_info, [], ""

def send_message(message: str, chat_history: list) -> tuple:
    """Send a message and get response"""
    global engine
    
    if engine is None:
        # Return chat_history as-is, with error message
        return chat_history, "Please select a profile first.", ""
    
    if not message.strip():
        return chat_history, "", ""
    
    result = engine.send_message(message)
    
    # Add to chat history - use dictionary format for newer Gradio versions
    if chat_history is None:
        chat_history = []
    
    chat_history = list(chat_history) if chat_history else []
    
    # Add user and assistant messages in the correct format
    chat_history.append({
        "role": "user",
        "content": message
    })
    chat_history.append({
        "role": "assistant",
        "content": result["response"]
    })
    
    # Build recommendations display
    recommendations_text = ""
    if result["conversation_complete"] and result["recommendations"]:
        recommendations_text = "**Recommended Products:**\n\n"
        for product in result["recommendations"]:
            recommendations_text += f"- **{product['name']}** (${product['price']})\n"
            recommendations_text += f"  - Category: {product['category']}\n"
            recommendations_text += f"  - Features: {', '.join(product['features'])}\n"
            recommendations_text += f"  - Age Range: {product['age_range']}\n\n"
    
    return chat_history, recommendations_text, ""

def reset_chat():
    """Reset the conversation"""
    global engine
    if engine:
        engine.reset_conversation()
    return [], "", ""

def build_ui():
    """Build the Gradio UI"""
    with gr.Blocks(title="Adaptive Commerce - Conversational Shopping") as demo:
        gr.Markdown("""
        # 🛍️ Conversational Shopping Assistant
        
        Welcome! I'm here to help you find the perfect products through conversation.
        Simply tell me what you're looking for, and I'll ask follow-up questions to narrow down to the best recommendations.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Profile Selection")
                profile_dropdown = gr.Dropdown(
                    choices=get_available_profiles(),
                    value="profile1",
                    label="Select User Profile",
                    interactive=True
                )
                load_profile_btn = gr.Button("Load Profile", variant="primary")
            
            with gr.Column(scale=2):
                profile_info = gr.Markdown("Select a profile and click 'Load Profile' to begin.")
        
        gr.Markdown("---")
        
        with gr.Row():
            chatbot = gr.Chatbot(
                value=[],
                label="Conversation",
                height=400,
                show_label=True,
                scale=1
            )
        
        with gr.Row():
            message_input = gr.Textbox(
                label="Your message",
                placeholder="Tell me what you're looking for...",
                lines=2
            )
        
        with gr.Row():
            send_btn = gr.Button("Send", variant="primary", scale=2)
            reset_btn = gr.Button("Reset Conversation", scale=1)
        
        gr.Markdown("---")
        
        recommendations = gr.Markdown(label="Recommendations")
        
        # Connect button events
        load_profile_btn.click(
            fn=initialize_chat,
            inputs=[profile_dropdown],
            outputs=[profile_info, chatbot, message_input]
        )
        
        send_btn.click(
            fn=send_message,
            inputs=[message_input, chatbot],
            outputs=[chatbot, recommendations, message_input]
        )
        
        # Allow Enter key to send
        message_input.submit(
            fn=send_message,
            inputs=[message_input, chatbot],
            outputs=[chatbot, recommendations, message_input]
        )
        
        reset_btn.click(
            fn=reset_chat,
            outputs=[chatbot, recommendations, message_input]
        )
    
    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch()
