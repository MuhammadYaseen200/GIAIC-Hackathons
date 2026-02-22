import asyncio
from watchers.gmail_watcher import GmailWatcher

async def test():
    w = GmailWatcher(vault_path='vault')
    w._resolve_paths()
    w._authenticate()
    print('Authenticated. Fetching unread emails...')
    emails = await w.poll()
    print(f'Found {len(emails)} unread emails')
    for e in emails[:5]:
        print(f'  [{e.classification.value:12}] {e.subject[:55]}')
    if emails:
        print()
        print('Processing first email into vault...')
        await w.process_item(emails[0])
        print('Done. Check vault/Needs_Action/ or vault/Inbox/')
    else:
        print('No unread emails found. Try sending yourself a test email first.')

asyncio.run(test())
