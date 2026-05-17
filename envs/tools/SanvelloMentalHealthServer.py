
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class CheckIn(BaseModel):
    """Represents a daily mood check-in record."""
    check_in_id: str = Field(..., description="Unique identifier for this check-in")
    user_id: str = Field(..., description="User identifier")
    mood_rating: int = Field(..., ge=1, le=10, description="Mood rating 1-10")
    feelings: List[str] = Field(..., description="List of emotions")
    notes: str = Field(default="", description="Optional journal notes")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="ISO 8601 timestamp")

class Journey(BaseModel):
    """Represents a guided therapeutic program."""
    journey_id: str = Field(..., description="Unique journey identifier")
    title: str = Field(..., description="Journey title")
    description: str = Field(..., description="Journey description")
    category: str = Field(..., description="Mental health category")
    total_steps: int = Field(..., ge=1, description="Total steps in program")
    duration_weeks: int = Field(..., ge=1, description="Duration in weeks")
    techniques: List[str] = Field(..., description="CBT techniques used")
    clinical_approach: str = Field(..., description="Clinical methodology")

class Enrollment(BaseModel):
    """Represents user enrollment in a journey."""
    enrollment_id: str = Field(..., description="Unique enrollment identifier")
    user_id: str = Field(..., description="User identifier")
    journey_id: str = Field(..., description="Journey identifier")
    current_step: int = Field(..., ge=1, description="Current step number")
    progress_percent: float = Field(..., ge=0, le=100, description="Completion percentage")

class CopingTool(BaseModel):
    """Represents an evidence-based coping tool."""
    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool name")
    type: str = Field(..., description="Tool category")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    description: str = Field(..., description="Tool description")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    for_crisis: bool = Field(..., description="Suitable for crisis")

class CommunityGroup(BaseModel):
    """Represents a peer support community group."""
    group_id: str = Field(..., description="Unique group identifier")
    group_name: str = Field(..., description="Group display name")
    topic: str = Field(..., description="Group topic")
    member_count: int = Field(..., ge=0, description="Active member count")
    moderated: bool = Field(..., description="Has professional moderation")
    guidelines: str = Field(..., description="Community guidelines")

class SanvelloScenario(BaseModel):
    """Main scenario model for Sanvello mental health platform."""
    check_ins: Dict[str, CheckIn] = Field(default={}, description="All check-in records")
    journeys: Dict[str, Journey] = Field(default={}, description="Available journeys")
    enrollments: Dict[str, Enrollment] = Field(default={}, description="User enrollments")
    coping_tools: Dict[str, CopingTool] = Field(default={}, description="Available coping tools")
    community_groups: Dict[str, CommunityGroup] = Field(default={}, description="Community groups")
    user_check_in_history: Dict[str, List[str]] = Field(default={}, description="User check-in IDs")
    user_enrollments: Dict[str, List[str]] = Field(default={}, description="User enrollment IDs")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp")
    next_check_in_id: int = Field(default=1, ge=1, description="Next check-in ID counter")
    next_enrollment_id: int = Field(default=1, ge=1, description="Next enrollment ID counter")

Scenario_Schema = [CheckIn, Journey, Enrollment, CopingTool, CommunityGroup, SanvelloScenario]

