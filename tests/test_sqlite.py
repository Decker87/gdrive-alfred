import sqlite3, json
from sqlite3 import Error

creationSql = '''CREATE TABLE "driveItems" (
	"id"	TEXT NOT NULL UNIQUE,
	"name"	TEXT,
	"createdTime"	TEXT,
	"modifiedTime"	TEXT,
	"viewedByMeTime"	TEXT,
	"ownerEmail"	TEXT,
	"ownerName"	TEXT,
	"sharingUserEmail"	TEXT,
	"sharingUserName"	TEXT,
	"mimeType"	TEXT,
	"webViewLink"	TEXT,
	"iconPath"	TEXT,
	"iconLink"	TEXT,
	PRIMARY KEY("id")
);'''

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def insert_cache(conn):
    sql = '''REPLACE INTO driveItems(id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,mimeType,webViewLink,iconPath,iconLink)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?);'''

    cache = json.load(open('cache.json')) 

    for item in cache:
        print("WORKING ON ###################")
        print(json.dumps(item, indent=2))
        print("###############")

        #id,name,createdTime,modifiedTime,viewedByMeTime,ownerEmail,ownerName,sharingUserEmail,sharingUserName,mimeType,webViewLink,iconPath,iconLink
        values = []
        values.append(item['id'])
        values.append(item.get('name', None))
        values.append(item.get('createdTime', None))
        values.append(item.get('modifiedTime', None))
        values.append(item.get('viewedByMeTime', None))
        if 'owners' in item:
            if 'emailAddress' in item['owners'][0] and item['owners'][0]['emailAddress'] != "":
                values.append(item['owners'][0]['emailAddress'])
            else:
                values.append(None)
            if 'displayName' in item['owners'][0] and item['owners'][0]['displayName'] != "":
                values.append(item['owners'][0]['displayName'])
            else:
                values.append(None)
        else:
            values.append(None)
            values.append(None)
        if 'sharingUser' in item:
            if 'emailAddress' in item['sharingUser'] and item['sharingUser']['emailAddress'] != "":
                values.append(item['sharingUser']['emailAddress'])
            else:
                values.append(None)
            if 'displayName' in item['sharingUser'] and item['sharingUser']['displayName'] != "":
                values.append(item['sharingUser']['displayName'])
            else:
                values.append(None)
        else:
            values.append(None)
            values.append(None)
        values.append(item.get('mimeType', None))
        values.append(item.get('webViewLink', None))
        values.append(item.get('iconPath', None))
        values.append(item.get('iconLink', None))

        conn.cursor().execute(sql, tuple(values))

    conn.commit()

def main():
    database = r"testdb.db"

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create the main table
        #create_table(conn, creationSql)
        insert_cache(conn)
    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    main()