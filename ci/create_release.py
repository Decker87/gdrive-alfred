import requests
import argparse
import json
import re

# When run, this script creates a new release in the GH repo!

def createRelease(ghUser, ghToken, versionStr, name):
    print(ghUser)
    print(ghToken)
    auth = requests.auth.HTTPBasicAuth(ghUser, ghToken)
    url = "https://api.github.com/repos/Decker87/gdrive-alfred/releases"
    data = {
        "tag_name": versionStr,
        "name": name,
        "draft": True,
    }
    r = requests.post(url, auth=auth, json = data)
    open("temp.txt", "w").write(json.dumps(r.json(), indent=2))
    if r.status_code == 201:
        print(json.dumps(r.json(), indent=4))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("GITHUB_USER", help="Github username.")
    parser.add_argument("GITHUB_TOKEN", help="Personal access token for Github.")
    parser.add_argument("VERSION", help="SemVer-style version to use.")
    parser.add_argument("--name", help="Name of the release.", default="default release name")
    args = parser.parse_args()

    # Parse to normal var names
    ghUser = args.GITHUB_USER
    ghToken = args.GITHUB_TOKEN
    version = args.version
    name = args.name
    
    # Do it!
    createRelease(ghUser, ghToken, version, name)

if __name__ == "__main__":
    main()