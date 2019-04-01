# Releases

CricleCI does not currently support parameterized builds. This means I can't manually kick off a special workflow to package and create a github release.

So, instead there is a semi-manual process:

1. Let circleci store the zip files as artifacts with each build
2. Manually download the zip, goto https://circleci.com/gh/Decker87/gdrive-alfred/tree/master
  1. Note: It may be possible to use the CircleCI API to do this step
3. Use the create_release.py script to create a draft release with the zip uploaded.
4. Don't forget to publish the draft release

# Install python libs and dependencies to local dir

```
mkdir pylib_dist
pip install --target=pylib_dist --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

# Auto-updating

Auto-updating with Alfred seems very troublesome to implement. Spent too much time on it already.
Instead I can add a node to the workflow that spins off another process to update. Can easily scriptify checking the latest release and downloading it / unzipping it if it's a later version.
