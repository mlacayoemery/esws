#Data server registrations
##1
wget "http://127.0.0.1:8000/server/CSV/register/Local HTTP/url/http://127.0.0.1:8001" -O /dev/null

##2
wget "http://127.0.0.1:8000/server/WCS/register/Local WCS/url/http://127.0.0.1:8080/gs215/ows" -O /dev/null
##3
wget "http://127.0.0.1:8000/server/WFS/register/Local WFS/url/http://127.0.0.1:8080/gs215/ows" -O /dev/null

##4
wget "http://127.0.0.1:8000/server/WPS/register/InVEST WPS/url/http://127.0.0.1:5000/wps" -O /dev/null

#InVEST WY registrations
wget "http://127.0.0.1:8000/server/CSV/1/register/wy.csv" -O /dev/null

wget "http://127.0.0.1:8000/server/WCS/2/register/invest:depth_to_root_rest_layer" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:eto" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:freshwater_pawc" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:freshwater_landuse_90" -O /dev/null
wget "http://127.0.0.1:8000/server/WCS/2/register/invest:precip" -O /dev/null

wget "http://127.0.0.1:8000/server/WFS/3/register/invest:fresh_ws" -O /dev/null

wget "http://127.0.0.1:8000/server/WPS/4/register/natcap.invest.hydropower.hydropower_water_yield"  -O /dev/null

wget "http://127.0.0.1:8000/server/4/job/natcap.invest.hydropower.hydropower_water_yield/new/%257B%2522pawc_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Afreshwater_pawc%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522biophysical_table_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8001/wy.csv%2522%252C%2520%2522watersheds_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWFS%2526version%253D1.0.0%2526request%253DGetFeature%2526typeName%253Dinvest%253Afresh_ws%2526outputFormat%253DSHAPE-ZIP%2522%252C%2520%2522lulc_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Afreshwater_landuse_90%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522seasonality_constant%2522%253A%2520%25225%2522%252C%2520%2522depth_to_root_rest_layer_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Adepth_to_root_rest_layer%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522eto_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Aeto%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522precipitation_path%2522%253A%2520%2522http%253A//127.0.0.1%253A8080/gs215/ows/ows%253Fservice%253DWCS%2526version%253D2.0.0%2526request%253DGetCoverage%2526coverageId%253Dinvest%253Aprecip%2526format%253Dimage%25252Fgeotiff%2522%252C%2520%2522workspace_dir%2522%253A%2520%25221f508d1c-7af9-11e9-bb47-52540097c7aa%2522%257D" -O /dev/null
