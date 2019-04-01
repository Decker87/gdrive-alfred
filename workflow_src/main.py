import pickle
import json
import datetime
import os.path
import os
import errno
import sys
import uuid

# These things may be packaged in pylib_dist folder as part of the release process
sys.path.insert(0, "pylib_dist")
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def auth():
    """Returns a credentials object"""
    scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    # token.pickle stores the user's access and refresh tokens
    try:
        creds = pickle.load(open('token.pickle', 'rb'))
        return creds
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
        pickle.dump(creds, open('token.pickle', 'wb'))

    return creds

def getService(creds):
    """Returns a service object."""
    service = build('drive', 'v3', credentials=creds)
    return service

def constructQuery(tokens):
    """Returns a string suitable for the "q" parameter based on tokens"""
    # each clause is something that gets "OR"ed together
    clauses = []

    # for each token, attempt to include it in any of the fields
    for token in tokens:
        clauses += ["(name contains '%s')" % (token)]
        clauses += ["('%s' in owners)" % (token.capitalize())]
        # Note: fullText will disable sorting
        #clauses += ["(fullText contains '%s')" % (token)]

    q = " or ".join(clauses)
    return q

def searchWithTokens(service, tokens):
    """Returns a list of items, sorted by score."""
    keywordFileFields = ["name", "owners", "spaces", "sharingUser"]
    generalFileFields = ["modifiedTime", "modifiedByMeTime", "viewedByMeTime", "mimeType", "createdTime", "webViewLink", "iconLink"]
    fileFields = keywordFileFields + generalFileFields
    fileFieldsStr = "files(%s)" % (", ".join(fileFields))
    q = constructQuery(tokens)
    results = service.files().list(pageSize=100, fields=fileFieldsStr, orderBy = "modifiedByMeTime desc, modifiedTime desc, ", q = q).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
        return []
    else:
        # Attach scores directly to the items; this is just easier than tracking separately
        for item in items:
            item["score"] = score(item, tokens)

        # Sort by scores
        sortedItems = sorted(items, key = lambda x: x["score"], reverse = True)
        # Record for debugging
        open("last_items.json", "w").write(json.dumps(sortedItems, indent=4, sort_keys=True))
        return sortedItems

def displayItems(items):
    # Pretty print and save
    pretty = json.dumps(items, indent=4, sort_keys=True)
    print(pretty)

def isoToDatetime(isoTimeStr):
    """Returns a datetime object for the given ISO 8601 string as returned by the Google API."""
    # Ex. "2018-11-05T17:59:17.265Z"
    format = "%Y-%m-%dT%H:%M:%S"

    # We need to trim off the milliseconds, as there's no way to interpret it with strptime.
    return datetime.datetime.strptime(isoTimeStr[0:19], format)

