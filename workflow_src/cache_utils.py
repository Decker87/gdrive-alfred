import sqlite3, json
from sqlite3 import Error

cacheFilename = 'cache.db'

connection = None
def getConnection():
    global connection
    if connection:
        return connection
    else:
        connection = sqlite3.connect(cacheFilename)
        return connection

def closeConnection():
    global connection
    if connection:
        connection.close()
        connection = None

#########################
### TABLE DEFINITIONS ###
#########################

schema = {
    'tables': [
        {
            'tableName': u'cacheItems',
            'fields': [
                { 'name': u'id', 'type': u'TEXT NOT NULL UNIQUE'},
                { 'name': u'name', 'type': u'TEXT'},
                { 'name': u'createdTime', 'type': u'TEXT'},
                { 'name': u'modifiedTime', 'type': u'TEXT'},
                { 'name': u'viewedByMeTime', 'type': u'TEXT'},
                { 'name': u'ownerEmail', 'type': u'TEXT'},
                { 'name': u'ownerName', 'type': u'TEXT'},
                { 'name': u'sharingUserEmail', 'type': u'TEXT'},
                { 'name': u'sharingUserName', 'type': u'TEXT'},
                { 'name': u'parentPath', 'type': u'TEXT'},
                { 'name': u'mimeType', 'type': u'TEXT'},
                { 'name': u'webViewLink', 'type': u'TEXT'},
                { 'name': u'iconPath', 'type': u'TEXT'},
                { 'name': u'iconLink', 'type': u'TEXT'},
            ],
            'primaryKey': u'id',
        },
    ]
}

def schemaIsAsExpected():
    '''Returns False if the DB isn't in a good state and we need to start over. This should happen very rarely.'''
    conn = getConnection()

    # Check whether it's got all the tables we expect
    expectedTables = [table['tableName'] for table in schema['tables']]
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    cur = conn.cursor()
    cur.execute(sql)
    actualTables = [item[0] for item in cur.fetchall()]
    actualTablesStr = str(sorted(actualTables))
    expectedTablesStr = str(sorted(expectedTables))
    if actualTablesStr != expectedTablesStr:
        #print("set of tables mismatch: '%s' vs '%s'" % (actualTablesStr, expectedTablesStr))
        return False

    # For each table, check that the columns match up
    for table in schema['tables']:
        tableName = table['tableName']
        tableInfo = conn.cursor().execute('PRAGMA table_info(%s);' % (tableName)).fetchall()

        # Create strings representing column names and types, and compare them
        expectedColumnsStr = '|'.join(['%s,%s' % (f['name'], f['type'].split(' ')[0]) for f in table['fields']])
        actualColumnStr = '|'.join(['%s,%s' % (col[1], col[2]) for col in tableInfo])

        if actualColumnStr != expectedColumnsStr:
            #print("Column mismatch for table '%s'.\nExpected '%s'\nActual   '%s'." % (tableName, expectedColumnsStr, actualColumnStr)) 
            return False

    return True

def wipeDatabase():
    closeConnection()
    open(cacheFilename, 'w').write('')

def initializeEmptyDatabase():
    try:
        conn = getConnection()

        # Create the tables!
        tables = schema['tables']

        for table in tables:
            sql = 'CREATE TABLE IF NOT EXISTS "{}" (\n{},\n  PRIMARY KEY("{}")\n);'.format(
                table['tableName'],
                ',\n'.join(['  "%s" %s' % (field['name'], field['type']) for field in table['fields']]),
                table['primaryKey'],
            )
            conn.cursor().execute(sql)
            conn.commit()
    except Error as e:
        print("Unhandled error: %s" % e)
        exit()

def prepareCacheDatabase():
    '''Gets the DB in a usable state with correct tables and schema.'''
    if not schemaIsAsExpected():
        wipeDatabase()
        initializeEmptyDatabase()

def updateCache(driveItems):
    '''Creates the cache and driveItems table if they don't exist, then updates the cache.
    driveItems is expected to be in the format returned from the Drive API'''

    conn = getConnection()

    sql = '''REPLACE INTO cacheItems(id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,parentPath,mimeType,webViewLink,iconPath,iconLink)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''

    for driveItem in driveItems:
        #id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,parentPath,mimeType,webViewLink,iconPath,iconLink
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
        values.append(driveItem.get('parentPath', None))
        values.append(driveItem.get('mimeType', None))
        values.append(driveItem.get('webViewLink', None))
        values.append(driveItem.get('iconPath', None))
        values.append(driveItem.get('iconLink', None))

        conn.cursor().execute(sql, tuple(values))
    
    conn.commit()

def getCacheItemsMatchingTokens(tokens):
    # Identify the table definition for the cache table - this should always happen
    tableSpec = None
    for table in schema['tables']:
        if table['tableName'] == 'cacheItems':
            tableSpec = table
            break

    columnsToMatchOn = ['name', 'ownerEmail', 'ownerName', 'sharingUserEmail', 'sharingUserName']
    allColumnNames = [field['name'] for field in tableSpec['fields']]
    clauses = ["  {} like '%' || ? || '%'".format(col) for col in columnsToMatchOn]

    sql = 'SELECT {} FROM cacheItems WHERE\n{}\n;'.format(
        ','.join(allColumnNames),
        ' OR\n'.join(clauses*len(tokens)),
    )

    # print("###### SQL ######")
    # print(sql)
    # print("#################")

    conn = getConnection()
    cur = conn.cursor()
    values = tuple(sorted(tokens*len(columnsToMatchOn))) # We don't care about order, but sorting will put them so all 5 copies of each token are adjacent.
    cur.execute(sql, values)
    rows = cur.fetchall()
    conn.close()

    # Return a list of cache items by using the column names as dict labels
    cacheItems = [dict(zip(allColumnNames, row)) for row in rows]
    return cacheItems

# Yes, we really do want to run this every time. This will make it so we always start with a database that has a known schema
prepareCacheDatabase()

if __name__ == '__main__':
    print(json.dumps(getCacheItemsMatchingTokens(['Alexis']), indent=2))
