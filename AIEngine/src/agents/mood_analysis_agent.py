from agents.base_agent import Agent
from typing import Dict, Tuple
import json

class MoodAnalysisAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Mood Analysis Agent", api_token)
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Analyze user's mood and emotional state.
        Returns: (response, updated_context, should_transition)
        """
        # Update conversation history with latest input
        if "mood_analysis_inputs" not in context:
            context["mood_analysis_inputs"] = []
        context["mood_analysis_inputs"].append(user_input)
        
        # Analyze mood based on all available information
        mood_analysis = self.analyze_mood(context)
        
        # Store mood analysis results
        context["mood_details"] = mood_analysis
        if "mood" in mood_analysis:
            context["user_mood"] = mood_analysis["mood"]
            print(context["user_mood"])
        
        # Evaluate if we have high confidence in mood analysis to transition
        transition_evaluation = self.evaluate_transition(mood_analysis, context)
        should_transition = transition_evaluation.get("should_transition", False)
        
        if should_transition:
            # Prepare for transition but let the coordinator handle it
            return transition_evaluation.get("transition_message", "I think I'm getting a sense of how you're feeling. Let's explore what might be causing this."), context, True
        
        # Generate a follow-up question to better understand mood
        system_prompt = """
        You are a mental health assistant focusing on understanding the user's emotional state.
        Based on what you know so far, ask a thoughtful follow-up question to better understand 
        their feelings. Be empathetic and show genuine interest in their wellbeing.
        """
        
        mood_context = f"Current mood analysis: {json.dumps(mood_analysis)}" if mood_analysis else ""
        
        messages = [{"role": "user", "content": user_input}]
        if context.get("conversation_history"):
            messages = context.get("conversation_history").copy()
        
        messages.insert(0, {"role": "system", "content": f"{system_prompt}\n\n{mood_context}"})
        
        response = self.get_completion(messages)
        return response, context, False
    
    def analyze_mood(self, context: Dict) -> Dict:
        system_prompt = """
        Analyze the user's responses to determine their current emotional state.
        Identify the primary mood and provide justification based on their messages.
        Be attentive to subtle emotional cues and professional context.
        """
        
        format_instruction = """
        {
            "mood": "happy|stressed|anxious|angry|sad|neutral|tired|overwhelmed",
            "confidence": "number between 0-10",
            "indicators": ["array of text clues that indicate this mood"],
            "response": "empathetic response acknowledging their mood and asking for more details"
        }
        """
        
        # Combine all relevant inputs
        all_inputs = []
        if context.get("conversation_history"):
            for msg in context.get("conversation_history"):
                if msg["role"] == "user":
                    all_inputs.append(msg["content"])
        
        if context.get("mood_analysis_inputs"):
            all_inputs.extend(context.get("mood_analysis_inputs"))
        
        input_text = "\n".join(all_inputs)
        
        messages = [
            {"role": "user", "content": f"Analyze these responses to determine mood: {input_text}"}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
    
    def evaluate_transition(self, mood_analysis: Dict, context: Dict) -> Dict:
        # Use confidence score from mood analysis as primary factor
        confidence = float(mood_analysis.get("confidence", 0))
        attempts = context.get("mood_analysis_attempts", 0)
        
        system_prompt = """
        Determine if we have enough information about the user's mood to transition to understanding
        the underlying issues. Consider:
        1. The confidence level in the mood assessment
        2. How many mood-focused exchanges we've had
        3. If the user has started discussing causes/issues already
        """
        
        format_instruction = """
        {
            "should_transition": true|false,
            "reasoning": "explanation for the decision",
            "transition_message": "a smooth transition message if should_transition is true"
        }
        """
        
        messages = [
            {"role": "user", "content": f"Mood analysis: {json.dumps(mood_analysis)}\nNumber of mood exchanges: {attempts + 1}\n\nShould we transition to understanding underlying issues?"}
        ]
        
        result = self.get_structured_completion(messages, system_prompt, format_instruction)
        
        # Override with confidence threshold as fallback
        if not result.get("should_transition") and (confidence >= 7 or attempts >= 3):
            result["should_transition"] = True
            result["reasoning"] = f"Overriding because confidence={confidence} or attempts={attempts+1}"
            
            if not result.get("transition_message"):
                name_prefix = f", {context.get('user_name')}" if context.get('user_name') else ""
                mood = mood_analysis.get("mood", "")
                
                if mood in ["neutral", "happy"]:
                    result["transition_message"] = f"I understand{name_prefix}. Even though things seem {mood} overall, I'd like to explore if there are any workplace challenges you're facing."
                else:
                    result["transition_message"] = f"Thank you for sharing{name_prefix}. It sounds like you're feeling {mood}. Let's explore what might be contributing to that."
        
        return result
