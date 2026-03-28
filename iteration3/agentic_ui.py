"""Gradio UI for autonomous agentic shopping application"""
import gradio as gr
import asyncio
from typing import Generator
import logging

from .agentic_workflow import (
    initialize_state,
    build_agentic_workflow,
    get_initial_greeting,
)
from .product_database import initialize_vector_search
from .agentic_types import AgenticState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticShoppingUI:
    """Manages the Gradio UI for autonomous agentic shopping"""
    
    def __init__(self):
        """Initialize the UI"""
        # Initialize vector search for semantic product matching
        try:
            initialize_vector_search()
            logger.info("Vector search initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector search: {e}")
        
        self.current_state: AgenticState = initialize_state()
        self.workflow = build_agentic_workflow().compile()
    
    def reset_conversation(self) -> tuple[str, str]:
        """Reset the conversation state"""
        self.current_state = initialize_state()
        greeting = get_initial_greeting()
        return greeting, ""
    
    def process_message(self, user_message: str, conversation_history: str) -> tuple[str, str]:
        """
        Process a user message and get agent response
        
        Args:
            user_message: The user's message
            conversation_history: The conversation history so far
        
        Returns:
            Tuple of (updated_history, agent_response)
        """
        
        if not user_message.strip():
            return conversation_history, "Please enter a message."
        
        try:
            # Set current message
            self.current_state["current_message"] = user_message
            
            # Execute the workflow
            result_state = self.workflow.invoke(self.current_state)
            
            # Update state
            self.current_state = result_state
            
            # Update conversation history
            new_history = conversation_history
            if new_history:
                new_history += "\n\n"
            
            new_history += f"**You:** {user_message}\n\n**Agent:** {result_state['assistant_response']}"
            
            # Get agent response
            agent_response = result_state["assistant_response"]
            
            logger.info(f"Message processed - Next action: {result_state['next_action']}")
            
            return new_history, agent_response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_msg = "I encountered an error processing your message. Please try again."
            return conversation_history, error_msg


def build_ui() -> gr.Blocks:
    """Build the Gradio UI"""
    
    ui_manager = AgenticShoppingUI()
    
    with gr.Blocks(title="Lumen Adaptive Commerce - Autonomous Shopping Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🛍️ Lumen Adaptive Commerce - Autonomous Shopping Agent
        
        Chat with our AI shopping agent to find the perfect product and complete your purchase!
        
        The agent will help you:
        1. Understand your needs
        2. Recommend the perfect product
        3. Guide you through checkout
        4. Process your payment
        5. Send you an order confirmation
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                conversation_display = gr.Textbox(
                    label="Conversation",
                    value=get_initial_greeting(),
                    interactive=False,
                    lines=20,
                    max_lines=50,
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Order Status")
                product_status = gr.Textbox(
                    label="Selected Product",
                    value="None",
                    interactive=False,
                )
                payment_status = gr.Textbox(
                    label="Payment Status",
                    value="Pending",
                    interactive=False,
                )
        
        with gr.Row():
            user_input = gr.Textbox(
                label="Your Message",
                placeholder="Type your message here...",
                lines=2,
            )
        
        with gr.Row():
            submit_btn = gr.Button("Send", variant="primary", size="lg")
            reset_btn = gr.Button("Start Over", variant="secondary")
        
        # Define interactions
        def on_submit(message: str, history: str):
            """Handle message submission"""
            if not message.strip():
                return history, "Please enter a message."
            
            new_history, response = ui_manager.process_message(message, history)
            
            # Update status
            product_info = "None"
            if ui_manager.current_state["selected_product"]:
                product_info = f"{ui_manager.current_state['selected_product']['name']}\n${ui_manager.current_state['selected_product']['price']:.2f}"
            
            payment_info = "Pending"
            if ui_manager.current_state["order_completed"]:
                payment_info = "✓ Completed"
            elif ui_manager.current_state["payment_successful"]:
                payment_info = "✓ Processed"
            elif ui_manager.current_state["payment_error"]:
                payment_info = f"✗ Failed: {ui_manager.current_state['payment_error'][:50]}"
            
            return new_history, response, product_info, payment_info
        
        def on_reset():
            """Handle reset"""
            greeting, response = ui_manager.reset_conversation()
            return greeting, response, "None", "Pending"
        
        # Connect buttons to handlers
        submit_btn.click(
            fn=on_submit,
            inputs=[user_input, conversation_display],
            outputs=[conversation_display, user_input, product_status, payment_status],
        ).then(
            lambda: "",
            outputs=user_input,
        )
        
        reset_btn.click(
            fn=on_reset,
            outputs=[conversation_display, user_input, product_status, payment_status],
        )
        
        # Allow pressing Enter to submit
        user_input.submit(
            fn=on_submit,
            inputs=[user_input, conversation_display],
            outputs=[conversation_display, user_input, product_status, payment_status],
        ).then(
            lambda: "",
            outputs=user_input,
        )
        
        # Add information about the demo
        with gr.Row():
            with gr.Accordion("ℹ️ Demo Information", open=False):
                gr.Markdown("""
                ### About This Demo
                
                This is an autonomous agentic shopping application built with LangGraph and LLMs.
                
                **Features:**
                - Natural language conversation
                - Intelligent product recommendations
                - Contextual understanding of needs
                - Secure checkout process
                - Order confirmation via email
                
                **Sample Users:**
                - Alice Johnson (user_001) - Default user
                - Bob Smith (user_002)
                
                **Sample Products:**
                - Superhero Cape Set ($25)
                - STEM Robot Kit ($45)
                - Outdoor Scavenger Hunt ($30)
                - Art Supply Box ($55)
                - Bamboo Toy Set ($40)
                - Sports Bundle ($120)
                - Party Game Pack ($35)
                - Learning Tablet ($180)
                
                **Try saying things like:**
                - "I need a gift for my 6-year-old's birthday party"
                - "Show me educational toys under $50"
                - "What eco-friendly products do you have?"
                - "I'll proceed with the default address and payment"
                """)
    
    return demo


def main():
    """Main entry point"""
    print("Starting Autonomous Agentic Shopping Application...")
    demo = build_ui()
    demo.launch(share=True)


if __name__ == "__main__":
    main()
