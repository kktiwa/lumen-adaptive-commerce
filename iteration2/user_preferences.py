"""User preferences management - loads and manages user preferences"""
from typing import Dict, Any
from .conversation_types import UserPreferences

# Sample user profiles that can be loaded
SAMPLE_USER_PROFILES = {
    "profile1": {
        "budget": "$50-100",
        "interests": ["sports", "outdoor activities", "tech"],
        "preferences": {
            "eco_friendly": True,
            "premium": False,
            "educational": True
        }
    },
    "profile2": {
        "budget": "$100-200",
        "interests": ["arts", "crafts", "STEM"],
        "preferences": {
            "eco_friendly": False,
            "premium": True,
            "educational": True
        }
    },
    "profile3": {
        "budget": "$0-50",
        "interests": ["games", "outdoor activities"],
        "preferences": {
            "eco_friendly": True,
            "premium": False,
            "educational": False
        }
    }
}

def load_user_preferences(profile_id: str = "profile1") -> UserPreferences:
    """Load a user profile by ID"""
    if profile_id in SAMPLE_USER_PROFILES:
        profile = SAMPLE_USER_PROFILES[profile_id]
        return UserPreferences(
            budget=profile["budget"],
            interests=profile["interests"],
            preferences=profile["preferences"]
        )
    
    # Default profile
    return UserPreferences(
        budget="$50-100",
        interests=["general"],
        preferences={"eco_friendly": True, "premium": False}
    )

def get_available_profiles() -> list:
    """Get list of available profile IDs"""
    return list(SAMPLE_USER_PROFILES.keys())
