import cPickle
import time
import signal
import os
import requests
import sys

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

CACHE_FILEPATH = "cache.pickle"

def getService():
    """Returns a service object."""
    scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    # token.pickle stores the user's access and refresh tokens
    try:
        creds = cPickle.load(open('token.pickle', 'rb'))
    except:
        creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        cPickle.dump(creds, open('token.pickle', 'wb'))

    service = build('drive', 'v3', credentials = creds)
    return service

def getIconPath(item):
    """Returns a file path for a file to use as the icon. May be None."""
    # No way to get an icon if it doesn't have one
    if ("mimeType" not in item) or ("iconLink" not in item):
        return None

    # Always create the icons folder if it doesn't exist
    try:
        os.makedirs("icons")
    except OSError:
        pass    # This happens if it already exists

    # Check if the icon exists based on the mimeType
    iconPath = "icons/%s.png" % (item["mimeType"].replace("/", "-"))
    if os.path.exists(iconPath):
        return iconPath

    # Grab the icon from the iconLink if we can
    # Default link is to 16px version - get 128 cuz it aint 1993 boi
    r = requests.get(item["iconLink"].replace("/16/", "/128/"))
    open(iconPath, "wb").write(r.content)
    return iconPath

def getItems(service):
    keywordFileFields = ["name", "owners(displayName, emailAddress)", "spaces", "sharingUser(displayName, emailAddress)"]
    generalFileFields = ["modifiedTime", "modifiedByMeTime", "viewedByMeTime", "mimeType", "createdTime", "webViewLink", "iconLink"]
    fileFields = keywordFileFields + generalFileFields
    fileFieldsStr = "files(%s)" % (", ".join(fileFields))
    fields = "nextPageToken, " + fileFieldsStr

    items = []

    # Continuously query, adding to items
    nextPageToken = None
    while True:
        result = service.files().list(includeTeamDriveItems = True, supportsTeamDrives = True, fields = fields, pageToken = nextPageToken,
            pageSize = 1000, orderBy = "viewedByMeTime asc", q = "viewedByMeTime > '1970-01-01T00:00:00.000Z'").execute()

        # Enrich with icon paths
        for item in result["files"]:
            item["iconPath"] = getIconPath(item)

        items += result["files"]
        print("items is now %i long" % (len(items)))
        if "nextPageToken" in result:
            nextPageToken = result["nextPageToken"]
        else:
            return items

def updateCache(service):
    print("Updating local cache...")
    items = getItems(service)
    cPickle.dump(items, open(CACHE_FILEPATH, "w"))

# Stuff to gracefully handle SIGINT and SIGTERM
waitingToDie = False    # Is this true of my life?
def gracefullyDie(signum, frame):
    global waitingToDie
    print("Waiting to die gracefully...")
    waitingToDie = True
signal.signal(signal.SIGINT, gracefullyDie)
signal.signal(signal.SIGTERM, gracefullyDie)

def main():
    """Continuously updates the cache."""
    service = getService()
    while not waitingToDie:
        try:
            updateCache(service)
        except:
            pass
        time.sleep(1)

if __name__ == '__main__':
    main()
