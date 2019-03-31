# Determine version
version="1.`git rev-list --count HEAD`"
packageName="gdrive-alfred-v$version.alfredworkflow"
packagePath="bin/$packageName"
mkdir "bin"

# Install necessary packages locally
pip install --upgrade --target=workflow_src/pylib_dist google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Zip it up (unfortunately zip util requires us to pushd to avoid copying workflow_src)
pushd workflow_src
zip -r "../$packagePath" *
popd

# Helpful msg
du -sh "$packagePath"

# Clean up if asked to
if [[ "$1" == "--clean-up" ]]; then
  rm -rf "workflow_src/pylib_dist"
fi