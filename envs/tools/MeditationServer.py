
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Meditation(BaseModel):
    """Represents a meditation session."""
    meditation_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique meditation identifier")
    title: str = Field(..., description="Meditation title")
    description: str = Field(..., description="Meditation description")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    category: str = Field(..., description="Category: sleep, stress, focus, anxiety, beginner, loving_kindness")
    level: str = Field(..., description="Experience level: beginner, intermediate, advanced")
    instructor: str = Field(..., description="Instructor name")
    technique: str = Field(..., description="Technique: mindfulness, body_scan, breathing, visualization")
    audio_url: str = Field(..., description="Audio streaming URL")
    background_music: bool = Field(..., description="Has background music")

class SleepContent(BaseModel):
    """Represents sleep aid content."""
    content_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique content identifier")
    title: str = Field(..., description="Content title")
    type: str = Field(..., description="Type: story, sound, music, meditation")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    narrator: str = Field(..., description="Narrator name")
    description: str = Field(..., description="Content description")
    sleep_aids: List[str] = Field(default=[], description="Ambient sound elements")
    rating: float = Field(..., ge=0, le=5, description="User rating")
    play_count: int = Field(..., ge=0, description="Total plays")

class BreathingExercise(BaseModel):
    """Represents a breathing exercise."""
    exercise_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique exercise identifier")
    name: str = Field(..., description="Exercise name")
    goal: str = Field(..., description="Goal: relax, energize, sleep, focus, anxiety_relief")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes")
    pattern: str = Field(..., description="Breathing pattern")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    visual_guide: bool = Field(..., description="Has visual guide")
    haptic_feedback: bool = Field(..., description="Has haptic feedback")

class MeditationSession(BaseModel):
    """Represents an active meditation session."""
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique session identifier")
    meditation_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Meditation identifier")
    user_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="User identifier")
    started_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Start timestamp ISO 8601")
    completed: bool = Field(default=False, description="Session completed")
    completion_percent: float = Field(default=0, ge=0, le=100, description="Completion percentage")
    notes: Optional[str] = Field(default=None, description="Reflection notes")

class UserStats(BaseModel):
    """Represents user meditation statistics."""
    user_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="User identifier")
    total_sessions: int = Field(default=0, ge=0, description="Total sessions completed")
    total_minutes: int = Field(default=0, ge=0, description="Total meditation minutes")
    current_streak: int = Field(default=0, ge=0, description="Current daily streak")
    longest_streak: int = Field(default=0, ge=0, description="Longest daily streak")
    favorite_category: str = Field(default="", description="Most practiced category")
    milestones_achieved: List[str] = Field(default=[], description="Achieved milestones")
    weekly_goal_minutes: int = Field(default=0, ge=0, description="Weekly goal in minutes")

class MeditationScenario(BaseModel):
    """Main scenario model for meditation server."""
    meditations: Dict[str, Meditation] = Field(default={}, description="All meditation content")
    sleep_content: Dict[str, SleepContent] = Field(default={}, description="All sleep content")
    breathing_exercises: Dict[str, BreathingExercise] = Field(default={}, description="All breathing exercises")
    active_sessions: Dict[str, MeditationSession] = Field(default={}, description="Active meditation sessions")
    user_stats: Dict[str, UserStats] = Field(default={}, description="User statistics")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp ISO 8601")

Scenario_Schema = [Meditation, SleepContent, BreathingExercise, MeditationSession, UserStats, MeditationScenario]

