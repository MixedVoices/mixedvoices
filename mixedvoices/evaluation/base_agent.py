from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BaseAgent(ABC):
    @abstractmethod
    def respond(self, input_text: str) -> Tuple[str, bool]:
        """Generate a response to the input text.
        First input_text will be an empty string if agent starts conversation.
        Returns (response, has_conversation_ended)
        """
        pass

    @property
    @abstractmethod
    def starts_conversation(self) -> Optional[bool]:
        """Whether the assistant says the first words in the conversation.
        If True, the assistant starts the conversation
        If False, the user starts the conversation
        If None, 50% chance of each
        """
        pass
