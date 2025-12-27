"""Task model for the Todo application.

This module defines the Task dataclass representing a single todo item.
ADR-003 Compliance: Pure dataclass with NO file I/O methods.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """Represents a single todo task.

    Attributes:
        id: Unique identifier for the task (assigned by repository).
        title: The title/name of the task (required, max 200 chars).
        description: Optional detailed description of the task.
        completed: Whether the task has been completed.
        created_at: Timestamp when the task was created.
    """

    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
