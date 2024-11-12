from http import HTTPStatus
from typing import Dict, Optional

import requests
import streamlit as st

from mixedvoices.dashboard.config import API_BASE_URL


class APIClient:
    """Client for interacting with the FastAPI backend"""

    @staticmethod
    def handle_request_error(e: requests.RequestException, operation: str) -> None:
        """Handle different types of request errors

        Args:
            e: The caught exception
            operation: The operation being performed ('fetch' or 'post')

        Raises:
            APIError: With detailed error information
        """
        if isinstance(e, requests.ConnectionError):
            error_msg = (
                f"Failed to connect to API server while {operation}ing data. "
                "Please check your internet connection."
            )
            st.error(error_msg)
            return

        if isinstance(e, requests.Timeout):
            error_msg = (
                f"Request timed out while {operation}ing data. Please try again."
            )
            st.error(error_msg)
            return

        if isinstance(e, requests.HTTPError):
            status_code = e.response.status_code
            try:
                response_data = e.response.json()
                error_detail = response_data.get(
                    "detail", "No additional details provided"
                )
            except ValueError:
                response_data = {}
                error_detail = e.response.text or "No response body"

            error_msg = {
                HTTPStatus.BAD_REQUEST: f"Invalid request: {error_detail}",
                HTTPStatus.UNAUTHORIZED: "Authentication failed. Check your creds.",
                HTTPStatus.FORBIDDEN: "You don't have permission for this action.",
                HTTPStatus.NOT_FOUND: f"Resource not found, endpoint: {e.response.url}",
                HTTPStatus.INTERNAL_SERVER_ERROR: "Server error. Try again later.",
            }.get(
                status_code, f"Request failed with status {status_code}: {error_detail}"
            )

            st.error(error_msg)
            return

        # Handle any other unexpected errors
        error_msg = f"Unexpected error while {operation}ing data: {str(e)}"
        st.error(error_msg)

    @staticmethod
    def fetch_data(endpoint: str) -> Dict:
        """Fetch data from the FastAPI backend

        Args:
            endpoint: API endpoint to fetch from

        Returns:
            Dict: Response data from API

        Raises:
            APIError: When request fails with detailed error information
        """
        try:
            response = requests.get(
                f"{API_BASE_URL}/{endpoint}", timeout=30  # Add reasonable timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            APIClient.handle_request_error(e, "fetch")
            return {}

    @staticmethod
    def post_data(
        endpoint: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Post data to the FastAPI backend

        Args:
            endpoint: API endpoint to post to
            json_data: JSON payload to send
            files: Files to upload
            params: Query parameters to include

        Returns:
            Dict: Response data from API

        Raises:
            APIError: When request fails with detailed error information
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/{endpoint}",
                json=json_data or None,
                files=files or None,
                params=params or None,
                timeout=30,  # Add reasonable timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            APIClient.handle_request_error(e, "post")
            return {}
