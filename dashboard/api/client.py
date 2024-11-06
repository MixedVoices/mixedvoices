import requests
from typing import Dict, Optional
import streamlit as st
from dashboard.config import API_BASE_URL

class APIClient:
    @staticmethod
    def fetch_data(endpoint: str) -> Dict:
        """Fetch data from the FastAPI backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching data from API: {str(e)}")
            return {}
    
    @staticmethod
    def post_data(endpoint: str, json_data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """Post data to the FastAPI backend"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/{endpoint}",
                json=json_data if json_data else None,
                files=files if files else None
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error posting data to API: {str(e)}")
            return {}