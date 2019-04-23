import sys
import uuid
import json
import argparse

import search
from workflow_version_utils import *

# Settings
MAX_ALFRED_ITEMS = 20

# Have to look in local folder - CI will pip install these locally
sys.path.insert(0, "pylib_dist")

def action_search(query):
    fullAlfredItemList = []
    searchAlfredItems = search.search(query)
    workflowUpdateAlfredItem = getWorkflowUpdateAlfredItem()

    if workflowUpdateAlfredItem:
        fullAlfredItemList.append(workflowUpdateAlfredItem)

    if searchAlfredItems:
        fullAlfredItemList += searchAlfredItems[:MAX_ALFRED_ITEMS]

    # Add UUIDs so we can record easily what was chosen when
    for item in fullAlfredItemList:
        if "arg" in item:
            item["arg"] = "%s|%s" % (uuid.uuid4().hex, item["arg"])

    # Print for Alfred
    # See https://www.alfredapp.com/help/workflows/inputs/script-filter/json/ for format
    print(json.dumps({"items": fullAlfredItemList}, indent = 4))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Action", default="search", choices=["search"])
    parser.add_argument("--query", help="Query if searching")
    args = parser.parse_args()

    if args.action == "search" and args.query != None:
        return action_search(args.query)

if __name__ == '__main__':
    main()
