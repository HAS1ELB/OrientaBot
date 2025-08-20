import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# App configuration
APP_TITLE = "OrientaBot - Conseiller d'orientation"
APP_ICON = "🎓"
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "collapsed"

# Default settings
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 2048