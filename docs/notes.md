# Releases

CricleCI does not currently support parameterized builds. This means I can't manually kick off a special workflow to package and create a github release.

So, instead there is a semi-manual process:

1. Let circleci store the zip files as artifacts with each build
2. Manually download the zip
3. Use the create_release.py script to create a draft release with the zip uploaded.
  1. Note: It may be possible to use the CircleCI API to do this step
4. Don't forget to publish the draft release