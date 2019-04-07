# Releases

CricleCI does not currently support parameterized builds. This means I can't manually kick off a special workflow to package and create a github release.

So, instead I've decided that any time I update the VERSION.txt file, that should tell CI to create a release and upload the .alfredworkflow file.

1. Change the VERSION.txt and push
1. Let CircleCI do its thing, should result in draft release with file attached
  1. Check https://circleci.com/gh/Decker87/gdrive-alfred/tree/master to watch
1. Visit https://github.com/Decker87/gdrive-alfred/releases to see it
1. Don't forget to publish the draft release

# Install python libs and dependencies to local dir

```
mkdir pylib_dist
pip install --target=pylib_dist --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

# Auto-updating

Auto-updating with Alfred seems very troublesome to implement. Spent too much time on it already.
Instead I can add a node to the workflow that spins off another process to update. Can easily scriptify checking the latest release and downloading it / unzipping it if it's a later version.
