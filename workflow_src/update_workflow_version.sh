# This script makes sure at least 1 (preferably just 1) copy of local_cache_updater.py is running in the background.
if ! ps -x | grep -v grep | grep -qF "python update_with_latest.py"; then
  nohup python "update_with_latest.py" &
fi
