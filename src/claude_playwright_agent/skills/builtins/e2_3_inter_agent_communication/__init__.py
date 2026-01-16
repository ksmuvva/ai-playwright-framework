"""
E2.3 - Inter-Agent Communication Skill.
"""

from .main import (
    AgentMessage,
    InterAgentCommunicationAgent,
    MessageContext,
    MessagePriority,
    MessageType,
)

# Aliases for test compatibility
CommunicationProtocol = MessageContext

__all__ = [
    "AgentMessage",
    "InterAgentCommunicationAgent",
    "MessageContext",
    "MessagePriority",
    "MessageType",
    # Alias
    "CommunicationProtocol",
]
