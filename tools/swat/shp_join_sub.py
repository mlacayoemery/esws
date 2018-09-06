import struct
import csv
import os

def f(widths):
    return ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's')
                    for fw in fieldwidths)

def p(pattern):
    return struct.Struct(fmtstring).unpack_from

esws_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-3])

in_path = os.path.join(esws_path, "data/sample.sub")
out_path = os.path.join(esws_path, "data/sample.csv")

sub = open(in_path, 'r')

skip_lines = 8
for i in range(skip_lines):
    next(sub)

line = next(sub).rstrip()
cols = (len(line) - 24) / 10

fieldwidths = [6, -1, 3, -6, 3, -2, 3, 10] + [-1, 9] * (cols - 1)

fmtstring = f(fieldwidths)
parse = p(fmtstring)

header = parse(line)

with open(out_path, 'wb') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)

    for line in sub:
        row = list(parse(line))
        row[1] = row[1].lstrip()
        row[2] = row[2].lstrip()
        row[3] = row[3].lstrip()

        writer.writerow(row)


ogr2ogr = """ogr2ogr -sql "select %s.*, %s.* from %s left join '%s'.%s on %s.%s = %s.%s" %s %s"""

shp_root = "sub"
shp_id = "SUBBASIN"
shp_path = os.path.join(esws_path, "data/sub.shp")

csv_root = "sample"
csv_id = "SUB"
csv_path = os.path.join(esws_path, "data/sample.csv")

shp_join_path = os.path.join(esws_path, "data/shape_join.shp")

cmd = ogr2ogr % (shp_root, csv_root, shp_root, csv_path, csv_root, shp_root, shp_id, csv_root, csv_id, shp_join_path, shp_path)

os.system(cmd)
