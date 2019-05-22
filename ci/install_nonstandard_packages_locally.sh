target="$1"

# If we're doing a test in circleCI, we need to install the platform-specific copy of ujson
if [[ "$CIRCLE_JOB" == "test"* ]]; then
    rm -rf "$target"/ujson* # Remove the mac-specific ones
    pip install --target="$target" ujson
fi

pip install --target="$target" google-api-python-client google-auth-httplib2 google-auth-oauthlib requests email

# For some reason, the "google" library doesn't have an __init__.py which prevents it from being imported.
touch "$target/google/__init__.py"
