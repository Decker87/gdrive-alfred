# This script makes sure at least 1 (preferably just 1) copy of continuously_update_local_cache.py is running in the background.
if ! ps -x | grep -v grep | grep -qF "python continuously_update_local_cache.py"; then
  nohup python "continuously_update_local_cache.py" &
fi
