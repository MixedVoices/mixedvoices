import os
from typing import Final

from PIL import Image


def load_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, "content", "logo.png")
    if not os.path.exists(logo_path):
        return
    return Image.open(logo_path)


API_PORT: Final = 7760
DASHBOARD_PORT: Final = 7761
API_BASE_URL: Final = f"http://localhost:{API_PORT}/api"
page_icon = load_logo()
DEFAULT_PAGE_CONFIG = {
    "page_title": "MixedVoices Dashboard",
    "page_icon": page_icon,
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
