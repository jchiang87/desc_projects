import csv
import pandas as pd

md_file = 'run1_352_metadata_v1.csv'

class CsvProcessor(object):
    def __init__(self):
        self.data = []
    def process_row(self, data):
        filters = 'ugrizy'
        row = [int(data[0]), float(data[1]), filters[int(data[2])],
               float(data[-4]), float(data[-6])]
        self.data.append(row)
    def make_dataframe(self):
        columns = 'visit mjd filter cputime_fell cputime'.split()
        return pd.DataFrame(data=self.data, columns=columns)

with open(md_file, 'rb') as csvfile:
    data = [row for row in csv.reader(csvfile, delimiter=',')][1:]

processor = CsvProcessor()

for row in data:
    processor.process_row(row)

df = processor.make_dataframe()

df_sort = df.sort(['cputime_fell'])

print df_sort[df_sort['filter'] == 'r'][:10]



