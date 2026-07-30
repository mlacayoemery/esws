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
         2 "Install geo stack (conda-forge GDAL 3.10)"
         3 "PROJ.4 (now part of option 2)"
         4 "Install Python requirements"
         5 "Setup OneTjs"
         6 "Setup WPS client"
         7 "Install GeoServer"
         8 "Install systemd services"
         9 "Configure firewall"
         10 "Install InVEST sample data"
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
# Install the geo stack from conda-forge, mirroring docker/Dockerfile.invest.
# natcap.invest pins gdal==3.10.*, and pip cannot satisfy that on its own --
# building GDAL's Python bindings needs a matching libgdal. conda-forge ships
# libgdal, PROJ and GEOS together, which is why building GDAL and PROJ from
# source (what this option used to do, at 2.4.4 and 7.0.0) is no longer needed.
ESWS_ENV="${ESWS_ENV:-$HOME/esws-invest}"
if [ ! -x "$HOME/.local/bin/micromamba" ]; then
    mkdir -p "$HOME/.local/bin"
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
        | tar -xj -C "$HOME/.local" bin/micromamba
fi
"$HOME/.local/bin/micromamba" create -y -p "$ESWS_ENV" -c conda-forge \
    python=3.11 \
    "gdal=3.10.*" \
    "pygeoprocessing>=2.4.10" \
    c-compiler cxx-compiler cython numpy \
    setuptools setuptools_scm wheel pip babel
echo "Geo stack installed in $ESWS_ENV"
read -p "Press [Enter] key to continue..."
;;

3)
# PROJ.4 used to be built from source here for Shapely. conda-forge ships it
# with the geo stack, so there is nothing left to do.
echo "PROJ is provided by the conda-forge geo stack -- use option 2 instead."
read -p "Press [Enter] key to continue..."
;;

4)
# Install the Python stack into the environment from option 2.
#
# --no-build-isolation is required: natcap.invest publishes no Linux wheels, so
# it builds from sdist, and in an isolated build environment its pygeoprocessing
# build requirement pulls the newest GDAL bindings off PyPI -- which then refuse
# to build against the conda libgdal ("Python bindings of GDAL 3.13.2 require at
# least libgdal 3.13.2, but 3.10.3 was found").
ESWS_ENV="${ESWS_ENV:-$HOME/esws-invest}"
"$HOME/.local/bin/micromamba" run -p "$ESWS_ENV" \
    pip install --no-build-isolation -r requirements_py3.txt

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
# Install GeoServer, version-matched to the container stack (3.0.0).
# Uses the platform-independent binary (Jetty bundled), so there is no Tomcat
# to install -- see scripts/install-geoserver.sh. GeoServer 3.0 needs Java 17.
sudo apt-get install -y openjdk-17-jre-headless unzip curl
sh scripts/install-geoserver.sh
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

sudo systemctl stop esws-geoserver
sudo systemctl disable esws-geoserver
sudo cp esws-geoserver.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/esws-geoserver.service
sudo systemctl reload esws-geoserver
sudo systemctl start esws-geoserver
sudo systemctl enable esws-geoserver
alias geoserver="sudo systemctl status esws-geoserver"

sudo systemctl stop esws-tjs
sudo systemctl disable esws-tjs
sudo cp esws-tjs.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/esws-tjs.service
sudo systemctl reload esws-tjs
sudo systemctl start esws-tjs
sudo systemctl enable esws-tjs
alias tjs="sudo systemctl status esws-tjs"


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
# Fetch the InVEST sample datasets and publish them: rasters and vectors to
# GeoServer, tables over HTTP, everything registered in the dashboard. The same
# loader `make demo` runs, pointed at a local install rather than at the compose
# network -- it takes every endpoint from the environment.
#
# It replaces tools/invest/import_sample_data_wy.py, which this option used to
# run. That script is Python 2 and has been unable to even parse for as long as
# this installer has targeted Python 3, so the option could only ever fail.
ESWS_ENV="${ESWS_ENV:-$HOME/esws-invest}"
./scripts/fetch_invest_samples.sh
# The loader's endpoints default to the compose service names; on a local
# install everything is on this host.
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:8000}" \
FILESERVER_URL="${FILESERVER_URL:-http://localhost:8001}" \
WPS_URL="${WPS_URL:-http://localhost:5000/wps}" \
GEOSERVER_BASE_URL="${GEOSERVER_BASE_URL:-http://localhost:8080/geoserver}" \
INVEST_SAMPLES_DIR="${INVEST_SAMPLES_DIR:-${INVEST_DATA_ROOT:-/store/invest}/samples}" \
    "$HOME/.local/bin/micromamba" run -p "$ESWS_ENV" python scripts/load_demo.py
;;

Q)
#quit installer
git pull
break
;;
esac

done

