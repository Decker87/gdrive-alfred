import requests
import argparse
import json
import re
import os

# When run, this script creates a new release in the GH repo!

def createRelease(ghUser, ghToken, version, name):
    auth = requests.auth.HTTPBasicAuth(ghUser, ghToken)
    url = "https://api.github.com/repos/Decker87/gdrive-alfred/releases"
    data = {
        "tag_name": version,
        "name": name,
        "draft": True,
    }
    r = requests.post(url, auth=auth, json = data)
    if r.status_code == 201:
        return r.json()

    print("ERROR: Code %i returned." % (r.status_code))
    print(json.dumps(r.json(), indent=4))
    return None

def addAssetToRelease(ghUser, ghToken, releaseId, assetPath):
    url = "https://uploads.github.com/repos/Decker87/gdrive-alfred/releases/%i/assets" % (releaseId)
    data = open(assetPath, "rb")
    headers = {"Content-Type": "application/zip"}
    params = {"name": os.path.basename(assetPath)}
    auth = requests.auth.HTTPBasicAuth(ghUser, ghToken)
    r = requests.post(url, data=data, headers=headers, params=params, auth=auth)
    if r.status_code == 201:
        return r.json()
    
    print("ERROR: Code %i returned." % (r.status_code))
    print(json.dumps(r.json(), indent=4))
    None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("GITHUB_USER", help="Github username.")
    parser.add_argument("GITHUB_TOKEN", help="Personal access token for Github.")
    parser.add_argument("VERSION", help="SemVer-style version to use.")
    parser.add_argument("--name", help="Name of the release.", default="default release name")
    parser.add_argument("--asset-path", help="Path to asset to add.", default=None)
    args = parser.parse_args()

    # Parse to normal var names
    ghUser = args.GITHUB_USER
    ghToken = args.GITHUB_TOKEN
    version = args.VERSION
    name = args.name
    assetPath = args.asset_path
    
    # Do it!
    release = createRelease(ghUser, ghToken, version, name)
    if not release:
        return
    if assetPath:
        addAssetToRelease(ghUser, ghToken, release["id"], assetPath)

if __name__ == "__main__":
    main()