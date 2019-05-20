#ESWS VM
##1
wget "http://127.0.0.1:8000/server/CSV/register/ESWS HTTP/url/http://192.168.122.22:8001" -O /dev/null

#Data VM
##2
wget "http://127.0.0.1:8000/server/WCS/register/KVM WCS/url/http://192.168.122.21:8080/gs215/ows" -O /dev/null
##3
wget "http://127.0.0.1:8000/server/WFS/register/KVM WFS/url/http://192.168.122.21:8080/gs215/ows" -O /dev/null

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


wget "http://127.0.0.1:8000/server/4/job/natcap.invest.hydropower.hydropower_water_yield/new/%7B%22pawc_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWCS%26version%3D2.0.0%26request%3DGetCoverage%26coverageId%3Dinvest%3Afreshwater_pawc%26format%3Dimage%252Fgeotiff%22%2C%20%22biophysical_table_uri%22%3A%20%22http%3A//192.168.122.22%3A8001/wy.csv%22%2C%20%22watersheds_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWFS%26version%3D1.0.0%26request%3DGetFeature%26typeName%3Dinvest%3Afresh_ws%26outputFormat%3DSHAPE-ZIP%22%2C%20%22lulc_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWCS%26version%3D2.0.0%26request%3DGetCoverage%26coverageId%3Dinvest%3Alanduse_90%26format%3Dimage%252Fgeotiff%22%2C%20%22seasonality_constant%22%3A%20%225%22%2C%20%22depth_to_root_rest_layer_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWCS%26version%3D2.0.0%26request%3DGetCoverage%26coverageId%3Dinvest%3Adepth_to_root_rest_layer%26format%3Dimage%252Fgeotiff%22%2C%20%22eto_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWCS%26version%3D2.0.0%26request%3DGetCoverage%26coverageId%3Dinvest%3Aeto%26format%3Dimage%252Fgeotiff%22%2C%20%22precipitation_uri%22%3A%20%22http%3A//192.168.122.21%3A8080/gs215/ows/ows%3Fservice%3DWCS%26version%3D2.0.0%26request%3DGetCoverage%26coverageId%3Dinvest%3Aprecip%26format%3Dimage%252Fgeotiff%22%2C%20%22workspace_dir%22%3A%20%221f508d1c-7af9-11e9-bb47-52540097c7aa%22%7D" -O /dev/null
