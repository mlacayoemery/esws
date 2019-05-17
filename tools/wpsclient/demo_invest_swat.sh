#ESWS VM
##1
wget "http://127.0.0.1:8000/server/CSV/register/ESWS HTTP/url/http://192.168.122.22:8001" -O /dev/null

#Gala
##2
wget "http://127.0.0.1:8000/server/WCS/register/Gala WCS/url/http://127.0.0.1:8080/gs215/ows" -O /dev/null
##3
wget "http://127.0.0.1:8000/server/WFS/register/Gala WFS/url/http://127.0.0.1:8080/gs215/ows" -O /dev/null

#ESWS VM
##4
wget "http://127.0.0.1:8000/server/WPS/register/InVEST WPS/url/http://192.168.122.22:5000/wps" -O /dev/null

#WIN VM
##5
wget "http://127.0.0.1:8000/server/CSV/register/SWAT HTTP/url/http://192.168.122.23:8001" -O /dev/null
##6
wget "http://127.0.0.1:8000/server/WPS/register/SWAT WPS/url/http://192.168.122.23:5000/wps" -O /dev/null

#InVEST WY registrations
wget "http://127.0.0.1:8000/server/CSV/1/register/wy.csv" -O /dev/null

wget "http://127.0.0.1:8000/server/WCS/2/register/invest:depth_to_root_rest_layer" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:eto" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:freshwater_pawc" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:landuse_90" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:precip" -O /dev/null

wget "http://127.0.0.1:8000/server/WFS/3/register/invest:fresh_ws" -O /dev/null

wget "http://127.0.0.1:8000/server/WPS/4/register/natcap.invest.hydropower.hydropower_water_yield"  -O /dev/null

#SWAT registratons
wget "http://127.0.0.1:8000/server/CSV/5/register/esws_swat.zip" -O /dev/null
wget "http://127.0.0.1:8000/server/WPS/6/register/swat"  -O /dev/null
