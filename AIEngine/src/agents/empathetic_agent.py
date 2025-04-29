from agents.base_agent import Agent
from typing import Dict, Tuple


class EmpatheticAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Empathetic Agent", api_token)
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Provide empathetic responses and emotional support.
        Returns: (response, updated_context, should_transition)
        """
        # If this is first time in this state, start empathetic conversation
        if context.get("empathy_attempts", 0) == 0:
            initial_response = self.start_empathetic_conversation(context)
            context["empathy_attempts"] = 1
            return initial_response, context, False
        
        # Update attempt counter
        context["empathy_attempts"] = context.get("empathy_attempts", 0) + 1
        
        # Evaluate if we should transition after at least one exchange
        transition_evaluation = self.evaluate_transition(context)
        should_transition = transition_evaluation.get("should_transition", False)
        
        if should_transition:
            return transition_evaluation.get("transition_message", "I think it might be helpful to try a practical approach. Would you be open to a suggestion that might help?"), context, True
        
        # Continue empathetic conversation
        system_prompt = """
        You are a mental health assistant for working professionals. Continue the empathetic
        conversation by responding to the user's latest message. Validate their feelings,
        normalize their experience when appropriate, and gently help them gain perspective.
        Be patient, kind, and authentic.
        """
        
        messages = context.get("conversation_history", []).copy()
        
        return self.get_completion(messages, system_prompt), context, False
    
    def start_empathetic_conversation(self, context: Dict) -> str:
        system_prompt = """
        You are a mental health assistant for working professionals. Provide an empathetic,
        supportive response that acknowledges the user's feelings and challenges. Offer some
        initial perspective or validation that might help them feel understood and less alone.
        Be genuine, warm, and compassionate.
        """
        
        mood_context = f"User's mood: {context.get('user_mood', 'unknown')}"
        issue_context = f"Primary issue: {context.get('underlying_issue', 'unknown')}"
        
        # Combine all relevant inputs
        all_inputs = []
        if context.get("conversation_history"):
            for msg in context.get("conversation_history"):
                if msg["role"] == "user":
                    all_inputs.append(msg["content"])
        
        input_text = "\n".join(all_inputs)
        
        messages = [
            {"role": "user", "content": f"Based on this context:\n{mood_context}\n{issue_context}\n\nUser activities: {input_text}\n\nProvide an empathetic response that acknowledges their challenges and offers support."}
        ]
        
        return self.get_completion(messages, system_prompt)
    
    def evaluate_transition(self, context: Dict) -> Dict:
        attempts = context.get("empathy_attempts", 0)
        
        system_prompt = """
        Determine if we have provided enough empathetic support and should transition to suggesting
        tools or techniques that might help the user. Consider:
        1. How many empathy-focused exchanges we've had
        2. If the conversation feels like it's reaching a natural point for practical support
        3. Whether the user seems receptive to suggestions or tools
        """
        
        format_instruction = """
        {
            "should_transition": true|false,
            "reasoning": "explanation for the decision",
            "transition_message": "a smooth transition message if should_transition is true"
        }
        """
        
        messages = [
            {"role": "user", "content": f"Number of empathetic exchanges: {attempts}\nMood: {context.get('user_mood', 'unknown')}\nIssue: {context.get('underlying_issue', 'unknown')}\n\nShould we transition to tool suggestion?"}
        ]
        
        result = self.get_structured_completion(messages, system_prompt, format_instruction)
        
        # Override with attempt threshold as fallback
        if not result.get("should_transition") and attempts >= 2:
            result["should_transition"] = True
            result["reasoning"] = f"Overriding because we've had {attempts} empathy-focused exchanges"
            
            if not result.get("transition_message"):
                name_prefix = f"{context.get('user_name')}" if context.get('user_name') else "there"
                
                result["transition_message"] = f"I wonder, {name_prefix}, if it might be helpful to try a practical technique that could help with what you're experiencing. Would you be open to that?"
        
        return result
