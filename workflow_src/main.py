import cPickle
import pickle
import json
import datetime
import os.path
import os
import errno
import sys
import uuid

CACHE_FILEPATH = "cache.pickle"

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

def searchLocalCache(tokens):
    items = cPickle.load(open(CACHE_FILEPATH))
    
    # Attach scores directly to the items; this is just easier than tracking separately
    tokenMatchedItems = []
    for item in items:
        item["score"] = score(item, tokens, zeroOnZeroTokenScore = True)
        if item["score"] > 0.0:
            tokenMatchedItems.append(item)

    # Sort by scores
    sortedItems = sorted(tokenMatchedItems, key = lambda x: x["score"], reverse = True)
    return sortedItems

def recordItemChoices(items):
    """Records in a file all the choices the user had available. This is used
    for recording data about which results were good or not."""
    open("itemChoices.jsonlog", "a").write(json.dumps(items))

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
        if "iconPath" in item:
            alfredItem["icon"] = {"path": item["iconPath"]}

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
    sortedItems = searchLocalCache(tokens)

    # Output stuff to STDOUT
    print(renderForAlfred(sortedItems))

if __name__ == '__main__':
    main()
