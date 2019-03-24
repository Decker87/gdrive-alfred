from __future__ import print_function
import pickle
import os.path
import json
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def auth():
    """Returns a credentials object"""

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

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
    generalFileFields = ["modifiedTime", "modifiedByMeTime", "viewedByMeTime", "mimeType", "createdTime", "webViewLink"]
    fileFields = keywordFileFields + generalFileFields
    fileFieldsStr = "files(%s)" % (", ".join(fileFields))
    q = constructQuery(tokens)
    results = service.files().list(pageSize=100, fields=fileFieldsStr, orderBy = "modifiedByMeTime desc, modifiedTime desc, ", q = q).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
        return []
    else:
        # Attach scores directly to the items; this is just easier
        for item in items:
            item["score"] = score(item, tokens)

        # Sort by scores
        sortedItems = sorted(items, key = lambda x: x["score"], reverse = True)
        return sortedItems

def displayItems(items):
    # Pretty print and save
    pretty = json.dumps(items, indent=4, sort_keys=True)
    print(pretty)
    open("last_items.json", "w").write(pretty)

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

def renderForAlfred(items):
    """Returns a list of items in a format conducive to alfred displaying it."""
    # See https://www.alfredapp.com/help/workflows/inputs/script-filter/json/ for format, something like:
    # {"items": [
    #     {
    #         "uid": "desktop",
    #         "type": "file",
    #         "title": "Desktop",
    #         "subtitle": "~/Desktop",
    #         "arg": "~/Desktop",
    #         "autocomplete": "Desktop",
    #         "icon": {
    #             "type": "fileicon",
    #             "path": "~/Desktop"
    #         }
    #     }
    # ]}

    # Just to keep alfred quick, limit to top 20
    alfredItems = []

    for item in items[0:20]:
        alfredItem = {}
        alfredItem["title"] = item["name"]
        alfredItem["arg"] = item["webViewLink"]
        # TODO: Add icon

        alfredItems.append(alfredItem)

    return json.dumps({"items": alfredItems})

def main():
    creds = auth()
    service = getService(creds)
    sortedItems = searchWithTokens(service, ["eoy"])
    displayItems(sortedItems)

if __name__ == '__main__':
    main()