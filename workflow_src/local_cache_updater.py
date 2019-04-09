import cPickle
import time
import signal
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

CACHE_FILEPATH = "cache.pickle"

def getService():
    creds = cPickle.load(open('token.pickle', 'rb'))
    service = build('drive', 'v3', credentials=creds)
    return service

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
        items += result["files"]
        print("items is now %i long" % (len(items)))
        if "nextPageToken" in result:
            nextPageToken = result["nextPageToken"]
        else:
            return items

def updateCache(service):
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
        time.sleep(10)

if __name__ == '__main__':
    main()
