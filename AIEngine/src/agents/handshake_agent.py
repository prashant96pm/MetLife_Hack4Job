from agents.base_agent import Agent
from typing import Dict, Tuple


class HandshakeAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Handshake Agent", api_token)
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Process initial handshake with user.
        Returns: (response, updated_context, should_transition)
        """
        # Extract name if present
        name_result = self.extract_name(user_input)
        if name_result.get("name"):
            context["user_name"] = name_result.get("name")
        
        # Evaluate if we have enough information to move to mood analysis
        transition_evaluation = self.evaluate_transition(user_input, context)
        should_transition = transition_evaluation.get("should_transition", False)
        
        if should_transition:
            # Prepare for transition but let the coordinator handle it
            return transition_evaluation.get("farewell_message", "Thanks for sharing about your day. I'd like to understand how you're feeling."), context, True
        
        # Generate a follow-up question
        system_prompt = """
        You are a mental health assistant for working professionals. Ask a follow-up question
        about the user's day at work. Be friendly and conversational. Ask about specific aspects
        of their work day like meetings, tasks, interactions with colleagues, or accomplishments.
        """
        
        messages = [{"role": "user", "content": user_input}]
        if context.get("conversation_history"):
            messages = context.get("conversation_history").copy()
        
        response = self.get_completion(messages, system_prompt)
        return response, context, False
    
    def extract_name(self, text: str) -> Dict:
        system_prompt = """
        Extract the user's name if they introduce themselves. 
        If no name is found, return null.
        """
        
        format_instruction = """
        {
            "name": "string or null"
        }
        """
        
        messages = [
            {"role": "user", "content": f"Extract name from: '{text}'"}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
    
    def evaluate_transition(self, user_input: str, context: Dict) -> Dict:
        system_prompt = """
        Determine if we have enough information about the user to transition from initial handshake
        to mood analysis. Consider:
        1. Length and detail of their responses
        2. If they've mentioned work-related activities
        3. If they've shared any feelings or experiences
        
        We should transition when:
        - The user has provided substantial information about their day/activities
        - OR they've shared their current feelings/mood already
        - OR the handshake exchange has gone on for a sufficient period
        """
        
        format_instruction = """
        {
            "should_transition": true|false,
            "confidence": "number between 0-10",
            "reasoning": "explanation for the decision",
            "farewell_message": "a transition message if should_transition is true"
        }
        """
        
        # Combine all conversation history
        all_messages = []
        if context.get("conversation_history"):
            for msg in context.get("conversation_history"):
                if msg["role"] == "user":
                    all_messages.append(msg["content"])
        all_messages.append(user_input)
        
        conversation_text = "\n".join(all_messages)
        attempts = context.get("handshake_attempts", 0)
        
        messages = [
            {"role": "user", "content": f"Conversation so far:\n{conversation_text}\n\nNumber of exchanges: {attempts + 1}\n\nShould we transition to mood analysis?"}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
