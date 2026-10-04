"""
Config model - application configuration management
"""

import json
import logging
import os
import platform
from typing import Dict

logger = logging.getLogger(__name__)

# Data directory setup
if platform.system() == "Windows":
    BASE_DIR = os.getenv("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
else:
    BASE_DIR = os.path.expanduser("~")

DATA_DIR = os.path.join(BASE_DIR, "JobTracker")
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def get_default_config() -> Dict:
    """Get default configuration"""
    return {
        'search_terms': ['Python Developer', 'Software Engineer'],
        'location': 'Germany',
        'country': 'Germany',
        'results_wanted': 50,
        'scrape_interval_hours': 2,
        'email_check_interval_minutes': 30,
        'gmail_email': '',
        'gmail_enabled': False,
        'theme': 'Dark',
        'groq_api_key': '',
        'base_resume_path': '',
        'base_cover_letter_path': '',
    }


def load_config(config_path: str = CONFIG_FILE) -> Dict:
    """Load configuration from file"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {config_path}")
                # Merge with defaults to ensure all keys exist
                defaults = get_default_config()
                defaults.update(config)
                return defaults
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    logger.info("Using default configuration")
    return get_default_config()


def save_config(config: Dict, config_path: str = CONFIG_FILE) -> bool:
    """Save configuration to file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False
