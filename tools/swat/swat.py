import os

model_path = "c:\\swat_sample\\model"
swat_exe = "swat.exe"

cmd = os.path.join(model_path, swat_exe)

print "Runnng %s" % cmd
os.chdir(model_path)
os.system(cmd)
