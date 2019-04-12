# This script is used to build (package) a .alfredworkflow file.
# If all goes right, it will end up at bin/gdrive-alfred.alfredworkflow
packageName="gdrive-alfred.alfredworkflow"
packagePath="bin/$packageName"
mkdir "bin"

# Install necessary packages locally
ci/install_nonstandard_packages_locally.sh "workflow_src/pylib_dist"

# Zip it up (unfortunately zip util requires us to pushd to avoid copying workflow_src)
pushd workflow_src
zip -r "../$packagePath" *
popd

# Helpful msg
du -sh "$packagePath"