# Section 2: Class
class SanvelloMentalHealthAPI:
    def __init__(self):
        """Initialize Sanvello API with empty state."""
        self.check_ins: Dict[str, CheckIn] = {}
        self.journeys: Dict[str, Journey] = {}
        self.enrollments: Dict[str, Enrollment] = {}
        self.coping_tools: Dict[str, CopingTool] = {}
        self.community_groups: Dict[str, CommunityGroup] = {}
        self.user_check_in_history: Dict[str, List[str]] = {}
        self.user_enrollments: Dict[str, List[str]] = {}
        self.current_time: str = ""
        self.next_check_in_id: int = 1
        self.next_enrollment_id: int = 1

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = SanvelloScenario(**scenario)
        self.check_ins = model.check_ins
        self.journeys = model.journeys
        self.enrollments = model.enrollments
        self.coping_tools = model.coping_tools
        self.community_groups = model.community_groups
        self.user_check_in_history = model.user_check_in_history
        self.user_enrollments = model.user_enrollments
        self.current_time = model.current_time
        self.next_check_in_id = model.next_check_in_id
        self.next_enrollment_id = model.next_enrollment_id

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "check_ins": {cid: ci.model_dump() for cid, ci in self.check_ins.items()},
            "journeys": {jid: j.model_dump() for jid, j in self.journeys.items()},
            "enrollments": {eid: e.model_dump() for eid, e in self.enrollments.items()},
            "coping_tools": {tid: t.model_dump() for tid, t in self.coping_tools.items()},
            "community_groups": {gid: g.model_dump() for gid, g in self.community_groups.items()},
            "user_check_in_history": self.user_check_in_history,
            "user_enrollments": self.user_enrollments,
            "current_time": self.current_time,
            "next_check_in_id": self.next_check_in_id,
            "next_enrollment_id": self.next_enrollment_id
        }

    def daily_check_in(self, user_id: str, mood_rating: int, feelings: List[str], notes: str) -> dict:
        """Record daily mood check-in."""
        check_in_id = f"ci_{self.next_check_in_id}"
        self.next_check_in_id += 1
        
        check_in = CheckIn(
            check_in_id=check_in_id,
            user_id=user_id,
            mood_rating=mood_rating,
            feelings=feelings,
            notes=notes,
            timestamp=self.current_time
        )
        self.check_ins[check_in_id] = check_in
        
        if user_id not in self.user_check_in_history:
            self.user_check_in_history[user_id] = []
        self.user_check_in_history[user_id].append(check_in_id)
        
        user_history = [self.check_ins[cid] for cid in self.user_check_in_history[user_id]]
        avg_mood = sum(ci.mood_rating for ci in user_history) / len(user_history)
        insights = f"Your average mood is {avg_mood:.1f}. "
        if mood_rating < avg_mood:
            insights += "Today's mood is below your average."
        else:
            insights += "Today's mood is at or above your average."
        
        recommended_tools = []
        if mood_rating <= 4:
            recommended_tools = ["breathing", "grounding"]
        elif mood_rating <= 7:
            recommended_tools = ["meditation", "journaling"]
        else:
            recommended_tools = ["visualization"]
        
        journey_suggestion = "anxiety" if "anxious" in feelings else "stress"
        
        return {
            "check_in_id": check_in_id,
            "timestamp": self.current_time,
            "insights": insights,
            "recommended_tools": recommended_tools,
            "guided_journey_suggestion": journey_suggestion
        }

    def get_guided_journeys(self, category: Optional[str]) -> dict:
        """Retrieve guided therapeutic programs."""
        filtered = [j for j in self.journeys.values() if not category or j.category == category]
        return {
            "journeys": [
                {
                    "journey_id": j.journey_id,
                    "title": j.title,
                    "description": j.description,
                    "category": j.category,
                    "total_steps": j.total_steps,
                    "duration_weeks": j.duration_weeks,
                    "techniques": j.techniques,
                    "clinical_approach": j.clinical_approach
                }
                for j in filtered
            ]
        }

    def start_journey(self, user_id: str, journey_id: str) -> dict:
        """Enroll user in a guided program."""
        journey = self.journeys[journey_id]
        enrollment_id = f"en_{self.next_enrollment_id}"
        self.next_enrollment_id += 1
        
        enrollment = Enrollment(
            enrollment_id=enrollment_id,
            user_id=user_id,
            journey_id=journey_id,
            current_step=1,
            progress_percent=0.0
        )
        self.enrollments[enrollment_id] = enrollment
        
        if user_id not in self.user_enrollments:
            self.user_enrollments[user_id] = []
        self.user_enrollments[user_id].append(enrollment_id)
        
        return {
            "enrollment_id": enrollment_id,
            "current_step": 1,
            "progress_percent": 0.0,
            "weekly_goal": {"week": 1, "goal": f"Complete step 1 of {journey.title}"},
            "next_activity": {"step": 1, "title": "Introduction", "description": "Begin your journey"}
        }

    def get_coping_tools(self, tool_type: Optional[str], situation: Optional[str]) -> dict:
        """Retrieve evidence-based coping tools."""
        filtered = [
            t for t in self.coping_tools.values()
            if (not tool_type or t.type == tool_type)
        ]
        return {
            "tools": [
                {
                    "tool_id": t.tool_id,
                    "name": t.name,
                    "type": t.type,
                    "duration_minutes": t.duration_minutes,
                    "description": t.description,
                    "instructions": t.instructions,
                    "for_crisis": t.for_crisis
                }
                for t in filtered
            ]
        }

    def track_progress(self, user_id: str, metric_type: Optional[str]) -> dict:
        """Retrieve comprehensive progress tracking."""
        user_check_ins = [self.check_ins[cid] for cid in self.user_check_in_history.get(user_id, [])]
        total_check_ins = len(user_check_ins)
        current_streak = min(total_check_ins, 7)
        improvement_score = sum(ci.mood_rating for ci in user_check_ins) / max(total_check_ins, 1)
        
        weekly_avg = [0.0] * 7
        if user_check_ins:
            for i in range(7):
                weekly_avg[i] = sum(ci.mood_rating for ci in user_check_ins[-7:]) / len(user_check_ins[-7:])
        
        best_day = "Monday"
        common_triggers = ["work stress", "sleep issues"]
        
        user_enroll = [self.enrollments[eid] for eid in self.user_enrollments.get(user_id, [])]
        journey_progress = [
            {
                "enrollment_id": e.enrollment_id,
                "journey_id": e.journey_id,
                "current_step": e.current_step,
                "progress_percent": e.progress_percent
            }
            for e in user_enroll
        ]
        
        return {
            "overview": {
                "total_check_ins": total_check_ins,
                "current_streak": current_streak,
                "improvement_score": improvement_score
            },
            "mood_trends": {
                "weekly_average": weekly_avg,
                "best_day": best_day,
                "common_triggers": common_triggers
            },
            "journey_progress": journey_progress,
            "weekly_report": {
                "summary": "You've made progress this week",
                "wins": ["Consistent check-ins", "Started new journey"],
                "areas_for_growth": ["Try more coping tools", "Engage with community"]
            }
        }

    def join_community_group(self, group_topic: str) -> dict:
        """Join anonymous peer support community group."""
        group = next((g for g in self.community_groups.values() if g.topic == group_topic), None)
        return {
            "group_id": group.group_id,
            "group_name": group.group_name,
            "member_count": group.member_count,
            "moderated": group.moderated,
            "recent_discussions": [
                {"thread_id": "t1", "title": "Coping with morning anxiety", "replies": 12},
                {"thread_id": "t2", "title": "Sleep tips that worked for me", "replies": 8}
            ],
            "guidelines": group.guidelines
        }

