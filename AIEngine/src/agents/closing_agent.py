from agents.base_agent import Agent
from typing import Dict, Tuple


class ClosingAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Closing Agent", api_token)
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Create a warm closing to the conversation.
        Returns: (response, updated_context, should_transition)
        """
        system_prompt = """
        Create a warm closing message that:
        1. Acknowledges the conversation and what was shared
        2. Reinforces any action plan or insights gained
        3. Offers encouragement and hope
        4. Reminds them that it's okay to seek support when needed
        5. Ends on a positive, hopeful note
        
        Use their name if available and reference specific elements of your conversation.
        """
        
        name_prefix = f", {context.get('user_name')}" if context.get('user_name') else ""
        mood = context.get('user_mood', 'your feelings')
        issue = context.get('underlying_issue', 'the challenges you mentioned')
        
        # Build context from conversation data
        context_summary = f"User name: {context.get('user_name', 'Not provided')}\n"
        context_summary += f"Mood: {context.get('user_mood', 'unknown')}\n"
        context_summary += f"Issue: {context.get('underlying_issue', 'unknown')}\n"
        
        if context.get('action_plan') and context.get('action_plan').get('actions'):
            actions = [a.get('title', 'An action') for a in context.get('action_plan', {}).get('actions', [])]
            context_summary += f"Action plan: {', '.join(actions)}\n"
        
        messages = [
            {"role": "user", "content": f"Create a closing message for this conversation.\n\nContext:\n{context_summary}"}
        ]
        
        closing = self.get_completion(messages, system_prompt)
        
        # Always end the conversation after closing
        context["closing_complete"] = True
        return closing, context, True
