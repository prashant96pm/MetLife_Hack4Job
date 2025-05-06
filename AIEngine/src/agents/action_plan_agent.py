from agents.base_agent import Agent
from typing import Dict, Tuple


class ActionPlanAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Action Plan Agent", api_token)
    
        """
        Create an action plan and handle user feedback.
        Returns: (response, updated_context, should_transition)
        """
        # If this is first time in this state, create action plan
        if context.get("action_plan_attempts", 0) == 0:
            action_plan = self.create_action_plan(context)
            context["action_plan"] = action_plan
            context["action_plan_attempts"] = 1
            
            # Format the response
            response = action_plan.get("plan_introduction", "I'd like to suggest a few actions for tomorrow that might help:") + "\n\n"
            
            for i, action in enumerate(action_plan.get("actions", []), 1):
                response += f"{i}. **{action.get('title', 'Action')}**: {action.get('description', '')}\n"
            
            if "additional_suggestion" in action_plan:
                response +=  f"\nOne more thing: {action_plan['additional_suggestion']}\n"
                
            response += "\nHow does this plan sound to you? Is there anything you'd like to adjust?"
            
            return response, context, False
        
        # Analyze user feedback on the plan
        feedback_analysis = self.analyze_feedback(user_input, context)
        context["plan_feedback"] = feedback_analysis
        
        # Check if user wants to adjust the plan
        if feedback_analysis.get("wants_adjustment", False):
            # User wants to adjust - stay in action plan stage
            updated_plan = self.adjust_plan(user_input, context)
            return updated_plan, context, False
        else:
            # User is satisfied or neutral about the plan - transition to closing
            return "Thank you for your feedback. I hope this plan will be helpful for you.", context, True
 
    
    def create_action_plan(self, context: Dict) -> Dict:
        system_prompt = """
        Create a simple action plan for the user based on what you've learned about their
        mood, challenges, and workplace situation. Focus on 3-5 small, actionable steps they
        can take tomorrow to improve their wellbeing. Be specific and realistic. Consider
        their work context and the professional challenges they've mentioned.
        """
        
        format_instruction = """
        {
            "plan_introduction": "brief introduction to the action plan",
            "actions": [
                {"title": "action title", "description": "brief description", "benefit": "how this helps"}
            ],
            "additional_suggestion": "one more general wellbeing suggestion"
        }
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
            {"role": "user", "content": f"Based on this context:\n{mood_context}\n{issue_context}\n\nUser messages: {input_text}\n\nCreate a personalized action plan."}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
    
    def analyze_feedback(self, user_input: str, context: Dict) -> Dict:
        system_prompt = """
        Analyze the user's feedback on the action plan. Determine if they accepted the plan,
        if they had specific concerns, or if they suggested modifications.
        """
        
        format_instruction = """
        {
            "accepted_plan": true|false,
            "concerns": ["array of concerns if any"],
            "suggestions": ["array of user suggestions if any"],
            "sentiment": "positive|neutral|negative",
            "wants_adjustment": true|false

        }
        """
        
        messages = [
            {"role": "user", "content": f"Action plan: {json.dumps(context.get('action_plan', {}))}. User feedback: '{user_input}'. Analyze their response."}
        ]
        
        result =  self.get_structured_completion(messages, system_prompt, format_instruction)
        # If result doesn't include wants_adjustment, determine it from the text
        if "wants_adjustment" not in result:
            wants_adjustment = self.detect_adjustment_request(user_input)
            result["wants_adjustment"] = wants_adjustment
            
        return result
        
    def detect_adjustment_request(self, user_input: str) -> bool:
        """Specifically check if the user wants to adjust the plan"""
        system_prompt = """
        Determine if the user is explicitly requesting to adjust or modify the action plan.
        Look for phrases like "I want to adjust", "can we change", "I'd prefer", etc.
        """
        
        format_instruction = """
        {
            "wants_adjustment": true|false,
            "confidence": "number between 0-10"
        }
        """
        
        messages = [
            {"role": "user", "content": f"Is the user requesting to adjust the plan in this message: '{user_input}'?"}
        ]
        
        result = self.get_structured_completion(messages, system_prompt, format_instruction)
        return result.get("wants_adjustment", False)
    
    def adjust_plan(self, user_input: str, context: Dict) -> str:
        """Handle the user's request to adjust the action plan"""
        system_prompt = """
        The user wants to adjust the action plan. Do necessary modifications based on user input. Make another variation of the plan.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = self.get_completion(messages)
        return response
