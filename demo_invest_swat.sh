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


wget "http://127.0.0.1:8000/server/4/job/natcap.invest.hydropower.hydropower_water_yield/new/%257B%2522pawc_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Afreshwater_pawc%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522biophysical_table_uri%2522%253A%2520%2522http%253A//192.168.122.22%253A8001/wy.csv%2522%252C%2520%2522watersheds_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWFS%2526version%253D1.0.0%2526request%253DGetFeature%2526typeName%253Dinvest%253Afresh_ws%2526outputFormat%253DSHAPE-ZIP%2522%252C%2520%2522lulc_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Alanduse_90%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522seasonality_constant%2522%253A%2520%25225%2522%252C%2520%2522depth_to_root_rest_layer_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Adepth_to_root_rest_layer%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522eto_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Aeto%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522precipitation_uri%2522%253A%2520%2522http%253A//192.168.122.21%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Aprecip%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522workspace_dir%2522%253A%2520%25221f508d1c-7af9-11e9-bb47-52540097c7aa%2522%257D" -O /dev/null

wget "http://127.0.0.1:8000/server/6/job/swat/new/%257B%2522model%2522%253A%2520%2522http%253A//127.0.0.1%253A8000/esws_swat.zip%2522%257D" -O /dev/null
