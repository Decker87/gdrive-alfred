# This script makes sure at least 1 (preferably just 1) copy of a python script is running in the background.
script="$1"
if ! ps -x | grep -v grep | grep -qF "python ""$script"; then
  nohup python "$script" &
fi
