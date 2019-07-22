#!/bin/bash
sudo apt-get install -y dialog

HEIGHT=20
WIDTH=40
CHOICE_HEIGHT=9
BACKTITLE="Ecosystem Service Web Services (ESWS)"
TITLE="ESWS"
MENU="Choose one of the following options:"

OPTIONS=(0 "Clone ESWS repository"
         1 "Install system requirements"
#         2 "Install GDAL from source with Python 2 and 3 bindings"
#         3 "Install PROJ.4 from source for Shapely Python library"
         4 "Install Python requirements"
         5 "Setup WPS client"
         6 "Install GeoServer"
         7 "Install systemd services"
         8 "Configure firewall"
         9 "Quit setup")

while true; do 
CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
case $CHOICE in
0)
sudo apt-get install -y git

if [ -f "/home/esws/esws/requirements.system" ]; then
    echo "ESWS already downloaded"
else 
    git clone https://github.com/mlacayoemery/esws.git /home/esws/esws
fi

read -p "Press [Enter] key to continue..."
;;

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
sudo pip2 install --upgrade pip
sudo pip3 install --upgrade pip

sudo pip2 install --upgrade Cython
sudo pip2 install --upgrade numpy>=1.11.0
sudo pip2 install --upgrade flask
sudo pip2 install --upgrade pywps
sudo pip2 install --upgrade -e git+https://github.com/boundlessgeo/gsconfig.git@d05a4dc152aa3fb97171f418d7dc09f5f45445a5#egg=gsconfig-py
sudo pip2 install --upgrade -r requirements_py2.txt
sudo pip3 install --upgrade -r requirements_py3.txt
read -p "Press [Enter] key to continue..."
;;

5)
#setup wps client
sh tools/wpsclient/setup.sh
;;

6)
#install GeoServer
sudo apt-get install -y openjdk-8-jdk tomcat8 unzip
cd ..
if [ -f "geoserver-2.15.1-war.zip" ]; then
    echo "GeoServer already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.15.1/geoserver-2.15.1-war.zip
fi
if [ -f "geoserver-2.15.1-wps-plugin.zip" ]; then
    echo "GeoServer WPS plugin already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.15.1/extensions/geoserver-2.15.1-wps-plugin.zip
fi
unzip -p geoserver-2.15.1-war.zip geoserver.war > gs215.war
sudo service tomcat8 stop
sudo mv gs215.war /var/lib/tomcat8/webapps
sudo service tomcat8 start
echo "Waiting 10 seconds for Tomcat setup"
sleep 10
sudo service tomcat8 stop
sudo -u tomcat8 unzip geoserver-2.15.1-wps-plugin.zip -d /var/lib/tomcat8/webapps/gs215/WEB-INF/lib
sudo service tomcat8 start
cd esws
read -p "Press [Enter] key to continue..."
;;

7)
sudo systemctl stop esws-dashboard
sudo systemctl disable esws-dashboard
sudo cp esws-dashboard.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/esws-dashboard.service
sudo systemctl reload esws-dashboard
sudo systemctl start esws-dashboard
sudo systemctl enable esws-dashboard
alias dashboard="sudo systemctl status esws-dashboard"

sudo systemctl stop esws-wps-invest
sudo systemctl disable esws-wps-invest
sudo cp esws-wps-invest.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/esws-wps-invest.service
sudo systemctl reload esws-wps-invest
sudo systemctl start esws-wps-invest
sudo systemctl enable esws-wps-invest
alias invest="sudo systemctl status esws-wps-invest"

sudo systemctl stop esws-file-server
sudo systemctl disable esws-file-server
sudo cp esws-file-server.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/esws-file-server.service
sudo systemctl reload esws-file-server
sudo systemctl start esws-file-server
sudo systemctl enable esws-file-server
alias http="sudo systemctl status esws-file-server"

#sudo systemctl stop esws-data-gala
#sudo systemctl disable esws-data-gala
#sudo cp esws-data-gala.service /etc/systemd/system
#sudo chmod 644 /etc/systemd/system/esws-data-gala.service
#sudo systemctl reload esws-data-gala
#sudo systemctl start esws-data-gala
#sudo systemctl enable esws-data-gala

read -p "Press [Enter] key to continue..."
;;

8)
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

read -p "Press [Enter] key to continue..."
;;

9)
#quit installer
git pull
break
;;
esac

done