# Section 2: Class
class MeditationAPI:
    def __init__(self):
        """Initialize meditation API with empty state."""
        self.meditations: Dict[str, Meditation] = {}
        self.sleep_content: Dict[str, SleepContent] = {}
        self.breathing_exercises: Dict[str, BreathingExercise] = {}
        self.active_sessions: Dict[str, MeditationSession] = {}
        self.user_stats: Dict[str, UserStats] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MeditationScenario(**scenario)
        self.meditations = model.meditations
        self.sleep_content = model.sleep_content
        self.breathing_exercises = model.breathing_exercises
        self.active_sessions = model.active_sessions
        self.user_stats = model.user_stats
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "meditations": {mid: m.model_dump() for mid, m in self.meditations.items()},
            "sleep_content": {cid: c.model_dump() for cid, c in self.sleep_content.items()},
            "breathing_exercises": {eid: e.model_dump() for eid, e in self.breathing_exercises.items()},
            "active_sessions": {sid: s.model_dump() for sid, s in self.active_sessions.items()},
            "user_stats": {uid: u.model_dump() for uid, u in self.user_stats.items()},
            "current_time": self.current_time
        }

    def get_meditation_library(self, category: Optional[str], duration: Optional[int], experience_level: Optional[str]) -> dict:
        """Browse and filter meditation library."""
        results = []
        for m in self.meditations.values():
            if category and m.category != category:
                continue
            if duration and m.duration_minutes > duration:
                continue
            if experience_level and m.level != experience_level:
                continue
            results.append({
                "meditation_id": m.meditation_id,
                "title": m.title,
                "description": m.description,
                "duration_minutes": m.duration_minutes,
                "category": m.category,
                "level": m.level,
                "instructor": m.instructor,
                "technique": m.technique,
                "audio_url": m.audio_url,
                "background_music": m.background_music
            })
        return {"meditations": results}

    def get_daily_meditation(self, user_id: str, mood: Optional[str]) -> dict:
        """Get personalized daily meditation recommendation."""
        for m in self.meditations.values():
            return {
                "meditation_id": m.meditation_id,
                "title": m.title,
                "description": m.description,
                "duration": m.duration_minutes,
                "recommended_for": f"Based on mood: {mood}" if mood else "Daily practice",
                "theme": m.category,
                "new_content": True,
                "series_info": {}
            }
        return {}

    def get_sleep_content_list(self, content_type: Optional[str], narrator: Optional[str]) -> dict:
        """Browse sleep content."""
        results = []
        for c in self.sleep_content.values():
            if content_type and content_type != "all" and c.type != content_type:
                continue
            if narrator and c.narrator != narrator:
                continue
            results.append({
                "content_id": c.content_id,
                "title": c.title,
                "type": c.type,
                "duration_minutes": c.duration_minutes,
                "narrator": c.narrator,
                "description": c.description,
                "sleep_aids": c.sleep_aids,
                "rating": c.rating,
                "play_count": c.play_count
            })
        return {"sleep_content": results}

    def get_breathing_exercises_list(self, goal: Optional[str], duration: Optional[int]) -> dict:
        """Get breathing exercises."""
        results = []
        for e in self.breathing_exercises.values():
            if goal and e.goal != goal:
                continue
            if duration and e.duration_minutes > duration:
                continue
            results.append({
                "exercise_id": e.exercise_id,
                "name": e.name,
                "goal": e.goal,
                "duration_minutes": e.duration_minutes,
                "pattern": e.pattern,
                "instructions": e.instructions,
                "visual_guide": e.visual_guide,
                "haptic_feedback": e.haptic_feedback
            })
        return {"exercises": results}

    def start_meditation_session(self, meditation_id: str, user_id: str) -> dict:
        """Begin tracked meditation session."""
        m = self.meditations[meditation_id]
        session_id = f"session_{user_id}_{meditation_id}_{len(self.active_sessions)}"
        session = MeditationSession(
            session_id=session_id,
            meditation_id=meditation_id,
            user_id=user_id,
            started_at=self.current_time
        )
        self.active_sessions[session_id] = session
        return {
            "session_id": session_id,
            "started_at": self.current_time,
            "streaming_url": m.audio_url,
            "progress_tracking": True,
            "allow_background_play": True,
            "completion_reward": "Mindfulness points"
        }

    def log_meditation_completion(self, session_id: str, completion_percent: float, notes: Optional[str]) -> dict:
        """Record meditation session completion."""
        session = self.active_sessions[session_id]
        session.completed = True
        session.completion_percent = completion_percent
        session.notes = notes
        
        user_id = session.user_id
        if user_id not in self.user_stats:
            self.user_stats[user_id] = UserStats(user_id=user_id)
        
        stats = self.user_stats[user_id]
        stats.total_sessions += 1
        stats.current_streak += 1
        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak
        
        m = self.meditations[session.meditation_id]
        stats.total_minutes += int(m.duration_minutes * completion_percent / 100)
        
        weekly_progress = (stats.total_minutes / stats.weekly_goal_minutes * 100) if stats.weekly_goal_minutes > 0 else 0
        
        return {
            "logged": True,
            "stats_updated": {
                "total_sessions": stats.total_sessions,
                "current_streak": stats.current_streak,
                "total_minutes": stats.total_minutes,
                "weekly_goal_progress": weekly_progress
            },
            "insights": "Great progress on your mindfulness journey",
            "next_recommendation": {}
        }

    def get_meditation_stats(self, user_id: str, period: Optional[str]) -> dict:
        """Retrieve meditation practice statistics."""
        stats = self.user_stats[user_id]
        mindfulness_score = min(100, stats.total_sessions * 5 + stats.current_streak * 10)
        avg_length = stats.total_minutes / stats.total_sessions if stats.total_sessions > 0 else 0
        
        return {
            "total_sessions": stats.total_sessions,
            "total_minutes": stats.total_minutes,
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "favorite_category": stats.favorite_category,
            "average_session_length": avg_length,
            "milestones_achieved": stats.milestones_achieved,
            "mindfulness_score": mindfulness_score
        }

