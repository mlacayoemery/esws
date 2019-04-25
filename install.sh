#!/bin/bash
apt-get install -y dialog

HEIGHT=15
WIDTH=40
CHOICE_HEIGHT=4
BACKTITLE="Ecosystem Service Web Services (ESWS)"
TITLE="InVEST WY Demo"
MENU="Choose one of the following options:"

OPTIONS=(1 "Install system requirements"
         2 "Install GDAL from source with Python 2 and 3 bindings"
         3 "Install PROJ.4 from source for Shapely Python library"
         4 "Install Python requirements"
         5 "Install GeoServer")

CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
case $CHOICE in
1)
#install system requirements
xargs apt-get install -y < requirements.system
;;

2)
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
;;

3)
#install PROJ.4 for shapely
cd ..
wget http://download.osgeo.org/proj/proj-5.2.0.tar.gz
tar -xvf proj-5.2.0.tar.gz
wget http://download.osgeo.org/proj/proj-datumgrid-1.8.zip
unzip proj-datumgrid-1.8.zip -d proj-5.2.0/nad
cd proj-5.2.0
./configure
make
make install
cd ../esws
;;

4)
#install Python requirements
pip2 install -r requirements.txt
;;

5)
#install GeoServer
cd ..
wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.13.3/geoserver-2.13.3-war.zip
wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.13.3/extensions/geoserver-2.13.3-wps-plugin.zip
unzip -p geoserver-2.13.3-war.zip geoserver.war > gs213.war
service tomcat8 stop
mv gs213.war /var/lib/tomcat8/webapps
su tomcat8
unzip geoserver-2.13.3-wps-plugin.zip -d /var/lib/tomcat8/webapps/geoserver/WEB-INF/lib
exit
service tomcat8 start
cd ../esws
;;
esac

