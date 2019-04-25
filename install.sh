#install system requirements
xargs apt-get install -y < requirements.system

#install GDAL with Python 2 and 3 bindings
cd ..
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ldconfig
wget http://download.osgeo.org/gdal/2.3.1/gdal-2.3.1.tar.gz
tar -xvf gdal-2.3.1.tar.gz
cd gdal-2.3.1
./configure --with-python
make
make install
pip2 install /data/share/gdal-2.3.1/swig/python
pip3 install /data/share/gdal-2.3.1/swig/python
cd ../esws

#install Python requirements
pip2 install -r requirements.txt

