from typing import List, Optional

from openai import OpenAI

import mixedvoices


def get_openai_client():
    if mixedvoices.OPEN_AI_CLIENT is None:
        mixedvoices.OPEN_AI_CLIENT = OpenAI()
    return mixedvoices.OPEN_AI_CLIENT


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
            if request_callback_step:
                request_callback_step["variants"].append(step)
        elif "Check" in step:
            check_step = next(
                (s for s in standard_steps if s["name"] == "Check Availability"),
                None,
            )
            if check_step:
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
            "subpoints": None,
            "variants": ["Check Calender", "Check Inventory"],
        },
    ]

    combine_existing_steps(standard_steps, existing_step_names)
    stringify_subpoints_and_variants(standard_steps)
    return "\n".join(
        f"{i + 1}. {step['name']}{step['subpoints'] or ''}{step['variants'] or ''}"
        for i, step in enumerate(standard_steps)
    )
