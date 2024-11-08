from typing import Final

API_PORT: Final = 8000
DASHBOARD_PORT: Final = 8501
API_BASE_URL: Final = f"http://localhost:{API_PORT}/api"
DEFAULT_PAGE_CONFIG = {
    "page_title": "MixedVoices Dashboard",
    "page_icon": "🎙️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
