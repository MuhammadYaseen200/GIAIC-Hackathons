import asyncio
from watchers.gmail_watcher import GmailWatcher

asyncio.run(GmailWatcher(vault_path='vault').start())
