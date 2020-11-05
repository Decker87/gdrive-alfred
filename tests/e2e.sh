# Meant to be run from base dir
cd "workflow_src"
../ci/install_nonstandard_packages_locally.sh "pylib_dist"

echo "TEST: basic search with cache"
rm cache.json 2>/dev/null
python continuously_update_local_cache.py --spoof-server --debug
python main.py --query "Edward" | tee out.txt
if ! grep -Fq "Org Chart" out.txt; then
    echo "FAILED!"
    exit 1
fi

echo "TEST: basic search with cache, sheet type"
rm cache.json 2>/dev/null
python continuously_update_local_cache.py --spoof-server --debug
python main.py --query "Kelly sheet" | tee out.txt
if ! grep -Fq "1tgzWrjCGkJLjTPlQO3Uuz42XJKqH0Mu13VUkVAGBt1c" out.txt; then
    echo "FAILED!"
    exit 2
fi

echo "TEST: basic search with cache, doc type"
rm cache.json 2>/dev/null
python continuously_update_local_cache.py --spoof-server --debug
python main.py --query "Kelly doc" | tee out.txt
if ! grep -Fq "1uwEPYqv1Vl9dsAs3X51qrUigE2NfExOBT764XyaFifs" out.txt; then
    echo "FAILED!"
    exit 3
fi

echo "TEST: Junk query should have empty item results"
python main.py --query "fajksdhfhadslfjhdsafljkadh" | tee out.txt
# Items always contain an "arg", so no "arg" = empty items
if ! grep -Fq '"items":' out.txt || grep -Fq '"args"' out.txt; then
    echo "FAILED!"
    exit 4
fi

echo "TEST: If version is out of date, should add an item to update"
python continuously_get_latest_workflow.py --debug --spoof-newer-version
python main.py --query "Edward" | tee out.txt
if ! grep -Fq "An update is available" out.txt; then
    rm "latest/VERSION.txt"
    echo "FAILED!"
    exit 5
fi
rm "latest/VERSION.txt"

echo "TEST: Search with no cache - should say its updating"
rm cache.db 2>/dev/null
python main.py --query "Edward" | tee out.txt
# Make sure it has an item to update the cache
if ! grep -Fq "Updating cache" out.txt; then
    echo "FAILED!"
    exit 6
fi
# Make sure that's the only item
t=`cat out.txt | grep '"title"' | wc -l`
t=`echo $t`
if [[ "$t" != "1" ]]; then
    echo "FAILED!"
    exit 7
fi

echo "SUCCESS"
