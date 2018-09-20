import os

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import easyows
import shp_join_sub

model_path = "c:\\swat_sample\\model"
swat_exe = "swat.exe"

cmd = os.path.join(model_path, swat_exe)

print "Runnng %s" % cmd
os.chdir(model_path)
os.system(cmd)

sub_path = os.path.join(model_path,
                        "output.sub")
shp_path = "c:\\swat_sample\\subs1.shp"

shp_join_sub.join(shp_path, sub_path)
easyows.publish_shp(shp_path)
