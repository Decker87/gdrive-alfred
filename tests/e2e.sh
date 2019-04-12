# Meant to be run from base dir
cd "workflow_src"
../ci/install_nonstandard_packages_locally.sh "pylib_dist"
rm cache.json 2>/dev/null
python continuously_update_local_cache.py --spoof-server --debug
python search_local_cache.py "Edward" | tee out.txt
grep -Fq "Org Chart" out.txt
exit $?
