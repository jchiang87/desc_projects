import sys
from desc.twinkles.db_table_access import LsstDatabaseTable

class NumChildren(dict):
    def __init__(self):
        super(NumChildren, self).__init__()
    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = 0
        return dict.__getitem__(self, key)

def count_children(curs):
    results = NumChildren()
    for entry in curs:
        objectId, parent = tuple(entry)
        if parent != 0:
            results[parent] += 1
    return results

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = LsstDatabaseTable(**db_info)

query = '''create table NewObject (objectId BIGINT,
        parentObjectId BIGINT,
        numChildren INT,
        psRa DOUBLE,
        psDecl DOUBLE,
        primary key (objectId))'''
print query
jc_desc.apply(query)

query = '''insert into NewObject select
        objectId, parentObjectId, 0, psRa, psDecl from Object'''
print query
jc_desc.apply(query)

query = 'select objectId, parentObjectId from Object where parentObjectId != 0'
print query
results = jc_desc.apply(query, count_children)
nobjs = len(results)
print "number of blended objects", nobjs

nrow = 1
for parentId, numChildren in results.items():
    if nrow % (nobjs/20) == 0:
        sys.stdout.write('.')
    query = '''update NewObject set numChildren=%(numChildren)i
             where objectId=%(parentId)i''' % locals()
    jc_desc.apply(query)
    nrow += 1
