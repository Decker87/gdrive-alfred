import requests
from zipfile import ZipFile
from StringIO import StringIO

# Overall design in this file = catch exceptions at high level and abort if there are any

def getCurrentVersion():
    return open("VERSION.txt", "r").read()

def getLatestRelease():
    r = requests.get("https://api.github.com/repos/Decker87/gdrive-alfred/releases/latest")
    if r.status_code != 200:
        return None
    return r.json()

def versionIsNewer(oldVersion, newVersion):
    oldMajor, oldMinor, oldPatch = [int(x) for x in oldVersion.split(".")]
    newMajor, newMinor, newPatch = [int(x) for x in newVersion.split(".")]

    if newMajor > oldMajor:
        return True
    if newMajor < oldMajor:
        return False
    if newMinor > oldMinor:
        return True
    if newMinor < oldMinor:
        return False
    if newPatch > oldPatch:
        return True

    return False

def updateToRelease(release):
    assetName = "gdrive-alfred.alfredworkflow"

    # Determine download URL
    if "assets" not in release:
        print("ERROR: Release has no assets.")
        return False

    for asset in release["assets"]:
        if asset["name"] == assetName:
            downloadUrl = asset["browser_download_url"]
            break
    else:
        print("ERROR: No asset called '%s'." % (assetName))
        return False

    # Download it to memory
    r = requests.get(downloadUrl)
    if r.status_code != 200:
        print("ERROR: Response code %i while downloading '%s'." % (r.status_code, assetName))
        return False

    # Unzip it from memory
    ZipFile(StringIO(r.content)).extractall(".")
    print("INFO: Updated Adam's drive search to %s" % (release["tag_name"]))

def UpdateToLatestVersion():
    currentVersion = getCurrentVersion()
    latestRelease = getLatestRelease()
    latestVersion = latestRelease["tag_name"]

    if versionIsNewer(currentVersion, latestVersion):
        updateToRelease(latestRelease)

def main():
    UpdateToLatestVersion()

if __name__ == "__main__":
    main()
