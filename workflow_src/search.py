import datetime
import sys

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")
import ujson

# Settings
CACHE_FILEPATH = "cache.json"
MIN_TOKEN_LENGTH = 2

def isoToDatetime(isoTimeStr):
    """Returns a datetime object for the given ISO 8601 string as returned by the Google API."""
    # Ex. "2018-11-05T17:59:17.265Z"
    format = "%Y-%m-%dT%H:%M:%S"

    # We need to trim off the milliseconds, as there's no way to interpret it with strptime.
    return datetime.datetime.strptime(isoTimeStr[0:19], format)

def score(item, tokens, zeroOnZeroTokenScore = False):
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
        if "owners" in item and token.lower() in item["owners"].__str__().lower():
            tokenScore += weightOwnerHit / totalTokenWeight / numTokens

    if zeroOnZeroTokenScore and tokenScore == 0.0:
        return 0.0

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

def tokenize(s):
    '''Returns a list of strings that are tokens'''
    return [token for token in s.split(" ") if len(token) >= MIN_TOKEN_LENGTH]

def searchLocalCache(query):
    """query is just a string, needs to be tokenized."""
    tokens = tokenize(query)
    try:
        items = ujson.load(open(CACHE_FILEPATH))
        if items == None:   # If cache exists but reads "null"
            return None
    except:
        return None

    # See if any tokens match a mime type, use the last one
    mimeTypeKeywords = {
        "sheet": "application/vnd.google-apps.spreadsheet",
        "slide": "application/vnd.google-apps.presentation",
        "doc": "application/vnd.google-apps.document",
        "folder": "application/vnd.google-apps.folder",
    }
    mimeTypeRequired = None

    for token in tokens:
        if token in mimeTypeKeywords:
            mimeTypeRequired = mimeTypeKeywords[token]

    # Remove any tokens that were just mime type filters
    tokens = [token for token in tokens if token not in mimeTypeKeywords]

    # Attach scores directly to the items; this is just easier than tracking separately
    tokenMatchedItems = []
    for item in items:
        if mimeTypeRequired and "mimeType" in item and item["mimeType"] != mimeTypeRequired:
            continue

        item["score"] = score(item, tokens, zeroOnZeroTokenScore = True)
        if item["score"] > 0.0:
            tokenMatchedItems.append(item)

    # Sort by scores
    sortedItems = sorted(tokenMatchedItems, key = lambda x: (x["score"], x["viewedByMeTime"]), reverse = True)
    return sortedItems

def convertToAlfredItem(googleItem):
    """Converts a google item to alfred item."""

    alfredItem = {
        "title": googleItem["name"],
        "arg": googleItem["webViewLink"],
    }

    # For the icon, download it if we need to
    if "iconPath" in googleItem:
        alfredItem["icon"] = {"path": googleItem["iconPath"]}

    # Use parent list as subtitle
    if "fullParentList" in googleItem:
        alfredItem["subtitle"] = " >> ".join(googleItem["fullParentList"])

    return alfredItem

def search(query):
    """Returns a list of items in alfred format from the search."""

    # If we got "None", it means the cache wasn't readable
    googleItems = searchLocalCache(query)
    if googleItems == None:
        return [{
            "title": "Updating cache, try again in a few minutes.",
            "subtitle": "This is normal on first installation.",
            "icon": {"path": "hourglass.png"},
        }]

    # Else we just need to convert them all
    return [convertToAlfredItem(i) for i in googleItems]
