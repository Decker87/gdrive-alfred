import sys

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")
import requests

# Settings
DLED_WORKFLOW_PATH = "latest/gdrive-alfred.alfredworkflow"
DLED_VERSION_PATH = "latest/VERSION.txt"
CURRENT_VERSION_PATH = "VERSION.txt"

def getCurrentVersion():
    try:
        return open(CURRENT_VERSION_PATH).read().strip()
    except:
        return None

def getDownloadedVersion():
    try:
        return open(DLED_VERSION_PATH).read().strip()
    except:
        return None

def getLatestVersionAndRelease():
    """Returning the release too allows the caller to avoid an extra call to get the download link."""
    r = requests.get("https://api.github.com/repos/Decker87/gdrive-alfred/releases/latest")
    if r.status_code != 200:
        return None
    release = r.json()
    version = release["tag_name"]
    return version, release

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

def getWorkflowUpdateAlfredItem():
    '''Returns None or a dict containing an item for alfred, if there is a newer version.'''
    currentVersion = getCurrentVersion()
    downloadedVersion = getDownloadedVersion()

    if not currentVersion or not downloadedVersion:
        return None

    if not versionIsNewer(currentVersion, downloadedVersion):
        return None

    return {
        "title": "An update is available!",
        "subtitle": "Click here to update from %s to %s." % (currentVersion, downloadedVersion),
        "icon": {"path": "update.png"},
        "arg": "UPDATE",
    }
