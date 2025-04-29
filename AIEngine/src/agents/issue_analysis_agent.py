from agents.base_agent import Agent
from typing import Dict, Tuple
import json

class IssueAnalysisAgent(Agent):
    def __init__(self, api_token: str):
        super().__init__("Issue Analysis Agent", api_token)
    
    def process(self, user_input: str, context: Dict) -> Tuple[str, Dict, bool]:
        """
        Analyze underlying issues based on user information.
        Returns: (response, updated_context, should_transition)
        """
        # Update issue analysis inputs
        if "issue_analysis_inputs" not in context:
            context["issue_analysis_inputs"] = []
        context["issue_analysis_inputs"].append(user_input)
        
        # Make sure we have an attempts counter and increment it
        if "issue_analysis_attempts" not in context:
            context["issue_analysis_attempts"] = 1
        else:
            context["issue_analysis_attempts"] += 1
        
        # If this is first attempt in this state, do initial issue analysis
        if context["issue_analysis_attempts"] == 1:
            issue_analysis = self.identify_underlying_issues(context)
            context["issue_details"] = issue_analysis
            if "primary_issue" in issue_analysis:
                context["underlying_issue"] = issue_analysis["primary_issue"]
            
            # Return the follow-up question from issue analysis
            return issue_analysis.get("follow_up_question", "Can you tell me more about what's been challenging for you at work recently?"), context, False
        
        # After the first attempt, check if we should force transition due to max attempts
        if context["issue_analysis_attempts"] >= 3:  # Force after 3 total attempts (initial + 2 follow-ups)
            # Add final issue analysis based on all data
            updated_issue_analysis = self.identify_underlying_issues(context)
            context["issue_details"] = updated_issue_analysis
            if "primary_issue" in updated_issue_analysis:
                context["underlying_issue"] = updated_issue_analysis["primary_issue"]
            
            return "Thank you for sharing those details. I think I understand what you're going through now.", context, True
        
        # If not forcing transition, evaluate transition normally
        transition_evaluation = self.evaluate_transition(user_input, context)
        should_transition = transition_evaluation.get("should_transition", False)
        
        if should_transition:
            # Add one final issue analysis based on all data
            updated_issue_analysis = self.identify_underlying_issues(context)
            context["issue_details"] = updated_issue_analysis
            if "primary_issue" in updated_issue_analysis:
                context["underlying_issue"] = updated_issue_analysis["primary_issue"]
            
            return transition_evaluation.get("transition_message", "Thank you for sharing those details. Let's take a moment to reflect on what you're experiencing."), context, True
        
        # Still in issue analysis, ask a targeted follow-up
        system_prompt = """
        You are a mental health assistant for working professionals. Based on what you know
        about the user's mood and potential issues, ask a targeted follow-up question to
        better understand the specific challenges they're facing. Be empathetic and supportive.
        """
        
        mood_context = f"User's mood: {context.get('user_mood', 'unknown')}"
        issue_context = f"Potential issues: {', '.join(context.get('issue_details', {}).get('potential_issues', ['unknown']))}" if context.get('issue_details') else "Potential issues: unknown"
        
        messages = context.get("conversation_history", []).copy()
        messages.insert(0, {"role": "system", "content": f"{system_prompt}\n\nContext:\n{mood_context}\n{issue_context}"})
        
        response = self.get_completion(messages)
        return response, context, False

    def identify_underlying_issues(self, context: Dict) -> Dict:
        system_prompt = """
        Based on the user's responses, identify potential underlying workplace issues
        that might be affecting their mental wellbeing. Formulate a thoughtful question
        to explore the most likely issue while being supportive and non-judgmental.
        """
        
        format_instruction = """
        {
            "potential_issues": ["array of possible issues"],
            "primary_issue": "work_stress|work_life_balance|colleague_conflict|burnout|career_uncertainty|time_management|perfectionism|imposter_syndrome|workplace_anxiety|other",
            "follow_up_question": "question to explore the primary issue",
            "rationale": "why you think this is the primary issue"
        }
        """
        
        # Combine all relevant inputs
        all_inputs = []
        if context.get("conversation_history"):
            for msg in context.get("conversation_history"):
                if msg["role"] == "user":
                    all_inputs.append(msg["content"])
        
        if context.get("issue_analysis_inputs"):
            all_inputs.extend(context.get("issue_analysis_inputs"))
        
        input_text = "\n".join(all_inputs)
        mood_context = f"The user's identified mood is: {context.get('user_mood', 'unknown')}"
        
        messages = [
            {"role": "user", "content": f"{mood_context}\nAnalyze these responses to identify underlying issues: {input_text}"}
        ]
        
        return self.get_structured_completion(messages, system_prompt, format_instruction)
    
    def evaluate_transition(self, user_input: str, context: Dict) -> Dict:
        attempts = context.get("issue_analysis_attempts", 0)
        
        system_prompt = """
        Determine if we have enough information about the user's underlying issues to transition 
        to an empathetic conversation. Consider:
        1. Whether we've identified a primary issue with good confidence
        2. If the user has shared enough about their specific challenges
        3. How many issue-focused exchanges we've had
        """
        
        format_instruction = """
        {
            "should_transition": true|false,
            "reasoning": "explanation for the decision",
            "transition_message": "a smooth transition message if should_transition is true"
        }
        """
        
        issue_details = json.dumps(context.get("issue_details", {}))
        
        messages = [
            {"role": "user", "content": f"Issue analysis: {issue_details}\nLatest user input: {user_input}\nNumber of issue exchanges: {attempts + 1}\n\nShould we transition to empathetic conversation?"}
        ]
        
        result = self.get_structured_completion(messages, system_prompt, format_instruction)
        
        return result