# Section 3: MCP Tools
mcp = FastMCP(name="SanvelloMentalHealthServer")
api = SanvelloMentalHealthAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Sanvello API.

    Args:
        scenario (dict): Scenario dictionary matching SanvelloScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Sanvello state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def daily_check_in(user_id: str, mood_rating: int, feelings: list, notes: str = "") -> dict:
    """
    Record daily mood check-in with CBT-based assessment.

    Args:
        user_id (str): The unique identifier of the user account.
        mood_rating (int): Mood rating on a scale from 1 (lowest) to 10 (highest).
        feelings (list): List of selected emotions describing current state.
        notes (str): [Optional] Journal entry or additional notes about the day.

    Returns:
        check_in_id (str): Unique identifier for this check-in record.
        timestamp (str): ISO 8601 timestamp when the check-in was recorded.
        insights (str): Pattern insights derived from historical mood data.
        recommended_tools (list): List of suggested coping tools.
        guided_journey_suggestion (str): Recommended therapeutic program.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if not isinstance(feelings, list) or not feelings:
            raise ValueError("feelings must be a non-empty list")
        return api.daily_check_in(user_id, mood_rating, feelings, notes)
    except Exception as e:
        raise e

@mcp.tool()
def get_guided_journeys(category: str = None) -> dict:
    """
    Retrieve structured CBT-based therapeutic programs.

    Args:
        category (str): [Optional] Filter by mental health category.

    Returns:
        journeys (list): List of available guided therapeutic journeys.
    """
    try:
        return api.get_guided_journeys(category)
    except Exception as e:
        raise e

@mcp.tool()
def start_journey(user_id: str, journey_id: str) -> dict:
    """
    Enroll user in a guided mental health program.

    Args:
        user_id (str): The unique identifier of the user account.
        journey_id (str): Unique identifier for the therapeutic program to enroll in.

    Returns:
        enrollment_id (str): Unique identifier for this enrollment instance.
        current_step (int): Current step number in the program.
        progress_percent (float): Completion percentage of the journey.
        weekly_goal (dict): Structured goal for the current week.
        next_activity (dict): Details of the next recommended activity.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if not journey_id or not isinstance(journey_id, str):
            raise ValueError("journey_id must be a non-empty string")
        if journey_id not in api.journeys:
            raise ValueError(f"Journey {journey_id} not found")
        return api.start_journey(user_id, journey_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_coping_tools(tool_type: str = None, situation: str = None) -> dict:
    """
    Retrieve evidence-based coping tools for immediate relief.

    Args:
        tool_type (str): [Optional] Filter by tool category.
        situation (str): [Optional] Filter by specific situation.

    Returns:
        tools (list): List of available coping tools matching the filters.
    """
    try:
        return api.get_coping_tools(tool_type, situation)
    except Exception as e:
        raise e

@mcp.tool()
def track_progress(user_id: str, metric_type: str = None) -> dict:
    """
    Retrieve comprehensive progress tracking across all metrics.

    Args:
        user_id (str): The unique identifier of the user account.
        metric_type (str): [Optional] Filter for specific metrics.

    Returns:
        overview (dict): High-level summary of user engagement and wellness.
        mood_trends (dict): Analysis of mood patterns over time.
        journey_progress (list): Progress details for all enrolled programs.
        weekly_report (dict): Weekly reflection and progress summary.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        return api.track_progress(user_id, metric_type)
    except Exception as e:
        raise e

@mcp.tool()
def join_community_group(group_topic: str) -> dict:
    """
    Join anonymous peer support community groups.

    Args:
        group_topic (str): Topic of the support group.

    Returns:
        group_id (str): Unique identifier for the community group.
        group_name (str): Display name of the support group.
        member_count (int): Current number of active members.
        moderated (bool): Whether the group has professional moderation.
        recent_discussions (list): List of recent discussion threads.
        guidelines (str): Community guidelines and participation rules.
    """
    try:
        if not group_topic or not isinstance(group_topic, str):
            raise ValueError("group_topic must be a non-empty string")
        group = next((g for g in api.community_groups.values() if g.topic == group_topic), None)
        if not group:
            raise ValueError(f"Community group with topic {group_topic} not found")
        return api.join_community_group(group_topic)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
