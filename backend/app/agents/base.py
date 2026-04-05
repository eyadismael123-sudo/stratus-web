"""BaseAgent abstract class.

All agents inherit from this. The plug-in pattern means:
  new agent = new subclass + new row in agent_templates table.
  Nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base for all Stratus agents."""

    slug: str              # matches agent_templates.slug in DB
    personality_prompt: str  # injected into every Claude call

    @abstractmethod
    async def handle_message(
        self,
        client: dict,
        message: dict,
        memory: dict,
        profile: dict,
    ) -> str:
        """Process an incoming WhatsApp message and return the reply text.

        Args:
            client:  Row from the clients table (whatsapp_number, name, timezone, …)
            message: Parsed incoming message dict (type, text, voice_text, …)
            memory:  Agent-specific memory_json for this client (Layer 2)
            profile: Master personality profile_json for this client (Layer 3)

        Returns:
            Reply text to send back via WhatsApp.
        """

    @abstractmethod
    async def proactive_outreach(
        self,
        client: dict,
        memory: dict,
        profile: dict,
    ) -> str | None:
        """Generate a proactive message if relevant, or return None.

        Called by the scheduler — e.g. morning briefing cron.
        Return None if there's nothing meaningful to send today.
        """

    @abstractmethod
    def get_intro_message(self, client: dict) -> str:
        """Return the intro message sent automatically when the agent is hired."""

    @abstractmethod
    def get_onboarding_question(self, step: int, collected: dict) -> str | None:
        """Return the question for the given onboarding step, or None when done."""

    @abstractmethod
    def process_onboarding_answer(
        self, step: int, answer: str, collected: dict
    ) -> dict:
        """Validate/parse the answer and return the updated collected_data dict."""

    async def update_memory(
        self,
        client_id: str,
        agent_slug: str,
        new_interaction: str,
        current_memory: dict,
    ) -> dict:
        """Use Haiku to update agent_memory after every interaction.

        Override in subclasses if you need custom memory update logic.
        Default implementation returns current_memory unchanged (subclass handles it).
        """
        return current_memory
