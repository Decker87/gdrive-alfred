import sqlite3
from itertools import product

tokens = ['Adam', 'Brandon']

sqlPerToken = '''    (name like '%' || ? || '%' OR
    ownerEmail like '%' || ? || '%' OR
    ownerName like '%' || ? || '%' OR
    sharingUserEmail like '%' || ? || '%' OR
    sharingUserName like '%' || ? || '%')'''

columnsToMatchOn = ['name', 'ownerEmail', 'ownerName', 'sharingUserEmail', 'sharingUserName']
clauses = ["  {} like '%' || ? || '%'".format(col) for col in columnsToMatchOn]

sql = '''SELECT * FROM driveItems WHERE\n%s\n;''' % (' OR\n'.join(clauses*len(tokens)))


print("FINAL SQL ############################")
print(sql)
print("#########################")

conn = sqlite3.connect('testdb.db')
cur = conn.cursor()
cur.execute(sql, tuple(sorted(tokens*len(columnsToMatchOn)))) # We don't actually care about the order, but sorting will put them so all 5 copies of each token are adjacent.
rows = cur.fetchall()

print(len(rows))
