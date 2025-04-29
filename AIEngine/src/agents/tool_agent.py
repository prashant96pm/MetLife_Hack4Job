from agents.base_agent import Agent
from typing import Dict, Tuple
from data_classes.tool import Tool

class ToolSuggestionAgent(Agent):
    def __init__(self, api_token: str, tools: Dict[str, Tool]):
        super().__init__("Tool Suggestion Agent", api_token)
        self.tools = tools
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Suggest appropriate tools and handle user acceptance.
        Returns: (response, updated_context, should_transition)
        """
        # If this is first time in this state, suggest tool
        if context.get("tool_suggestion_attempts", 0) == 0:
            tool_suggestion = self.suggest_tool(context)
            context["recommended_tool"] = tool_suggestion.get("recommended_tool", "breathing_exercise")
            context["tool_suggestion_attempts"] = 1
            return tool_suggestion.get("introduction", f"I'd like to suggest a {context['recommended_tool'].replace('_', ' ')} that might help you right now. Would you like to try it?"), context, False
        
        # Check for user acceptance
        acceptance_analysis = self.check_user_acceptance(user_input)
        user_accepted = acceptance_analysis.get("user_accepted", False)
        
        if user_accepted:
            tool_name = context.get("recommended_tool")
            context["recommended_tool"] = tool_name
            print(f"\n[Tool Suggested: {tool_name}]")
            
            # Transition to Plan of Action
            return "I hope that will be helpful for you. Now, let's think about some practical steps you can take going forward.", context, True
 
            
        # User didn't accept - try once more or move on
        context["tool_suggestion_attempts"] = context.get("tool_suggestion_attempts", 0) + 1
        
        if context.get("tool_suggestion_attempts", 0) >= 2:
            # Move to Plan of Action
            return "That's completely fine. Let's focus on creating a plan that works for you instead.", context, True
        
        # Try a different tool
        alternate_tools = [t for t in self.tools.keys() if t != context.get("recommended_tool")]
        if alternate_tools:
            new_tool = random.choice(alternate_tools)
            context["recommended_tool"] = new_tool
            return f"That's fine. Perhaps a {new_tool.replace('_', ' ')} might be more helpful? It could help you by {self.tools[new_tool].description}. Would you like to try it?", context, False
        else:
            # Move to Plan of Action
            return "I understand. Let's focus on creating a plan that works for you instead.", context, True
    
    def suggest_tool(self, context: Dict) -> Dict:
        system_prompt = """
        Based on the user's mood and issues, suggest an appropriate mental wellbeing tool
        that could help them in this moment. Choose from available tools and explain
        briefly how it might help with their specific situation.
        """
        
        format_instruction = """
        {
            "recommended_tool": "breathing_exercise|gratitude_journal|music_recommendation|mindfulness_meditation|thought_reframing|notepad|body_scan|positive_affirmations",
            "reason": "why this tool might help",
            "introduction": "gentle introduction to suggest the tool"
        }
        """
        
        mood_context = f"User's mood: {context.get('user_mood', 'unknown')}"
        issue_context = f"Primary issue: {context.get('underlying_issue', 'unknown')}"
        tools_list = ", ".join(self.tools.keys())
        
        messages = [
            {"role": "user", "content": f"Based on this context:\n{mood_context}\n{issue_context}\n\nAvailable tools: {tools_list}\n\nSuggest an appropriate tool to help the user."}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
    
    def check_user_acceptance(self, user_input: str) -> Dict:
        system_prompt = """
        Determine if the user is interested in trying the suggested tool. 
        Look for affirmative responses like 'yes', 'okay', 'sure', etc.
        """
        
        format_instruction = """
        {
            "user_accepted": true|false,
            "confidence": "number between 0-10"
        }
        """
        
        messages = [
            {"role": "user", "content": f"Did the user accept the tool suggestion in this response: '{user_input}'"}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
