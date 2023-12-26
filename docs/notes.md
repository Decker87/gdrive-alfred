# Releases

CircleCI doesn't work. To cut a release do it manually.

1. Manually package and create a release.
  ```bash
  pushd workflow_src

  pip3 install --upgrade --target=. google-api-python-client google-auth-httplib2 google-auth-oauthlib requests

  # Add any changed module files!
  git add *
  git commit -m "update modules"

  mkdir -p "../bin"
  zip -r "../bin/gdrive-alfred.alfredworkflow" *

  popd
  ```

1. Change the VERSION.txt and push.
1. Call `python3 ci/create_release.py --asset-path "bin/gdrive-alfred.alfredworkflow" $GITHUB_USER $GITHUB_TOKEN $newVersion`
1. OR just create a new release manually in github UI.
1. Visit https://github.com/Decker87/gdrive-alfred/releases to see it
1. Don't forget to publish the draft release

# Install python libs and dependencies to local dir

```
pip3 install --target=. --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

# Delete a remote git tag (rendering release a draft)

```
tag=1.1.1; git tag -d $tag; git push origin :refs/tags/$tag
```

# Perf notes

On 11/04/20, I tried SQLite and found it's very fast - around 40ms to query for all items matching tokens. The overhead of spawning a python process is about 40ms, so it's basically at the theoretical maximum.

Long ago, I tried running things as a cache server so that the searcher would only need to make an HTTP call. However HTTP calls seem to have 167ms overhead at least, so it's unfruitful.

# Change file perms on windows

```
git update-index --chmod=+x <file>
```

# CircleCI environment example

```
CIRCLECI=true
CIRCLE_BRANCH=fix-imports
CIRCLE_BUILD_NUM=191
CIRCLE_BUILD_URL=https://circleci.com/gh/Decker87/gdrive-alfred/191
CIRCLE_COMPARE_URL=
CIRCLE_INTERNAL_CONFIG=/.circleci-runner-config.json
CIRCLE_INTERNAL_SCRATCH=/tmp/circleci-508795058
CIRCLE_INTERNAL_TASK_DATA=/.circleci-task-data
CIRCLE_JOB=test_py27
CIRCLE_NODE_INDEX=0
CIRCLE_NODE_TOTAL=1
CIRCLE_PREVIOUS_BUILD_NUM=189
CIRCLE_PROJECT_REPONAME=gdrive-alfred
CIRCLE_PROJECT_USERNAME=Decker87
CIRCLE_REPOSITORY_URL=git@github.com:Decker87/gdrive-alfred.git
CIRCLE_SHA1=48812b179606896806ccc4b07a79651129843778
CIRCLE_SHELL_ENV=/tmp/.bash_env-5cb2a5d6888f900001ae27e9-0-build
CIRCLE_STAGE=test_py27
CIRCLE_USERNAME=Decker87
CIRCLE_WORKFLOW_ID=0218144f-f331-487f-81c9-237eae3b62b6
CIRCLE_WORKFLOW_JOB_ID=e0981ced-f4ef-4236-9915-26095e287696
CIRCLE_WORKFLOW_UPSTREAM_JOB_IDS=
CIRCLE_WORKFLOW_WORKSPACE_ID=0218144f-f331-487f-81c9-237eae3b62b6
CIRCLE_WORKING_DIRECTORY=~/project
HOME=/home/circleci
NO_PROXY=127.0.0.1,localhost,circleci-internal-outer-build-agent
OLDPWD=/home/circleci
PWD=/home/circleci/project/workflow_src
SSH_AUTH_SOCK=/tmp/circleci-508795058/ssh_auth_sock
```
