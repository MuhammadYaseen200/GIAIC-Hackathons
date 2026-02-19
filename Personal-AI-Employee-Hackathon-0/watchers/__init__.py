"""Watcher system for the Personal AI Employee.

Re-exports key classes for convenient imports:
    from watchers import Classification, EmailItem, WatcherState, BaseWatcher, GmailWatcher
"""

from watchers.base_watcher import BaseWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.models import Classification, EmailItem, WatcherState

__all__ = [
    "Classification",
    "EmailItem",
    "WatcherState",
    "BaseWatcher",
    "GmailWatcher",
]
