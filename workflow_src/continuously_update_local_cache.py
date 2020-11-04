# Exit fast if it's already running. Taken from https://stackoverflow.com/a/384493
import os
import fcntl
lock_file_pointer = os.open('continuously_update_local_cache.lock', os.O_WRONLY | os.O_CREAT)
try:
    fcntl.lockf(lock_file_pointer, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    exit()

# OK, we're the only one running, so go ahead and do normal stuff
import pickle
import time
import signal
import sys
import json
import traceback
import argparse

# Have to look in local folder - CI will pip install these locally
libAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.sep + "pylib_dist"
sys.path.insert(0, libAbsPath)
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Globals / settings
CACHE_FILEPATH = "cache.json"
EXCEPTIONLOG_FILEPATH = "exceptions.log"
FLOW_TIMEOUT = 60

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
spoofServer = False

def getService():
    """Returns a service object."""
    scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    # token.pickle stores the user's access and refresh tokens
    try:
        creds = pickle.load(open('token.pickle', 'rb'))
    except:
        creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # Custom signal logic to keep from blocking forever
        def alarmHandler(signum, frame): exit()
        signal.signal(signal.SIGALRM, alarmHandler)

        signal.alarm(FLOW_TIMEOUT)  # Set an alarm
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server()
        signal.alarm(0) # Cancel the alarm

        # Save the credentials for the next run
        pickle.dump(creds, open('token.pickle', 'wb'))

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
        if not spoofServer:
            result = service.files().list(includeTeamDriveItems = True, supportsTeamDrives = True, fields = fields, pageToken = nextPageToken,
                pageSize = pageSize, orderBy = "viewedByMeTime asc", q = "viewedByMeTime > '1970-01-01T00:00:00.000Z'").execute()
        else:
            result = json.load(open("../test_data/files_list_resp.json"))

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
            time.sleep(5)
            nextPageToken = result["nextPageToken"]
        else:
            return items

def updateCache(service):
    print("Updating local cache...")
    items = getItems(service)
    json.dump(items, open(CACHE_FILEPATH, "w"), indent = 4)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Debug mode. Will only run once and get 10 items.", action="store_true")
    parser.add_argument("--all-fields", help="Query for all fields", action="store_true")
    parser.add_argument("--spoof-server", help="Simulate interactions with remote server", action="store_true")
    parser.add_argument("--just-once", help="Just update cache once and exit", action="store_true")
    args = parser.parse_args()

    global debugMode, getAllFields, spoofServer
    debugMode = args.debug
    getAllFields = args.all_fields
    spoofServer = args.spoof_server

    """Continuously updates the cache."""
    service = getService() if not spoofServer else None
    while not waitingToDie:
        try:
            # Clear the memoization table of directory info
            clearKnownFolderInfoCache()
            updateCache(service)
        except Exception:
            exceptionStr = "%s\n%s%s" % ("#"*40, traceback.format_exc(), "#"*40)
            print(exceptionStr)
            open(EXCEPTIONLOG_FILEPATH, "a").write(exceptionStr + "\n")
        if debugMode or args.just_once:
            break
        time.sleep(10)

if __name__ == '__main__':
    main()
