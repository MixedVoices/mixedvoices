import pytest

from mixedvoices.processors.utils import (
    get_standard_steps_string,
    parse_explanation_response,
)


def test_parse_explanation_response():
    with pytest.raises(ValueError):
        parse_explanation_response("Random text")

    with pytest.raises(ValueError):
        parse_explanation_response(
            "Explanation: This is an explanation.\nSuccess: Successful"
        )

    with pytest.raises(ValueError):
        parse_explanation_response("Explanation: This is an explanation.\nScore: True")

    with pytest.raises(ValueError):
        parse_explanation_response(
            "Explanation: This is an explanation.\nEmotion: True"
        )

    respose = parse_explanation_response(
        "Explanation: This is an explanation.\nSuccess: TRUE"
    )

    assert respose["explanation"] == "This is an explanation."
    assert respose["success"]

    respose = parse_explanation_response(
        "Explanation: This is an explanation.\nScore: 5"
    )

    assert respose["explanation"] == "This is an explanation."
    assert respose["score"] == 5

    respose = parse_explanation_response(
        "Explanation: This is an explanation.\nScore: PASS"
    )

    assert respose["explanation"] == "This is an explanation."
    assert respose["score"] == "PASS"

    respose = parse_explanation_response(
        "Explanation: This is an explanation.\nScore: N/A"
    )

    assert respose["explanation"] == "This is an explanation."
    assert respose["score"] == "N/A"


def test_get_standard_steps_string():
    existing_step_names = [
        "Greeting",
        "Request Doctor Callback",
        "Request Nurse Callback",
        "Check Medicine Availability",
        "Check Cream Availability",
        "Ask to speak to manager",
    ]

    standard_steps = get_standard_steps_string(existing_step_names)
    assert (
        standard_steps
        == """1. Greeting
2. Inquiry Handling
  a. Address, timings etc.
3. Caller Complaint Handling
  a. Complaints regarding product/service
  b. Complaint regarding bot
4. Collect Caller Information
  a. name, phone number, id, etc
5. Request Expert Callback
  a. Use relevant variation, eg. Request Doctor Callback, Request Nurse Callback
6. Call Transfer to Human Agent
  a. Only use if caller asks to connect with a human
  b. OR if bot transfers to human agent
  c. DONT use in any other case
7. Set Appointment
  a. Request for appointment, determining purpose, time, place, confirmation etc
  b. Create this only *ONE* time at end of appointment discussion
8. Offer Further Assistance
9. Farewell
10. Check Availability
  a. Only used to check availability of product/service
  b. Use relevant variation, eg. Check Medicine Availability, Check Inventory Availability, Check Cream Availability
11. Ask to speak to manager"""
    )  # noqa E501
