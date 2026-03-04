"""Main application logic for conversational chat"""
from .chat_workflow import graph, create_initial_state
from .user_preferences import get_available_profiles

class ConversationalChatEngine:
    """Main engine for conversational product recommendations"""
    
    def __init__(self, profile_id: str = "profile1"):
        self.state = create_initial_state(profile_id)
        self.profile_id = profile_id
    
    def send_message(self, user_message: str) -> dict:
        """Send a message and get a response"""
        # Update current message
        self.state["current_message"] = user_message
        
        # Run the workflow
        result = graph.invoke(self.state)
        
        # Update state with result
        self.state = result
        
        return {
            "response": result["assistant_response"],
            "recommendations": result["product_recommendations"],
            "conversation_complete": result["conversation_complete"],
            "context": result["conversation_context"]
        }
    
    def get_conversation_history(self) -> list:
        """
        Retrieve the complete conversation history with formatted timestamps.

        Returns a list of message dictionaries containing the role, content, and 
        ISO-formatted timestamp for each message in the conversation history. This 
        allows clients to access the full dialogue context in a serializable format.

        Returns:
            list: A list of dictionaries, each containing:
                - role (str): The message sender's role (e.g., 'user', 'assistant')
                - content (str): The message text content
                - timestamp (str): ISO 8601 formatted timestamp of when the message was sent

        Raises:
            KeyError: If expected message structure is missing 'role', 'content', or 'timestamp' keys
        """
        """Get the full conversation history"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat()
            }
            for msg in self.state["conversation_history"]
        ]
    
    def reset_conversation(self, profile_id: str = None):
        """Reset the conversation"""
        if profile_id:
            self.profile_id = profile_id
        self.state = create_initial_state(self.profile_id)
    
    def get_user_profile(self) -> dict:
        """Get the current user's profile"""
        return {
            "budget": self.state["user_preferences"]["budget"],
            "interests": self.state["user_preferences"]["interests"],
            "preferences": self.state["user_preferences"]["preferences"]
        }

def run_chat_session(profile_id: str = "profile1"):
    """Run an interactive chat session (for testing)"""
    engine = ConversationalChatEngine(profile_id)
    
    print(f"\n=== Conversational Shopping Assistant ===")
    print(f"Loaded profile: {profile_id}")
    print(f"Budget: {engine.get_user_profile()['budget']}")
    print(f"Interests: {', '.join(engine.get_user_profile()['interests'])}")
    print("\nHello! I'm here to help you find the perfect products. Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
        
        result = engine.send_message(user_input)
        print(f"\nAssistant: {result['response']}\n")
        
        if result["conversation_complete"]:
            print(f"\n=== Recommended Products ===")
            for product in result["recommendations"]:
                print(f"- {product['name']} (${product['price']}) - {product['category']}")
            print()

if __name__ == "__main__":
    run_chat_session("profile1")
