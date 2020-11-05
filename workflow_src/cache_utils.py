import sqlite3, json
from sqlite3 import Error

cacheFilename = 'cache.db'

schema = {
    'fields': [
        { 'name': 'id', 'type': 'TEXT NOT NULL UNIQUE'},
        { 'name': 'name', 'type': 'TEXT'},
        { 'name': 'createdTime', 'type': 'TEXT'},
        { 'name': 'modifiedTime', 'type': 'TEXT'},
        { 'name': 'viewedByMeTime', 'type': 'TEXT'},
        { 'name': 'ownerEmail', 'type': 'TEXT'},
        { 'name': 'ownerName', 'type': 'TEXT'},
        { 'name': 'sharingUserEmail', 'type': 'TEXT'},
        { 'name': 'sharingUserName', 'type': 'TEXT'},
        { 'name': 'mimeType', 'type': 'TEXT'},
        { 'name': 'webViewLink', 'type': 'TEXT'},
        { 'name': 'iconPath', 'type': 'TEXT'},
        { 'name': 'iconLink', 'type': 'TEXT'},
    ],
    'primaryKey': 'id',
    'tableName': 'cacheItems',
}

def getConnection():
    return sqlite3.connect(cacheFilename)

def createTable():
    '''Creates the DB and main driveItems table if they don't exist already.'''

    # Should look something like this.
    # CREATE TABLE IF NOT EXISTS "cacheItems" (
    #   "id" TEXT NOT NULL UNIQUE,
    #   "name" TEXT,
    #   "createdTime" TEXT,
    #   "modifiedTime" TEXT,
    #   "viewedByMeTime" TEXT,
    #   "ownerEmail" TEXT,
    #   "ownerName" TEXT,
    #   "sharingUserEmail" TEXT,
    #   "sharingUserName" TEXT,
    #   "mimeType" TEXT,
    #   "webViewLink" TEXT,
    #   "iconPath" TEXT,
    #   "iconLink" TEXT,
    #   PRIMARY KEY("id")
    # );

    sql = 'CREATE TABLE IF NOT EXISTS "{}" (\n{},\n  PRIMARY KEY("{}")\n);'.format(
        schema['tableName'],
        ',\n'.join(['  "%s" %s' % (field['name'], field['type']) for field in schema['fields']]),
        schema['primaryKey'],
    )

    print("###### SQL ######")
    print(sql)
    print("#################")

    try:
        conn = getConnection()
        conn.cursor().execute(sql)
        conn.commit()
        conn.close()
        return True
    except Error as e:
        print("Unhandled error: %s" % e)
        exit()
        return False

def updateCache(driveItems):
    '''Creates the cache and driveItems table if they don't exist, then updates the cache.
    driveItems is expected to be in the format returned from the Drive API'''

    createTable()

    conn = getConnection()

    sql = '''REPLACE INTO cacheItems(id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,mimeType,webViewLink,iconPath,iconLink)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?);'''

    for driveItem in driveItems:
        print("Working on another drive item.")
        #id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,mimeType,webViewLink,iconPath,iconLink
        values = []
        values.append(driveItem['id'])
        values.append(driveItem.get('name', None))
        values.append(driveItem.get('createdTime', None))
        values.append(driveItem.get('modifiedTime', None))
        values.append(driveItem.get('viewedByMeTime', None))
        if 'owners' in driveItem:
            if 'emailAddress' in driveItem['owners'][0] and driveItem['owners'][0]['emailAddress'] != "":
                values.append(driveItem['owners'][0]['emailAddress'])
            else:
                values.append(None)
            if 'displayName' in driveItem['owners'][0] and driveItem['owners'][0]['displayName'] != "":
                values.append(driveItem['owners'][0]['displayName'])
            else:
                values.append(None)
        else:
            values.append(None)
            values.append(None)
        if 'sharingUser' in driveItem:
            if 'emailAddress' in driveItem['sharingUser'] and driveItem['sharingUser']['emailAddress'] != "":
                values.append(driveItem['sharingUser']['emailAddress'])
            else:
                values.append(None)
            if 'displayName' in driveItem['sharingUser'] and driveItem['sharingUser']['displayName'] != "":
                values.append(driveItem['sharingUser']['displayName'])
            else:
                values.append(None)
        else:
            values.append(None)
            values.append(None)
        values.append(driveItem.get('mimeType', None))
        values.append(driveItem.get('webViewLink', None))
        values.append(driveItem.get('iconPath', None))
        values.append(driveItem.get('iconLink', None))

        conn.cursor().execute(sql, tuple(values))
    
    conn.commit()
    conn.close()

def getCacheItemsMatchingTokens(tokens):
    columnsToMatchOn = ['name', 'ownerEmail', 'ownerName', 'sharingUserEmail', 'sharingUserName']
    allColumnNames = [field['name'] for field in schema['fields']]
    clauses = ["  {} like '%' || ? || '%'".format(col) for col in columnsToMatchOn]

    sql = 'SELECT {} FROM cacheItems WHERE\n{}\n;'.format(
        ','.join(allColumnNames),
        ' OR\n'.join(clauses*len(tokens)),
    )

    print("###### SQL ######")
    print(sql)
    print("#################")

    conn = getConnection()
    cur = conn.cursor()
    values = tuple(sorted(tokens*len(columnsToMatchOn))) # We don't care about order, but sorting will put them so all 5 copies of each token are adjacent.
    cur.execute(sql, values)
    rows = cur.fetchall()
    conn.close()

    # Return a list of cache items by using the column names as dict labels
    cacheItems = [dict(zip(allColumnNames, row)) for row in rows]
    return cacheItems

if __name__ == '__main__':
    driveItems = json.load(open('cache.json'))
    updateCache(driveItems)
    cacheItems = getCacheItemsMatchingTokens(["Adam"])
    print(len(cacheItems))
    print(cacheItems[:5])
