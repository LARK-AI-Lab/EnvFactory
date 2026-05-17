# Data Source: https://theraapi.com/
# Server: TheraApi
# Category: Mental Health / Therapy Platform


def search_therapists(specialty: str = None, language: str = None, 
                      availability: str = None, insurance: str = None) -> list:
    """
    Search for licensed therapists with advanced filtering.
    
    Args:
        specialty (str): [Optional] "anxiety", "depression", "trauma", "cbt", "family", "addiction"
        language (str): [Optional] Therapist language: "english", "spanish", "mandarin", etc.
        availability (str): [Optional] "today", "this_week", "weekend", "evening"
        insurance (str): [Optional] Insurance provider name
        
    Returns:
        list: Each therapist contains {
            "therapist_id": str,
            "name": str,
            "title": str,            # "Licensed Clinical Psychologist", "LCSW", etc.
            "specialties": list,
            "languages": list,
            "rating": float,
            "experience_years": int,
            "availability": {
                "next_slot": str,    # ISO datetime
                "timezone": str
            },
            "session_types": list,   # "video", "audio", "in_person", "chat"
            "bio": str,
            "photo_url": str,
            "hourly_rate": float
        }
    """
    pass


def get_therapist_details(therapist_id: str) -> dict:
    """
    Get detailed profile for a specific therapist.
    
    Args:
        therapist_id (str): Unique therapist identifier
        
    Returns:
        dict: {
            "therapist_id": str,
            "name": str,
            "credentials": list,
            "education": list,
            "approach": str,         # Therapeutic approach description
            "specialties_detail": list,
            "availability_calendar": dict,
            "reviews": list,
            "insurance_accepted": list,
            "session_fee": {
                "initial": float,
                "followup": float
            },
            "cancellation_policy": str
        }
    """
    pass


def book_session(user_id: str, therapist_id: str, datetime: str, 
                 session_type: str = "video", notes: str = None) -> dict:
    """
    Schedule a therapy session.
    
    Args:
        user_id (str): Patient identifier
        therapist_id (str): Selected therapist
        datetime (str): Session time in ISO format
        session_type (str): [Optional] "video", "audio", "in_person", "chat"
        notes (str): [Optional] Topics to discuss or concerns
        
    Returns:
        dict: {
            "booking_id": str,
            "status": str,           # "confirmed", "pending", "waitlist"
            "session_link": str,     # For video sessions
            "reminder_settings": dict,
            "cancellation_deadline": str,
            "pre_session_form": dict # Assessment to complete before session
        }
    """
    pass


def create_group_session(topic: str, max_participants: int, 
                         facilitator_id: str = None) -> dict:
    """
    Create or join a group therapy session.
    
    Args:
        topic (str): Group focus: "grief_support", "anxiety_coping", "mindfulness", "addiction_recovery"
        max_participants (int): Maximum group size (usually 6-12)
        facilitator_id (str): [Optional] Specific therapist to facilitate
        
    Returns:
        dict: {
            "session_id": str,
            "topic": str,
            "facilitator": dict,
            "schedule": {
                "start_time": str,
                "duration_minutes": int,
                "recurring": bool
            },
            "current_participants": int,
            "max_participants": int,
            "join_link": str,
            "guidelines": str
        }
    """
    pass


def get_session_history(user_id: str, therapist_id: str = None) -> list:
    """
    Get history of therapy sessions with notes and outcomes.
    
    Args:
        user_id (str): Patient identifier
        therapist_id (str): [Optional] Filter by specific therapist
        
    Returns:
        list: Each session contains {
            "session_id": str,
            "therapist_name": str,
            "date": str,
            "duration_minutes": int,
            "session_type": str,
            "topics_discussed": list,
            "homework_assigned": list,
            "progress_notes": str,
            "next_session_recommended": str
        }
    """
    pass


def generate_wellness_report(user_id: str, period: str = "monthly") -> dict:
    """
    Generate comprehensive mental health progress report.
    
    Args:
        user_id (str): Patient identifier
        period (str): [Optional] "weekly", "monthly", "quarterly"
        
    Returns:
        dict: {
            "report_period": str,
            "sessions_attended": int,
            "mood_trends": dict,
            "goals_progress": list,
            "therapeutic_outcomes": {
                "anxiety_score_change": float,
                "depression_score_change": float,
                "overall_wellbeing_change": float
            },
            "recommendations": list,
            "shareable_with_provider": bool
        }
    """
    pass
