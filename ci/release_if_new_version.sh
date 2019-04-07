ls -lisa

versionPath="workflow_src/VERSION.txt"

# If the version increased in this commit, then roll a new version!
if ! git diff --exit-code HEAD^ HEAD "$versionPath"; then
    newVersion="$(cat $versionPath)"
    echo "newVersion=$newVersion"
else
    echo "$versionPath not updated this commit."
fi
