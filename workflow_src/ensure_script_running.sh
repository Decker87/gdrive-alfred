# This script makes sure at least 1 (preferably just 1) copy of a python script is running in the background.
script="$1"

# On some systems, the system python executable is called "Python" instead of "python" - so truncate to "ython"
if ! ps -x | grep -v grep | grep -qF "ython ""$script"; then
  nohup python "$script" &
fi
