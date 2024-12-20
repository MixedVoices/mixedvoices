from abc import ABC, abstractmethod
from typing import Optional


class BaseAgent(ABC):
    @abstractmethod
    def respond(self, input_text: str) -> str:
        """Generate a response to the input text.
        Input text might be an empty string in case the assistant starts the conversation
        """
        pass

    @property
    @abstractmethod
    def conversation_ended(self) -> bool:
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
