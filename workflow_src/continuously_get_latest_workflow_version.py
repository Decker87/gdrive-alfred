import sys
import time
import os
import signal
import traceback

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")
import requests

# Settings
LATEST_WORKFLOW_PATH = "latest/gdrive-alfred.alfredworkflow"
LATEST_VERSION_PATH = "latest/VERSION.txt"
ASSET_NAME = "gdrive-alfred.alfredworkflow"
EXCEPTIONLOG_FILEPATH = "exceptions.log"
CHECK_PERIOD_SECONDS = 5*60

def ensureDirectoriesExist():
    try:
        os.makedirs("latest")
    except OSError:
        pass    # This happens if it already exists

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

def getDownloadedVersion():
    try:
        return open(LATEST_VERSION_PATH).read().strip()
    except:
        return None

def getLatestWorkflow():
    # First get the latest release from GH
    r = requests.get("https://api.github.com/repos/Decker87/gdrive-alfred/releases/latest")
    if r.status_code != 200:
        return False
    release = r.json()
    latestVersion = release["tag_name"]

    # Check if it's actually newer than what we have already
    downloadedVersion = getDownloadedVersion()
    if downloadedVersion and not versionIsNewer(downloadedVersion, latestVersion):
        print("INFO: Latest version %s is not newer than downloaded version %s, not downloading." % (latestVersion, downloadedVersion))
        return True

    # Determine download URL
    if "assets" not in release:
        print("ERROR: Release has no assets.")
        return False

    for asset in release["assets"]:
        if asset["name"] == ASSET_NAME:
            downloadUrl = asset["browser_download_url"]
            break
    else:
        print("ERROR: No asset called '%s'." % (ASSET_NAME))
        return False

    # Now download and store version string
    r = requests.get(downloadUrl)
    if r.status_code != 200:
        print("ERROR: Response code %i while downloading '%s'." % (r.status_code, ASSET_NAME))
        return False

    # Save it
    open(LATEST_WORKFLOW_PATH, "wb").write(r.content)
    open(LATEST_VERSION_PATH, "w").write(latestVersion)
    print("SUCCESS: Downloaded latest workflow version.")
    return True

def main():
    """Continuously gets the latest release."""
    while True:
        try:
            ensureDirectoriesExist()
            getLatestWorkflow()
        except Exception:
            exceptionStr = "%s\n%s%s" % ("#"*40, traceback.format_exc(), "#"*40)
            print(exceptionStr)
            open(EXCEPTIONLOG_FILEPATH, "a").write(exceptionStr + "\n")
        print("INFO: Waiting %i seconds to get latest again." % (CHECK_PERIOD_SECONDS))
        time.sleep(CHECK_PERIOD_SECONDS)

if __name__ == "__main__":
    main()
