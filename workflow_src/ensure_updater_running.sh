# This script makes sure at least 1 (preferably just 1) copy of local_cache_updater.py is running in the background.
if ! ps -x | grep -v grep | grep -q "python local_cache_updater.py"; then
  nohup python "local_cache_updater.py" &
fi
