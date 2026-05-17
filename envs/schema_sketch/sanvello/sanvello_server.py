# Data Source: https://www.sanvello.com/
# Server: Sanvello
# Category: Mental Health / CBT & Mood Tracking


def daily_check_in(user_id: str, mood_rating: int, feelings: list, notes: str = None) -> dict:
    """
    Record daily mood check-in with CBT-based assessment.
    
    Args:
        user_id (str): User identifier
        mood_rating (int): Mood scale 1-10
        feelings (list): Selected emotions like ["anxious", "tired", "hopeful"]
        notes (str): [Optional] Journal entry for the day
        
    Returns:
        dict: {
            "check_in_id": str,
            "timestamp": str,
            "insights": str,         # Pattern insights based on history
            "recommended_tools": list,  # Suggested coping tools
            "guided_journey_suggestion": str  # Recommended program
        }
    """
    pass


def get_guided_journeys(category: str = None) -> list:
    """
    Get structured CBT-based programs for various mental health needs.
    
    Args:
        category (str): [Optional] Filter by: "anxiety", "depression", "stress", "sleep", "social_anxiety"
        
    Returns:
        list: Each journey contains {
            "journey_id": str,
            "title": str,
            "description": str,
            "category": str,
            "total_steps": int,
            "duration_weeks": int,
            "techniques": list,      # CBT techniques used
            "clinical_approach": str
        }
    """
    pass


def start_journey(user_id: str, journey_id: str) -> dict:
    """
    Enroll in a guided mental health program.
    
    Args:
        user_id (str): User identifier
        journey_id (str): Program to start
        
    Returns:
        dict: {
            "enrollment_id": str,
            "current_step": int,
            "progress_percent": float,
            "weekly_goal": dict,
            "next_activity": dict
        }
    """
    pass


def get_coping_tools(tool_type: str = None, situation: str = None) -> list:
    """
    Get evidence-based coping tools for immediate relief.
    
    Args:
        tool_type (str): [Optional] "breathing", "meditation", "grounding", "visualization", "journaling"
        situation (str): [Optional] "test_taking", "public_speaking", "morning_dread", "panic"
        
    Returns:
        list: Each tool contains {
            "tool_id": str,
            "name": str,
            "type": str,
            "duration_minutes": int,
            "description": str,
            "instructions": list,
            "for_crisis": bool
        }
    """
    pass


def track_progress(user_id: str, metric_type: str = "all") -> dict:
    """
    Get comprehensive progress tracking across all activities.
    
    Args:
        user_id (str): User identifier
        metric_type (str): [Optional] "mood", "journeys", "tools", "sleep", "all"
        
    Returns:
        dict: {
            "overview": {
                "total_check_ins": int,
                "current_streak": int,
                "improvement_score": float  # Calculated wellness metric
            },
            "mood_trends": {
                "weekly_average": list,
                "best_day": str,
                "common_triggers": list
            },
            "journey_progress": list,
            "weekly_report": {
                "summary": str,
                "wins": list,
                "areas_for_growth": list
            }
        }
    """
    pass


def join_community_group(group_topic: str) -> dict:
    """
    Join anonymous peer support community groups.
    
    Args:
        group_topic (str): Topic of interest: "anxiety_support", "depression_recovery", "stress_management", "sleep_tips"
        
    Returns:
        dict: {
            "group_id": str,
            "group_name": str,
            "member_count": int,
            "moderated": bool,
            "recent_discussions": list,
            "guidelines": str
        }
    """
    pass
