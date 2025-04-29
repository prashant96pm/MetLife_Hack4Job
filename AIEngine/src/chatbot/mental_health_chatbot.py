from data_classes.enums import ConversationStage
from agents.action_plan_agent import ActionPlanAgent
from agents.base_agent import Agent
from agents.closing_agent import ClosingAgent
from agents.empathetic_agent import EmpatheticAgent
from agents.handshake_agent import HandshakeAgent
from agents.issue_analysis_agent import IssueAnalysisAgent
from agents.mood_analysis_agent import MoodAnalysisAgent
from agents.tool_agent import ToolSuggestionAgent
from typing import Dict, Tuple
from data_classes.tool import Tool

class MentalHealthChatbot:
    def __init__(self, api_token):
        self.api_token = api_token
        self.conversation_history = []
        self.current_stage = ConversationStage.INITIAL_HANDSHAKE
        self.context = {
            "conversation_history": [],
            "handshake_attempts": 0,
            "mood_analysis_attempts": 0,
            "issue_analysis_attempts": 0,
            "empathy_attempts": 0,
            "tool_suggestion_attempts": 0,
            "action_plan_attempts": 0
        }
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agents
        self.agents = {
            ConversationStage.INITIAL_HANDSHAKE: HandshakeAgent(api_token),
            ConversationStage.MOOD_ANALYSIS: MoodAnalysisAgent(api_token),
            ConversationStage.UNDERSTANDING_ISSUE: IssueAnalysisAgent(api_token),
            ConversationStage.EMPATHETIC_CONVERSATION: EmpatheticAgent(api_token),
            ConversationStage.TOOL_SUGGESTION: ToolSuggestionAgent(api_token, self.tools),
            ConversationStage.PLAN_OF_ACTION: ActionPlanAgent(api_token),
            ConversationStage.CLOSING: ClosingAgent(api_token)
        }
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        return {
            "breathing_exercise": Tool(
                "Breathing Exercise",
                "A guided breathing exercise to reduce stress and anxiety",
            ),
            "gratitude_journal": Tool(
                "Gratitude Journal",
                "A digital journal to note things you're grateful for",
            ),
            "music_recommendation": Tool(
                "Music Recommendation",
                "Calming music recommendations based on mood",
            ),
            "mindfulness_meditation": Tool(
                "Mindfulness Meditation",
                "A short guided mindfulness meditation",
            ),
            "thought_reframing": Tool(
                "Thought Reframing",
                "Tool to help reframe negative thoughts into positive ones",
            ),
            "notepad": Tool(
                "Notepad",
                "Open a notepad to write down thoughts",
            ),
            "body_scan": Tool(
                "Body Scan Relaxation",
                "A guided body scan to release tension",
            ),
            "positive_affirmations": Tool(
                "Positive Affirmations",
                "List of positive affirmations for self-encouragement",
            )
        }
    
    def process_user_input(self, user_input: str) -> str:
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.context["conversation_history"] = self.conversation_history.copy()
            
            # Log the current stage
            print(f"Current stage: {self.current_stage.name}")
            
            # Process with appropriate agent
            current_agent = self.agents[self.current_stage]
            
            # Increment attempt counter for current stage
            stage_key = f"{self.current_stage.name.lower()}_attempts"
            self.context[stage_key] = self.context.get(stage_key, 0) + 1
            
            # Get response from agent
            response, updated_context, should_transition = current_agent.process(user_input, self.context)
            
            # Update context
            self.context.update(updated_context)
            
            # Handle transition if needed
            if should_transition:
                next_stage = self._get_next_stage(self.current_stage)
                print(f"\n[Stage Complete: {self.current_stage.name} → {next_stage.name}]")
                self.current_stage = next_stage
                if self.current_stage == ConversationStage.CLOSING:
                    self.context["closing_complete"] = True
            
            # Add chatbot response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            self.context["conversation_history"] = self.conversation_history.copy()
            
            return response
            
        except Exception as e:
            print(f"Error in process_user_input: {e}")
            return "I apologize, but I encountered an error. Could you please try again?"
    
    def _get_next_stage(self, current_stage: ConversationStage) -> ConversationStage:
        """Get the next conversation stage in the sequence."""
        stage_sequence = {
            ConversationStage.INITIAL_HANDSHAKE: ConversationStage.MOOD_ANALYSIS,
            ConversationStage.MOOD_ANALYSIS: ConversationStage.UNDERSTANDING_ISSUE,
            ConversationStage.UNDERSTANDING_ISSUE: ConversationStage.EMPATHETIC_CONVERSATION,
            ConversationStage.EMPATHETIC_CONVERSATION: ConversationStage.TOOL_SUGGESTION,
            ConversationStage.TOOL_SUGGESTION: ConversationStage.PLAN_OF_ACTION,
            ConversationStage.PLAN_OF_ACTION: ConversationStage.CLOSING,
            ConversationStage.CLOSING: ConversationStage.CLOSING  # Stay in closing
        }
        return stage_sequence.get(current_stage, ConversationStage.CLOSING)
    
    # Tool functions - these would be implemented with actual functionality
    def breathing_exercise(self) -> str:
        print("Guiding user through breathing exercise...")
        return "success"
    
    def gratitude_journal(self) -> str:
        print("Opening gratitude journal...")
        return "success"
    
    def music_recommendation(self) -> str:
        print("Recommending calming music...")
        return "success"
    
    def mindfulness_meditation(self) -> str:
        print("Starting mindfulness meditation...")
        return "success"
    
    def thought_reframing(self) -> str:
        print("Guiding through thought reframing...")
        return "success"
    
    def open_notepad(self) -> str:
        print("Opening notepad...")
        return "success"
    
    def body_scan(self) -> str:
        print("Guiding through body scan...")
        return "success"
    
    def positive_affirmations(self) -> str:
        print("Sharing positive affirmations...")
        return "success"