def score(item, tokens):
    """Returns an overall relevance score for the item, based on the tokens and other factors.
    Note that these are currently a bunch of hand-tuned heuristics. It can get much smarter if
    needed."""

    # Subscore for token points
    tokenScore = 0.0

    # Weights for different types of hits
    weightNameHit = 5.0
    weightSharingUserHit = 3.0
    weightOwnerHit = 1.0
    totalTokenWeight = sum([weightNameHit, weightSharingUserHit, weightOwnerHit])
    numTokens = len(tokens)

    for token in tokens:
        if token.lower() in item["name"].lower():
            tokenScore += weightNameHit / totalTokenWeight / numTokens
        if "sharingUser" in item and token.lower() in item["sharingUser"].__str__().lower():
            tokenScore += weightSharingUserHit / totalTokenWeight / numTokens
        # consider weighing by how many owners they are - more relevant if it's the only owner
        if token.lower() in item["owners"].__str__().lower():
            tokenScore += weightOwnerHit / totalTokenWeight / numTokens

    # Subscore for recency
    recencyScore = 0.0

    # Weights for different types of hits
    weightCreatedTimeHit = 2.0
    weightModifiedByMeTimeHit = 10.0
    weightViewedByMeTimeHit = 7.0
    weightModifiedTimeHit = 3.0
    totalRecencyWeight = sum([weightCreatedTimeHit, weightModifiedByMeTimeHit, weightViewedByMeTimeHit, weightModifiedTimeHit])

    # Boost scores for past 7 days of activity
    if datetime.datetime.now() - isoToDatetime(item["createdTime"]) <= datetime.timedelta(days = 7):
        recencyScore += weightCreatedTimeHit / totalRecencyWeight

    if "modifiedByMeTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["modifiedByMeTime"]) <= datetime.timedelta(days = 7):
            recencyScore += weightModifiedByMeTimeHit / totalRecencyWeight

    if "viewedByMeTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["viewedByMeTime"]) <= datetime.timedelta(days = 7):
            recencyScore += weightViewedByMeTimeHit / totalRecencyWeight

    if "modifiedTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["modifiedTime"]) <= datetime.timedelta(days = 7):
            recencyScore += weightModifiedTimeHit / totalRecencyWeight

    # Compute final score.
    # Hand-tuned stuff here: Up to a certain number of tokens, we do weight the token score more heavily. However if there are many tokens,
    # we don't want the token score to totally dominate over the recency score.
    tokenScoreWeight = float(min(numTokens, 3))
    recencyScoreWeight = 0.5
    totalScoreWeight = sum([tokenScoreWeight, recencyScoreWeight])

    score = (tokenScoreWeight / totalScoreWeight * tokenScore) + (recencyScoreWeight / totalScoreWeight * recencyScore)
    return score

def getIconPath(item):
    """Returns a file path for a file to use as the icon. May be None."""
    # No way to get an icon if it doesn't have one
    if ("mimeType" not in item) or ("iconLink" not in item):
        return None

    # Always create the icons folder if it doesn't exist
    try:
        os.makedirs("icons")
    except OSError as exc: # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise

    # Check if the icon exists based on the mimeType
    iconPath = "icons/%s.png" % (item["mimeType"].replace("/", "-"))
    if os.path.exists(iconPath):
        return iconPath

    # Grab the icon from the iconLink if we can
    # Intentional lazy import
    import urllib2
    # Default link is to 16px version - get 128 cuz it aint 1993 boi
    response = urllib2.urlopen(item["iconLink"].replace("/16/", "/128/"))
    open(iconPath, "w").write(response.read())
    return iconPath

def recordItemChoices(items):
    """Records in a file all the choices the user had available. This is used
    for recording data about which results were good or not."""
    open("")

def renderForAlfred(items):
    """Returns a list of items in a format conducive to alfred displaying it."""
    # See https://www.alfredapp.com/help/workflows/inputs/script-filter/json/ for format

    # Just to keep alfred quick, limit to top 20
    itemChoices = items[0:20]
    alfredItems = []
    for item in itemChoices:
        alfredItem = {}
        alfredItem["title"] = item["name"]

        # Generate a UUID for the item - useful for recording choice data
        id = uuid.uuid4().hex
        item["uuid"] = id
        # Prepend a UUID to identify the choice later
        alfredItem["arg"] = "%s|%s" % (uuid.uuid4().hex, item["webViewLink"])

        # For the icon, download it if we need to
        iconPath = getIconPath(item)
        if iconPath:
            alfredItem["icon"] = {"path": iconPath}

        alfredItems.append(alfredItem)

    recordItemChoices(itemChoices)

    return json.dumps({"items": alfredItems}, indent=4, sort_keys=True)

def tokenize(s):
    '''Returns a list of strings that are tokens'''
    # Don't count tokens under 3 chars; they will produce too much noise in the search
    return [token for token in s.split(" ") if len(token) >= 3]

def main():
    # Get input string as first arg and tokenize
    # Early exits - still need to return empty results
    if len(sys.argv) < 2:
        print(renderForAlfred([]))
        return

    tokens = tokenize(sys.argv[1])
    if len(tokens) < 1:
        print(renderForAlfred([]))
        return

    # We have valid tokens so let's do it
    creds = auth()
    service = getService(creds)
    sortedItems = searchWithTokens(service, tokens)

    # Output stuff to STDOUT
    print(renderForAlfred(sortedItems))
    #displayItems(sortedItems)

if __name__ == '__main__':
    main()