# Section 3: MCP Tools
mcp = FastMCP(name="MeditationServer")
api = MeditationAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the meditation API.

    Args:
        scenario (dict): Scenario dictionary matching MeditationScenario schema.

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
    Save current meditation state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_meditation_library(category: str = None, duration: int = None, experience_level: str = None) -> dict:
    """
    Browse and filter the meditation library by category, duration, and experience level.

    Args:
        category (str) [Optional]: The meditation category to filter by.
        duration (int) [Optional]: Maximum meditation duration in minutes.
        experience_level (str) [Optional]: The practitioner's experience level.

    Returns:
        meditations (list): List of meditation sessions matching the filter criteria.
    """
    try:
        return api.get_meditation_library(category, duration, experience_level)
    except Exception as e:
        raise e

@mcp.tool()
def get_daily_meditation(user_id: str, mood: str = None) -> dict:
    """
    Get a personalized daily meditation recommendation based on user preferences and current mood.

    Args:
        user_id (str): The unique identifier of the user account.
        mood (str) [Optional]: The user's current emotional state.

    Returns:
        meditation_id (str): The unique identifier for this meditation session.
        title (str): The display title of the recommended meditation.
        description (str): A detailed description of the meditation's focus and benefits.
        duration (int): The total length of the meditation in minutes.
        recommended_for (str): The reason this meditation was recommended.
        theme (str): The thematic focus of today's meditation.
        new_content (bool): Whether this is newly released content.
        series_info (dict): Information about the meditation course or series.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        return api.get_daily_meditation(user_id, mood)
    except Exception as e:
        raise e

@mcp.tool()
def get_sleep_content(content_type: str = None, narrator: str = None) -> dict:
    """
    Browse sleep stories, ambient sounds, music, and sleep meditations to aid rest.

    Args:
        content_type (str) [Optional]: The type of sleep content to retrieve.
        narrator (str) [Optional]: Filter by a specific narrator's voice.

    Returns:
        sleep_content (list): List of sleep content items matching the filter criteria.
    """
    try:
        return api.get_sleep_content_list(content_type, narrator)
    except Exception as e:
        raise e

@mcp.tool()
def get_breathing_exercises(goal: str = None, duration: int = None) -> dict:
    """
    Get guided breathing exercises designed for specific wellness goals.

    Args:
        goal (str) [Optional]: The intended outcome of the breathing exercise.
        duration (int) [Optional]: The desired exercise duration in minutes.

    Returns:
        exercises (list): List of breathing exercises matching the specified goal and duration.
    """
    try:
        return api.get_breathing_exercises_list(goal, duration)
    except Exception as e:
        raise e

@mcp.tool()
def start_meditation_session(meditation_id: str, user_id: str) -> dict:
    """
    Begin a tracked meditation session with streaming access and progress monitoring.

    Args:
        meditation_id (str): The unique identifier for this meditation session.
        user_id (str): The unique identifier of the user account.

    Returns:
        session_id (str): The unique identifier for this active meditation session.
        started_at (str): The timestamp when the meditation session began.
        streaming_url (str): The streaming URL for the meditation audio content.
        progress_tracking (bool): Whether session progress is being tracked.
        allow_background_play (bool): Whether audio can continue in background.
        completion_reward (str): The reward earned upon completing this session.
    """
    try:
        if not meditation_id or not isinstance(meditation_id, str):
            raise ValueError("Meditation ID must be a non-empty string")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if meditation_id not in api.meditations:
            raise ValueError(f"Meditation {meditation_id} not found")
        return api.start_meditation_session(meditation_id, user_id)
    except Exception as e:
        raise e

@mcp.tool()
def log_meditation_completion(session_id: str, completion_percent: float, notes: str = None) -> dict:
    """
    Record meditation session completion with progress percentage and optional reflection notes.

    Args:
        session_id (str): The unique identifier for this active meditation session.
        completion_percent (float): The percentage of the session completed.
        notes (str) [Optional]: Post-meditation reflection or notes.

    Returns:
        logged (bool): Whether the session completion was successfully recorded.
        stats_updated (dict): Updated meditation practice statistics.
        insights (str): Personalized insight based on practice patterns.
        next_recommendation (dict): Suggested next meditation session.
    """
    try:
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Session ID must be a non-empty string")
        if session_id not in api.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        return api.log_meditation_completion(session_id, completion_percent, notes)
    except Exception as e:
        raise e

@mcp.tool()
def get_meditation_stats(user_id: str, period: str = None) -> dict:
    """
    Retrieve meditation practice statistics, streaks, and milestones for a specified time period.

    Args:
        user_id (str): The unique identifier of the user account.
        period (str) [Optional]: The time period for statistics.

    Returns:
        total_sessions (int): The cumulative number of meditation sessions completed.
        total_minutes (int): The cumulative meditation time in minutes.
        current_streak (int): The number of consecutive days meditated.
        longest_streak (int): The maximum number of consecutive days ever meditated.
        favorite_category (str): The meditation category practiced most frequently.
        average_session_length (float): The mean duration of meditation sessions.
        milestones_achieved (list): List of practice milestones and achievements.
        mindfulness_score (int): Calculated mindfulness score from 0 to 100.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if user_id not in api.user_stats:
            raise ValueError(f"User {user_id} not found")
        return api.get_meditation_stats(user_id, period)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
