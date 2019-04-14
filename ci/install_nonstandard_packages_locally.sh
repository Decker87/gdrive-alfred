# CircleCI images have an old pip for some reason
if [[ "$CIRCLECI" == "true" ]]; then
    sudo pip install --upgrade pip
fi

target="$1"
pip install --target="$target" google-api-python-client google-auth-httplib2 google-auth-oauthlib requests
pip install --target="$target" --no-deps --platform=macosx-10.13-intel ujson

# For some reason, the "google" library doesn't have an __init__.py which prevents it from being imported.
touch "$target/google/__init__.py"
