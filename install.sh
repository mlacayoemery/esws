#!/bin/bash
sudo apt-get install -y dialog

HEIGHT=15
WIDTH=40
CHOICE_HEIGHT=6
BACKTITLE="Ecosystem Service Web Services (ESWS)"
TITLE="ESWS"
MENU="Choose one of the following options:"

OPTIONS=(1 "Install system requirements"
         2 "Install GDAL from source with Python 2 and 3 bindings"
         3 "Install PROJ.4 from source for Shapely Python library"
         4 "Install Python requirements"
         5 "Install GeoServer"
         6 "Quit setup")

while true; do 
CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
git pull
case $CHOICE in
1)
#install system requirements
sudo xargs apt-get install -y < requirements.system
read -p "Press [Enter] key to continue..."
;;

2)
#install GDAL with Python 2 and 3 bindings
cd ..
if [[ $LD_LIBRARY_PATH == *"/usr/local/lib"* ]]; then
    echo "LD_LIBRARY_PATH already set"
else
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
    sudo ldconfig
fi
if [ -f "gdal-2.3.1.tar.gz" ]; then
    echo "GDAL already downloaded"
else
    wget http://download.osgeo.org/gdal/2.3.1/gdal-2.3.1.tar.gz
fi
tar -xvf gdal-2.3.1.tar.gz
cd gdal-2.3.1
./configure --with-python
make
sudo make install
sudo pip2 install swig/python
sudo pip3 install swig/python
cd ../esws
read -p "Press [Enter] key to continue..."
;;

3)
#install PROJ.4 for shapely
cd ..
if [ -f "proj-5.2.0.tar.gz" ]; then
    echo "PROJ.4 already downloaded"
else
    wget http://download.osgeo.org/proj/proj-5.2.0.tar.gz
fi
tar -xvf proj-5.2.0.tar.gz
if [ -f "proj-datumgrid-1.8.zip" ]; then
    echo "PROJ.4 datum grid already downloaded"
else
    wget http://download.osgeo.org/proj/proj-datumgrid-1.8.zip
fi
unzip proj-datumgrid-1.8.zip -d proj-5.2.0/nad
cd proj-5.2.0
./configure
make
sudo make install
cd ../esws
read -p "Press [Enter] key to continue..."
;;

4)
#install Python requirements
sudo pip2 install --upgrade Cython
sudo pip2 install --upgrade numpy>=1.11.0
sudo pip2 install --upgrade -r requirements_py2.txt
sudo pip3 install --upgrade -r requirements_py3.txt
read -p "Press [Enter] key to continue..."
;;

5)
#install GeoServer
cd ..
if [ -f "geoserver-2.13.3-war.zip" ]; then
    echo "GeoServer already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.13.3/geoserver-2.13.3-war.zip
fi
if [ -f "geoserver-2.13.3-wps-plugin.zip" ]; then
    echo "GeoServer WPS plugin already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.13.3/extensions/geoserver-2.13.3-wps-plugin.zip
fi
unzip -p geoserver-2.13.3-war.zip geoserver.war > gs213.war
sudo service tomcat8 stop
sudo mv gs213.war /var/lib/tomcat8/webapps
sudo service tomcat8 start
sleep 10
sudo service tomcat8 stop
sudo -u tomcat8 unzip geoserver-2.13.3-wps-plugin.zip -d /var/lib/tomcat8/webapps/gs213/WEB-INF/lib
sudo service tomcat8 start
cd ../esws
read -p "Press [Enter] key to continue..."
;;

6)
#quit installer
break
;;
esac

done

