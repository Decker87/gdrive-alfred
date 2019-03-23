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
    keywordFileFields = ["name", "owners", "spaces", "sharingUser"]
    generalFileFields = ["modifiedTime", "modifiedByMeTime", "viewedByMeTime", "kind", "createdTime"]
    fileFields = keywordFileFields + generalFileFields
    fileFieldsStr = "files(%s)" % (", ".join(fileFields))
    q = constructQuery(tokens)
    results = service.files().list(pageSize=10, fields=fileFieldsStr, orderBy = "modifiedByMeTime desc, modifiedTime desc, ", q = q).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        pretty = json.dumps(items, indent=4, sort_keys=True)
        print(pretty)
        open("example_items.json", "w").write(pretty)
        for item in items:
            print("score: %i" % (score(item, tokens)))

def isoToDatetime(isoTimeStr):
    """Returns a datetime object for the given ISO 8601 string as returned by the Google API."""
    # Ex. "2018-11-05T17:59:17.265Z"
    format = "%Y-%m-%dT%H:%M:%S"

    # We need to trim off the milliseconds, as there's no way to interpret it with strptime.
    return datetime.datetime.strptime(isoTimeStr[0:19], format)

# TODO: Score according to which result is the most complete (i.e. has more keywords or unique keywords)
def score(item, tokens):
    """Returns an overall relevance score for the item, based on the tokens and other factors.
    Note that these are currently a bunch of hand-tuned heuristics. It can get much smarter if
    needed."""
    # TODO: Make score on interval of 0.0 to 1.0
    score = 0

    # For each token, add points
    for token in tokens:
        if token.lower() in item["name"].lower():
            score += 5
        if "sharingUser" in item and token.lower() in item["sharingUser"].__str__().lower():
            score += 3
        # consider weighing by how many owners they are - more relevant if it's the only owner
        if token.lower() in item["owners"].__str__().lower():
            score += 1

    # Add more points for being modified by me, being more recent, etc.
    # TODO: Weight this and token based points so it doesn't become irrelevant with high number of tokens
    
    # Boost scores for past 7 days of activity
    if datetime.datetime.now() - isoToDatetime(item["createdTime"]) <= datetime.timedelta(days = 7):
        score += 2

    if "modifiedByMeTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["modifiedByMeTime"]) <= datetime.timedelta(days = 7):
            score += 10

    if "viewedByMeTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["viewedByMeTime"]) <= datetime.timedelta(days = 7):
            score += 7

    if "modifiedTime" in item:
        if datetime.datetime.now() - isoToDatetime(item["modifiedTime"]) <= datetime.timedelta(days = 7):
            score += 3

    return score

def main():
    creds = auth()
    service = getService(creds)
    searchWithTokens(service, ["adam"])

if __name__ == '__main__':
    main()