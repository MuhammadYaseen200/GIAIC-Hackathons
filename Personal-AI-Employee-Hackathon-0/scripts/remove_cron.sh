#!/bin/bash
# remove_cron.sh — Remove all H0 cron entries.
crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED" | crontab -
echo "H0 cron entries removed."
echo "Verify with: crontab -l"
