versionPath="workflow_src/VERSION.txt"
packagePath="bin/gdrive-alfred.alfredworkflow"

# If we aren't on master branch from within CircleCI, don't do anything.
if [[ "$CIRCLE_BRANCH" != "master" ]]; then
    exit
fi

# If the version increased in this commit, then roll a new version!
if ! git diff --exit-code HEAD^ HEAD "$versionPath"; then
    newVersion="$(cat $versionPath)"
    echo "newVersion=$newVersion"
    python ci/create_release.py --asset-path "$packagePath" $GITHUB_USER $GITHUB_TOKEN $newVersion
else
    echo "$versionPath not updated this commit."
fi
