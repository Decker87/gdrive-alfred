import requests
import argparse
import json
import re
import webbrowser

# When run, this script creates a new release in the GH repo!

def getLatestRelease(ghUser, ghToken):
    auth = requests.auth.HTTPBasicAuth(ghUser, ghToken)
    url = "https://api.github.com/repos/Decker87/gdrive-alfred/releases/latest"
    r = requests.get(url, auth=auth)
    return r.json()

def getLatestReleaseVersion(ghUser, ghToken):
    latestRelease = getLatestRelease(ghUser, ghToken)
    return latestRelease["tag_name"]

def getIncrementedVersion(ghUser, ghToken):
    latestVersion = getLatestReleaseVersion(ghUser, ghToken)
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", latestVersion)
    major, minor, patch = [int(x) for x in m.groups()]
    patch += 1
    return "%i.%i.%i" % (major, minor, patch)

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
        # The html_url will by default be a view of the release, but we want to jump to editing it
        editUrl = r.json()["html_url"].replace("/releases/tag/", "/releases/edit/")
        webbrowser.open_new_tab(editUrl)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("GITHUB_USER", help="Github username.")
    parser.add_argument("GITHUB_TOKEN", help="Personal access token for Github.")
    parser.add_argument("--version", help="SemVer-style version to use.")
    parser.add_argument("--name", help="Name of the release.", default="default release name")
    args = parser.parse_args()

    # Parse to normal var names
    ghUser = args.GITHUB_USER
    ghToken = args.GITHUB_TOKEN
    version = args.version
    name = args.name

    # If no version is given, use the latest + 1
    if not version:
        version = getIncrementedVersion(ghUser, ghToken)
    
    # Do it!
    createRelease(ghUser, ghToken, version, name)

if __name__ == "__main__":
    main()