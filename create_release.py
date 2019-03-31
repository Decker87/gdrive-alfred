import requests
import argparse
import json

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
    print(r)
    open("temp.txt", "w").write(json.dumps(r.json(), indent=2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("GITHUB_USER", help="Github username.")
    parser.add_argument("GITHUB_TOKEN", help="Personal access token for Github.")
    parser.add_argument("VERSION", help="SemVer-style version to use.")
    parser.add_argument("NAME", nargs='?', help="Name of the release.", default="default name")
    args = parser.parse_args()
    
    createRelease(args.GITHUB_USER, args.GITHUB_TOKEN, args.VERSION, args.NAME)

if __name__ == "__main__":
    main()