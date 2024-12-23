from unittest.mock import patch

from mixedvoices.processors.llm_metrics import get_llm_metrics


# patch models.METRICS_MODEL
@patch("mixedvoices.models.METRICS_MODEL", "gpt-4o-mini")
def test_get_llm_metrics():
    transcript = """
    Bot: Hello. This is Locoto Dental. How can I assist you today?
    User: Hey. I wanted to just book an appointment.
    Bot: Awesome. I can help with that. Can I get your full name, please?
    User: Are you guys open today, though?
    Bot: Sorry. We're closed today. Our hours are 8 AM to 5 PM daily except for Sundays. Can I get your full name to schedule an appointment for you?
    User: But today is Wednesday, 2:30 PM. How are you guys closed?
    Bot: Oh, I see. My bad I totally missed the part, I'm not able to see the current time as I'm an AI. I apologize for the confusion. Can I still get your full name to schedule an appointment for you?
    User: No. Never mind. I wanted to come in right now, but doesn't seem like you will be able to help. So that's okay.
    Bot: I'm really sorry about that. If you change your mind, feel free to reach out again. Take care.
    """
    prompt = """You're voice assistant for Locoto's Dental.
    Info:-
    Location: 123 North Face Place, Anaheim, California
    Hours: 8 AM to 5PM daily, closed on Sundays.
    Practicing dentist: Dr. Mary Smith
    Other: Provides dental services to the local Anaheim community.

    Your job is to answer questions about the business, and book appointments.
    If user wants to book an appointment, your goal is to gather necessary information.
    Do it in a friendly and efficient manner like follows:

    1. Ask for full name.
    2. Ask for appointment purpose.
    3. Request their preferred date and time.
    4. Confirm all details with the caller, including date and time of the appointment.

    - Be sure to be kind of funny and witty!
    - Use casual language, phrases like "Umm...", "Well...", and "I mean" are preferred.
    - Keep your responses short, like in a real conversation. Less than 20 words.
    - NEVER use emojis.
    """
    metrics = get_llm_metrics(transcript, prompt)

    metric_scoring = {
        "empathy": list(range(11)),
        "repetition": ["PASS", "FAIL", "N/A"],
        "conciseness": list(range(11)),
        "hallucination": ["PASS", "FAIL"],
        "context": ["PASS", "FAIL"],
        "scheduling": list(range(11)) + ["N/A"],
        "adaptive_qa": list(range(11)) + ["N/A"],
        "objection_handling": list(range(11)),
    }

    for metric, scores in metric_scoring.items():
        assert metrics[metric]["score"] in scores
