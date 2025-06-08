from flask import Flask, request, jsonify
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Import the existing MentalHealthChatbot class
from chatbot.mental_health_chatbot import MentalHealthChatbot

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Store chatbot instances


def get_chatbot():
    global chatbot_instance
    if chatbot_instance is None:
        api_token = os.getenv("API_KEY")
        if not api_token:
            raise ValueError("API_KEY environment variable not set")
        chatbot_instance = MentalHealthChatbot(api_token)
    return chatbot_instance

def format_response(chatbot, assistant_message: str) -> Dict[str, Any]:
    """Format the API response with conversation details"""
    
    # Get the enum name as a string for the current stage
    current_stage = chatbot.current_stage.name if chatbot.current_stage else None
    
    # Extract relevant data from context
    context = chatbot.context
    
    response = {
        "assistant_message": assistant_message,
        "conversation_state": {
            "current_stage": current_stage,
            "user_mood": context.get("user_mood", None),
            "underlying_issue": context.get("underlying_issue", None),
            "user_name": context.get("user_name", None),
            "recommended_tool": context.get("recommended_tool", None),
            "action_plan": context.get("action_plan", None),
            "closing_complete": context.get("closing_complete", False)
        }
    }
    
    return response

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get the request data
        data = request.json
        
        if not data or 'user_message' not in data:
            return jsonify({
                "error": "Missing required parameter: user_message"
            }), 400
        
        user_message = data.get('user_message')
        
        # Get or create chatbot instance
        chatbot = get_chatbot()
        
        # Process user input
        assistant_message = chatbot.process_user_input(user_message)
        
        # Format and return the response
        response = format_response(chatbot, assistant_message)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "assistant_message": "I'm sorry, I encountered an error processing your message."
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the chatbot to initial state"""
    try:
        global chatbot_instance
        api_token = os.getenv("API_KEY")
        if not api_token:
            return jsonify({
                "error": "API_KEY environment variable not set"
            }), 500
            
        chatbot_instance = MentalHealthChatbot(api_token)
        
        return jsonify({
            "message": "Chatbot reset successful",
            "conversation_state": {
                "current_stage": "INITIAL_HANDSHAKE",
                "user_mood": None,
                "underlying_issue": None,
                "user_name": None,
                "recommended_tool": None,
                "action_plan": None,
                "closing_complete": False
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)