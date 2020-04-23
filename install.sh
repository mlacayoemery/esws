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
         2 "Install GDAL from source with Python 2 and 3 bindings"
         3 "Install PROJ.4 from source for Shapely Python library"
         4 "Install Python requirements"
         5 "Setup OneTjs"
         6 "Setup WPS client"
         7 "Install GeoServer"
         8 "Install systemd services"
         9 "Configure firewall"
         10 "Install InVEST Data"
         Q "Quit setup")

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
sudo pip3 install numpy
sudo apt-get install sqlite3 libsqlite3-dev
#install GDAL with Python 3 bindings
cd ..
if [[ $LD_LIBRARY_PATH == *"/usr/local/lib"* ]]; then
    echo "LD_LIBRARY_PATH already set"
else
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
    sudo ldconfig
fi
if [ -f "gdal-2.4.4.tar.gz" ]; then
    echo "GDAL already downloaded"
else
    wget http://download.osgeo.org/gdal/2.4.4/gdal-2.4.4.tar.gz
fi
tar -xvf gdal-2.4.4.tar.gz
cd gdal-2.4.4
./configure --with-python --with-sqlite3
make
sudo make install
sudo pip3 install swig/python
cd ../esws
read -p "Press [Enter] key to continue..."
;;

3)
#install PROJ.4 for shapely
cd ..
if [ -f "proj-7.0.0.tar.gz" ]; then
    echo "PROJ.4 already downloaded"
else
    wget http://download.osgeo.org/proj/proj-7.0.0.tar.gz
fi
tar -xvf proj-7.0.0.tar.gz
if [ -f "proj-datumgrid-1.8.zip" ]; then
    echo "PROJ.4 datum grid already downloaded"
else
    wget http://download.osgeo.org/proj/proj-datumgrid-1.8.zip
fi
unzip proj-datumgrid-1.8.zip -d proj-7.0.0/nad
cd proj-7.0.0
./configure
make
sudo make install
cd ../esws
read -p "Press [Enter] key to continue..."
;;

4)
#install Python requirements
#sudo pip3 install --upgrade pip

#sudo pip3 install --upgrade Cython
#sudo pip3 install --upgrade numpy>=1.11.0
#sudo pip3 install --upgrade flask
#sudo pip3 install --upgrade pywps
#sudo pip3 install --upgrade -e git+https://github.com/boundlessgeo/gsconfig.git@d05a4dc152aa3fb97171f418d7dc09f5f45445a5#egg=gsconfig-py
#sudo pip3 install --upgrade -r requirements_py2.txt
#sudo pip3 install --upgrade -r requirements_py3.txt

sudo xargs pip3 install --upgrade < requirements_py3.txt

read -p "Press [Enter] key to continue..."
;;

5)
cd ..
git clone https://github.com/mlacayoemery/OneTjs.git
python3 -m venv tjs-venv
source tjs-venv/bin/activate
cd OneTjs
pip3 install -r requirements.txt
deactivate
cd ../esws
;;

6)
#setup wps client
sh tools/wpsclient/setup.sh
;;

7)
#install GeoServer
sudo apt-get install -y openjdk-11-jdk tomcat9 unzip
cd ..
if [ -f "geoserver-2.17.0-war.zip" ]; then
    echo "GeoServer already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.17.0/geoserver-2.17.0-war.zip
fi
if [ -f "geoserver-2.17.0-wps-plugin.zip" ]; then
    echo "GeoServer WPS plugin already downloaded"
else 
    wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.17.0/extensions/geoserver-2.17.0-wps-plugin.zip
fi
unzip -p geoserver-2.17.0-war.zip geoserver.war > gs217.war
sudo service tomcat9 stop
sudo mv gs217.war /var/lib/tomcat8/webapps
sudo service tomcat9 start
echo "Waiting 10 seconds for Tomcat setup"
sleep 10
sudo service tomcat9 stop
sudo -u tomcat8 unzip geoserver-2.17.0-wps-plugin.zip -d /var/lib/tomcat8/webapps/gs217/WEB-INF/lib
sudo service tomcat9 start
cd esws
read -p "Press [Enter] key to continue..."
;;

8)
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

9)
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

read -p "Press [Enter] key to continue..."
;;

10)
python tools/invest/import_sample_data_wy.py 
;;

Q)
#quit installer
git pull
break
;;
esac

done

