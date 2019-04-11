# Meant to be run from workflow_src
rm cache.json cache.pickle
python continuously_update_local_cache.py --spoof-server --debug
python search_local_cache.py "Edward" | tee out.txt
grep -Fq "Org Chart" out.txt
exit $?
