import os
import re
import threading
import time
from typing import Generator, List, Literal, Tuple

import openai
import pygame
import requests
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents, Microphone

import mixedvoices as mv


def conversation_ended(response: str) -> bool:
    return (
        "bye" in response.lower()
        or "see you" in response.lower()
        or "see ya" in response.lower()
        or "catch you" in response.lower()
        or "talk to you" in response.lower()
    )


class DentalAssistant:
    SYSTEM_PROMPT = """You are a voice assistant for Locoto's Dental, a dental office located at 123 North Face Place, Anaheim, California. The hours are 8 AM to 5PM daily, but they are closed on Sundays.

    Locoto's dental provides dental services to the local Anaheim community. The practicing dentist is Dr. Mary Smith.

    You are tasked with answering questions about the business, and booking appointments. If they wish to book an appointment, your goal is to gather necessary information from callers in a friendly and efficient manner like follows:

    1. Ask for their full name.
    2. Ask for the purpose of their appointment.
    3. Request their preferred date and time for the appointment.
    4. Confirm all details with the caller, including the date and time of the appointment.

    - Be sure to be kind of funny and witty!
    - Keep all your responses short and simple. Use casual language, phrases like "Umm...", "Well...", and "I mean" are preferred.
    - Keep your responses short, like in a real conversation. Don't ramble for too long.
    - Don't say hey multiple times.
    - NEVER use emojis.
    """

    def __init__(self, mode: Literal["text", "cli", "voice"]):
        self.mode = mode
        self.conversation_memory = []
        self.output_audio_file = "output_audio.mp3"
        self.mute_microphone = threading.Event()

        # Initialize API keys
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Initialize clients
        if self.mode == "voice":
            self.dg_client = DeepgramClient(api_key=self.deepgram_api_key)
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        # TTS configuration
        self.deepgram_tts_url = "https://api.deepgram.com/v1/speak?model=aura-helios-en"
        self.headers = {
            "Authorization": f"Token {self.deepgram_api_key}",
            "Content-Type": "application/json",
        }
        self.path = "./data/call1.wav"

    def conversation_loop(self) -> Generator[Tuple[str, str], str, None]:
        """
        Generator that yields (user_message, assistant_response) tuples.
        Accepts user messages via send().
        """
        user_message = yield
        while user_message is not None:
            response = self.get_assistant_response(user_message)
            user_message = yield (user_message, response)

    def segment_text_by_sentence(self, text: str) -> List[str]:
        sentence_boundaries = re.finditer(r"(?<=[.!?])\s+", text)
        boundaries_indices = [boundary.start() for boundary in sentence_boundaries]

        segments = []
        start = 0
        for boundary_index in boundaries_indices:
            segments.append(text[start : boundary_index + 1].strip())
            start = boundary_index + 1
        segments.append(text[start:].strip())

        return segments

    def synthesize_audio(self, text: str) -> bytes:
        payload = {"text": text}
        with requests.post(
            self.deepgram_tts_url, stream=True, headers=self.headers, json=payload
        ) as r:
            return r.content

    def play_audio(self, file_path: str):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.mute_microphone.clear()

    def get_assistant_response(self, user_input: str) -> str:
        self.conversation_memory.append({"role": "user", "content": user_input.strip()})
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(self.conversation_memory)

        chat_completion = self.openai_client.chat.completions.create(
            model="gpt-4o", messages=messages
        )
        response = chat_completion.choices[0].message.content.strip()
        self.conversation_memory.append({"role": "assistant", "content": response})
        return response

    def handle_voice_response(self, response: str):
        text_segments = self.segment_text_by_sentence(response)
        with open(self.output_audio_file, "wb") as output_file:
            for segment_text in text_segments:
                audio_data = self.synthesize_audio(segment_text)
                output_file.write(audio_data)

        self.mute_microphone.set()
        self.current_microphone.mute()
        self.play_audio(self.output_audio_file)
        time.sleep(0.5)
        self.current_microphone.unmute()

        if os.path.exists(self.output_audio_file):
            os.remove(self.output_audio_file)

    def setup_voice_handlers(self, dg_connection):
        self.is_finals = []

        def on_open(_, open, **kwargs):  # Changed self to _
            print("Connection Open")

        def on_message(_, result, **kwargs):  # Changed self to _
            if self.mute_microphone.is_set():  # Using class's self here
                return

            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return

            if result.is_final:
                self.is_finals.append(sentence)
                if result.speech_final:
                    utterance = " ".join(self.is_finals)
                    print(f"Speech Final: {utterance}")
                    self.is_finals = []

                    response = self.get_assistant_response(utterance)
                    print(f"Assistant: {response}")
                    self.handle_voice_response(response)
            else:
                print(f"Interim Results: {sentence}")

        def on_close(_, close, **kwargs):
            print("Connection Closed")
            project = mv.load_project("dental_clinic")
            version = project.load_version("v1")
            metadata = {"transcript": self.get_combined_transcript()}
            version.add_recording(self.path, metadata=metadata)

        def on_error(_, error, **kwargs):
            print(f"Error: {error}")

        # Set up event handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    def run_voice_mode(self):
        try:
            dg_connection = self.dg_client.listen.live.v("1")
            self.setup_voice_handlers(dg_connection)

            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
                endpointing=500,
            )

            if not dg_connection.start(options, addons={"no_delay": "true"}):
                print("Failed to connect to Deepgram")
                return

            self.current_microphone = Microphone(dg_connection.send)
            self.current_microphone.start()

            print("\nPress Enter to stop...")
            input("")

            self.current_microphone.finish()
            dg_connection.finish()
            print("Session ended")

        except Exception as e:
            print(f"Error in voice mode: {e}")

    def run_cli_mode(self):
        print("Welcome to Locoto's Dental Assistant! (Type 'quit' to exit)")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "quit":
                print("Thank you for using Locoto's Dental Assistant!")
                break

            response = self.get_assistant_response(user_input)
            print(f"\nAssistant: {response}")

    def run(self):
        if self.mode == "voice":
            self.run_voice_mode()
        elif self.mode == "cli":
            self.run_cli_mode()
        else:  # text mode
            # In text mode, we don't automatically start a loop
            # Instead, the user should use get_assistant_response() or conversation_loop()
            pass

    def get_combined_transcript(self):
        all_messages = []
        # in the format user: message\nbot: message\n
        for message in self.conversation_memory:
            if message["role"] == "user":
                all_messages.append(f"user: {message['content']}\n")
            else:
                all_messages.append(f"bot: {message['content']}\n")

        return "".join(all_messages)


# Example usage:
if __name__ == "__main__":
    assistant_cli = DentalAssistant(mode="voice")
    assistant_cli.run()

    # Example 2: Text Mode (Programmatic)
    # assistant_text = DentalAssistant(mode='text')

    # Simple single message processing
    # response = assistant_text.get_assistant_response("What are your office hours?")
    # print(f"Response: {response}")
    # exit()

    # Using the conversation loop
    # conversation = assistant_text.conversation_loop()
    # next(conversation)  # Initialize the generator

    # # Simulate a conversation
    # messages = [
    #     "Hi, I'd like to book an appointment",
    #     "My name is John Smith",
    #     "I need a cleaning",
    #     "How about next Tuesday at 2pm?"
    # ]

    # for message in messages:
    #     user_msg, assistant_response = conversation.send(message)
    #     print(f"User: {user_msg}")
    #     print(f"Assistant: {assistant_response}\n")
