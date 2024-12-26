from openai import OpenAI

AGENT_PROMPT = """You're voice assistant for Locoto's Dental.
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


def check_conversation_ended(agent_message):
    return (
        "bye" in agent_message.lower()
        or "see you" in agent_message.lower()
        or "see ya" in agent_message.lower()
        or "catch you" in agent_message.lower()
        or "talk to you" in agent_message.lower()
    )


class DentalAgent:
    def __init__(self, model):
        self.conversation_memory = []
        self.model = model
        self.openai_client = OpenAI()

    def get_response(self, user_input: str) -> str:
        self.conversation_memory.append({"role": "user", "content": user_input.strip()})
        messages = [{"role": "system", "content": AGENT_PROMPT}]
        messages.extend(self.conversation_memory)

        chat_completion = self.openai_client.chat.completions.create(
            model=self.model, messages=messages
        )
        response = chat_completion.choices[0].message.content.strip()
        self.conversation_memory.append({"role": "assistant", "content": response})
        return response
