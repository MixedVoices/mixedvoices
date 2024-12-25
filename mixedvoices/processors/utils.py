import re
from typing import List, Optional


def stringify_subpoints_and_variants(standard_steps: List[dict]):
    for step in standard_steps:
        if step["variants"]:
            offset = len(step["subpoints"]) if step["subpoints"] else 0
            letter = chr(97 + offset)
            step["variants"] = (
                f"\n  {letter}. Use relevant variation, eg. {', '.join(step['variants'])}"
            )
        if step["subpoints"]:
            step["subpoints"] = [
                f"  {chr(97 + i)}. {subpoint}"
                for i, subpoint in enumerate(step["subpoints"])
            ]
            step["subpoints"] = "\n" + "\n".join(step["subpoints"])


def combine_existing_steps(
    standard_steps: List[dict], existing_step_names: Optional[List[str]] = None
):
    existing_step_names = existing_step_names or []

    for step in existing_step_names:
        if step in {s["name"] for s in standard_steps}:
            continue
        elif "Request" in step and "Callback" in step:
            request_callback_step = next(
                (s for s in standard_steps if s["name"] == "Request Expert Callback"),
                None,
            )
            if request_callback_step and step not in request_callback_step["variants"]:
                request_callback_step["variants"].append(step)
        elif "Check" in step and "Availability" in step:
            check_step = next(
                (s for s in standard_steps if s["name"] == "Check Availability"),
                None,
            )
            if check_step and step not in check_step["variants"]:
                check_step["variants"].append(step)
        else:
            standard_steps.append({"name": step, "subpoints": None, "variants": None})


def get_standard_steps_string(existing_step_names: Optional[List[str]] = None):
    standard_steps = [
        {"name": "Greeting", "subpoints": None, "variants": None},
        {
            "name": "Inquiry Handling",
            "subpoints": ["Address, timings etc."],
            "variants": None,
        },
        {
            "name": "Caller Complaint Handling",
            "subpoints": [
                "Complaints regarding product/service",
                "Complaint regarding bot",
            ],
            "variants": None,
        },
        {
            "name": "Collect Caller Information",
            "subpoints": ["name, phone number, id, etc"],
            "variants": None,
        },
        {
            "name": "Request Expert Callback",
            "subpoints": None,
            "variants": ["Request Doctor Callback"],
        },
        {
            "name": "Call Transfer to Human Agent",
            "subpoints": [
                "Only use if caller asks to connect with a human",
                "OR if bot transfers to human agent",
                "DONT use in any other case",
            ],
            "variants": None,
        },
        {
            "name": "Set Appointment",
            "subpoints": [
                "Request for appointment, determining purpose, time, place, confirmation etc",
                "Create this only *ONE* time at end of appointment discussion",
            ],
            "variants": None,
        },
        {"name": "Offer Further Assistance", "subpoints": None, "variants": None},
        {"name": "Farewell", "subpoints": None, "variants": None},
        {
            "name": "Check Availability",
            "subpoints": ["Only used to check availability of product/service"],
            "variants": ["Check Medicine Availability", "Check Inventory Availability"],
        },
    ]

    combine_existing_steps(standard_steps, existing_step_names)
    stringify_subpoints_and_variants(standard_steps)
    return "\n".join(
        f"{i + 1}. {step['name']}{step['subpoints'] or ''}{step['variants'] or ''}"
        for i, step in enumerate(standard_steps)
    )


def parse_explanation_response(
    response: str,
) -> dict:
    """
    Parse the response string to extract explanation and success/score.

    Args:
        response: String response from the API

    Returns:
        dict: Parsed explanation and success/score

    Raises:
        ValueError: If parsing fails
    """
    explanation_match = re.search(
        r"Explanation:\s*(.+?)(?=(?:\nSuccess:|\nScore:|$))",
        response,
        re.DOTALL | re.IGNORECASE,
    )

    success_match = re.search(r"Success:\s*(True|False|N/A)", response, re.IGNORECASE)
    score_match = re.search(r"Score:\s*(10|\d|N/A|PASS|FAIL)", response, re.IGNORECASE)

    if not explanation_match:
        raise ValueError("Could not parse explanation")

    explanation = explanation_match[1].strip()

    if success_match:
        success_value = success_match[1].strip()
        if success_value not in ["TRUE", "FALSE", "N/A"]:
            raise ValueError("Invalid success format")
        mapping = {"TRUE": True, "FALSE": False, "N/A": None}
        success_output = mapping[success_value]
        return {"explanation": explanation, "success": success_output}
    elif score_match:
        score = score_match[1].strip()
        if score in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            score_output = int(score)
        elif score in ["N/A", "FAIL", "PASS"]:
            score_output = score
        else:
            raise ValueError("Invalid score format")

        return {"explanation": explanation, "score": score_output}
    else:
        raise ValueError("Could not parse success or score")
