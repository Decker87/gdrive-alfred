# Exit fast if it's already running. Taken from https://stackoverflow.com/a/384493
import os
import fcntl
lock_file_pointer = os.open('continuously_get_latest_workflow.lock', os.O_WRONLY | os.O_CREAT)
try:
    fcntl.lockf(lock_file_pointer, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    exit()

# OK, we're the only one running, so go ahead and do normal stuff
import sys
import time
import signal
import traceback
import argparse
from workflow_version_utils import *

# Have to look in local folder - CI will pip install these locally
libAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.sep + "pylib_dist"
sys.path.insert(0, libAbsPath)
import requests

# Settings
ASSET_NAME = "gdrive-alfred.alfredworkflow"
EXCEPTIONLOG_FILEPATH = "exceptions.log"
CHECK_PERIOD_SECONDS = 5*60
debugMode = False
spoofNewerVersion = False

def ensureDirectoriesExist():
    try:
        os.makedirs("latest")
    except OSError:
        pass

def getLatestWorkflow():
    # First get the latest release from GH
    r = getLatestVersionAndRelease()
    if not r:
        return False
    latestVersion, release = r

    if spoofNewerVersion:
        latestVersion = "10.0.0"

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
    open(DLED_WORKFLOW_PATH, "wb").write(r.content)
    open(DLED_VERSION_PATH, "w").write(latestVersion)
    print("SUCCESS: Downloaded latest workflow version.")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Debug mode", action="store_true")
    parser.add_argument("--spoof-newer-version", help="Simulate latest version being very high in number.", action="store_true")
    args = parser.parse_args()

    global debugMode, spoofNewerVersion
    debugMode = args.debug
    spoofNewerVersion = args.spoof_newer_version

    """Continuously gets the latest release."""
    while True:
        try:
            ensureDirectoriesExist()
            getLatestWorkflow()
        except Exception:
            exceptionStr = "%s\n%s%s" % ("#"*40, traceback.format_exc(), "#"*40)
            print(exceptionStr)
            open(EXCEPTIONLOG_FILEPATH, "a").write(exceptionStr + "\n")
        if debugMode:
            break
        print("INFO: Waiting %i seconds to get latest again." % (CHECK_PERIOD_SECONDS))
        time.sleep(CHECK_PERIOD_SECONDS)

if __name__ == "__main__":
    main()
