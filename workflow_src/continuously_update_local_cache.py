import cPickle
import time
import signal
import os
import requests
import sys
import json
import traceback
import argparse

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

CACHE_FILEPATH = "cache.pickle"
CACHE_JSON_FILEPATH = "cache.json"

# Stuff to gracefully handle SIGINT and SIGTERM
waitingToDie = False    # Is this true of my life?
def gracefullyDie(signum, frame):
    global waitingToDie
    print("Waiting to die gracefully...")
    waitingToDie = True
signal.signal(signal.SIGINT, gracefullyDie)
signal.signal(signal.SIGTERM, gracefullyDie)

# Cleaner to just have these flags be global
debugMode = False
getAllFields = False

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

# Memoize to save time traversing the same parents, such as "My Drive"
# Looks like: {id: {isReadable: True|False, name: bla|None, realParentId: sdaf|None}}
knownFolderInfo = {}

def getFolderInfo(service, id):
    global knownFolderInfo

    if id in knownFolderInfo:
        return knownFolderInfo[id]

    fields = "*" if getAllFields else "parents, name"

    try:
        result = service.files().get(fileId = id, fields=fields, supportsTeamDrives = True).execute()
    except:
        knownFolderInfo[id] = {"isReadable": False, "name": None, "realParentId": None}
        return knownFolderInfo[id]
    
    # Edge cases: there can be multiple parents and some files are their own parent
    # In the case of multiple parents, we select the first.
    # If the file is its own parent, it has no "Real" parent
    if "parents" in result and result["parents"][0] != id:
        realParentId = result["parents"][0]
    else:
        realParentId = None
    
    knownFolderInfo[id] = {"isReadable": True, "name": result["name"], "realParentId": realParentId}

    return knownFolderInfo[id]

def clearKnownFolderInfoCache():
    global knownFolderInfo
    knownFolderInfo.clear()

def getFullParentList(service, parents):
    parentNameList = []

    currentParentId = parents[0]
    while not waitingToDie:
        folderInfo = getFolderInfo(service, currentParentId)
        
        # If we can't read it, then we can't do anything with it
        if not folderInfo["isReadable"]:
            break
        
        # Add it
        parentNameList.insert(0, folderInfo["name"])

        # Set up next iteration
        if folderInfo["realParentId"]:
            currentParentId = folderInfo["realParentId"]
        else:
            break

    return parentNameList

def getItems(service):
    keywordFileFields = ["name", "owners(displayName, emailAddress)", "spaces", "sharingUser(displayName, emailAddress)"]
    generalFileFields = ["modifiedTime", "modifiedByMeTime", "viewedByMeTime", "mimeType", "createdTime", "webViewLink", "iconLink", "parents"]
    fileFields = keywordFileFields + generalFileFields
    fileFieldsStr = "files(%s)" % (", ".join(fileFields))
    fields = "nextPageToken, " + fileFieldsStr

    # Debug mode overrides
    pageSize = 10 if debugMode else 1000
    fields = "*" if getAllFields else fields

    items = []

    # Continuously query, adding to items
    nextPageToken = None
    while not waitingToDie:
        result = service.files().list(includeTeamDriveItems = True, supportsTeamDrives = True, fields = fields, pageToken = nextPageToken,
            pageSize = pageSize, orderBy = "viewedByMeTime asc", q = "viewedByMeTime > '1970-01-01T00:00:00.000Z'").execute()

        if debugMode:
            json.dump(result, open("last_result.json", "w"), indent = 4)

        # Enrich with icon paths
        for item in result["files"]:
            item["iconPath"] = getIconPath(item)

        # Enrich with full parent tree
        for item in result["files"]:
            if "parents" in item:
                fullParentList = getFullParentList(service, item["parents"])

                if len(fullParentList) > 0:
                    item["fullParentList"] = fullParentList
                item.pop("parents") # Extra data, not needed

        items += result["files"]
        print("items is now %i long" % (len(items)))
        if not debugMode and "nextPageToken" in result:
            nextPageToken = result["nextPageToken"]
        else:
            return items

def updateCache(service):
    print("Updating local cache...")
    items = getItems(service)
    cPickle.dump(items, open(CACHE_FILEPATH, "w"))
    json.dump(items, open(CACHE_JSON_FILEPATH, "w"), indent = 4)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Debug mode", action="store_true")
    parser.add_argument("--all-fields", help="Query for all fields", action="store_true")
    args = parser.parse_args()

    global debugMode, getAllFields
    debugMode = args.debug
    getAllFields = args.all_fields

    """Continuously updates the cache."""
    service = getService()
    while not waitingToDie:
        try:
            # Clear the memoization table of directory info
            clearKnownFolderInfoCache()
            updateCache(service)
        except Exception:
            traceback.print_exc()
        if debugMode:
            break
        time.sleep(10)

if __name__ == '__main__':
    main()
