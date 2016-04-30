import desc.pserv

sql = """create table if not exists
         ObjectNumChildren (
         objectId BIGINT,
         numChildren INT,
         primary key (objectId))"""

connection = desc.pserv.DbConnection(db='jc_fermi',
                                     read_default_file='~/.my.cnf')
connection.apply(sql)

query = 'select objectId, parentObjectId from Object'

def count_children(curs):
    results = dict()
    for entry in curs:
        objectId, parent = tuple(entry)
        if not results.has_key(objectId):
            results[objectId] = 0
        if parent != 0:
            results[parent] += 1
    return results

results = connection.apply(query, cursorFunc=count_children)
print len(results)

for parentId, numChildren in results.items():
    connection.apply('insert into ObjectNumChildren values (%i, %i)'
                     % (parentId, numChildren))
