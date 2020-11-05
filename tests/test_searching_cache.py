import ujson

exit()

cache = ujson.load(open('cache.json'))

# {
#     "mimeType": "application/vnd.google-apps.spreadsheet", 
#     "owners": [
#         {
#             "emailAddress": "sushmita.subramanian@gusto.com", 
#             "displayName": "Sushmita Subramanian"
#         }
#     ], 
#     "modifiedByMeTime": "2018-08-22T18:42:59.924Z", 
#     "name": "Payroll Vision Quest", 
#     "modifiedTime": "2018-09-11T00:27:55.538Z", 
#     "webViewLink": "https://docs.google.com/spreadsheets/d/1DeYKe9FA6vvjteYUcK4qKKSJ1ViJGk_LjSgmVJL1DAY/edit?usp=drivesdk", 
#     "iconPath": "icons/application-vnd.google-apps.spreadsheet.png", 
#     "createdTime": "2018-08-20T21:50:41.265Z", 
#     "viewedByMeTime": "2018-08-22T18:42:59.924Z", 
#     "id": "1DeYKe9FA6vvjteYUcK4qKKSJ1ViJGk_LjSgmVJL1DAY", 
#     "sharingUser": {
#         "displayName": ""
#     }, 
#     "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.spreadsheet"
# }, 

r = []

tokens = ["adam", "brandon"]

def tokensMatchItem(item, tokens):
    for token in tokens:
        if token in item['name'].lower():
            return True
        if 'owners' in item:
            if token in item['owners'][0]['emailAddress'].lower():
                return True
            if token in item['owners'][0]['displayName'].lower():
                return True
        if 'sharingUser' in item:
            if 'displayName' in item['sharingUser'] and token in item['sharingUser']['displayName'].lower():
                return True
            if 'emailAddress' in item['sharingUser'] and token in item['sharingUser']['emailAddress'].lower():
                return True

    return False

for item in cache:
    if tokensMatchItem(item, tokens):
        r.append(item)

print(len(r))
