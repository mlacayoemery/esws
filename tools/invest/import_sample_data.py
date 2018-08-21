import geoserver.catalog
import os.path

rest_url = "http://localhost:8080/geoserver/rest"
username = "admin"
password = "geoserver"

data_path = "/home/mlacayo/workspace/data"
data_stores = [("scenario_override", os.path.join(data_path, "ScenarioGenerator/input/override")),
               ("scenario_elevation", os.path.join(data_path, "ScenarioGenerator/input/elevation")),
               ("scenario_roads", os.path.join(data_path, "ScenarioGenerator/input/roads")),
               ("scenario_majorroads", os.path.join(data_path, "ScenarioGenerator/input/majorroads")),
               ("scenario_constraints", os.path.join(data_path, "ScenarioGenerator/input/constraints")),
               ("scenario_proximity", os.path.join(data_path, "scenario_proximity/scenario_proximity_aoi")),
               ("wave_nawc", os.path.join(data_path, "WaveEnergy/input/WaveData/NAmerica_WestCoast_4m")),
               ("wave_global", os.path.join(data_path, "WaveEnergy/input/WaveData/Global")),
               ("wave_ns_4m_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/North_Sea_4m_Extract")),
               ("wave_naec_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/ECNA_extract")),
               ("wave_aus", os.path.join(data_path, "WaveEnergy/input/WaveData/Australia_4m")),
               ("wave_ns_10m_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/North_Sea_10m_Extract")),
               ("wave_aus_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/Australia_Extract")),
               ("wave_global_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/Global_extract")),
               ("wave_ns_4m", os.path.join(data_path, "WaveEnergy/input/WaveData/North_Sea_4m")),
               ("wave_nawc_extract", os.path.join(data_path, "WaveEnergy/input/WaveData/WCNA_extract")),
               ("wave_naec", os.path.join(data_path, "WaveEnergy/input/WaveData/NAmerica_EastCoast_4m")),
               ("wave_ns_10m", os.path.join(data_path, "WaveEnergy/input/WaveData/North_Sea_10m")),
               ("wave_resolution", os.path.join(data_path, "WaveEnergy/input/WaveData_Resolution")),
               ("wave_aoi", os.path.join(data_path, "WaveEnergy/input/AOI_WCVI")),
               ("habitat_access", os.path.join(data_path, "HabitatQuality/access_samp")),
               ("overlap_wildlife", os.path.join(data_path, "OverlapAnalysis/Input/RecreationLayers_RIS/WildlifeSightsRec")),
               ("overlap_scuba", os.path.join(data_path, "OverlapAnalysis/Input/RecreationLayers_RIS/ScubaRec")),
               ("overlap_fish", os.path.join(data_path, "OverlapAnalysis/Input/RecreationLayers_RIS/FishingRec")),
               ("overlap_surf", os.path.join(data_path, "OverlapAnalysis/Input/RecreationLayers_RIS/SurfspotRec")),
               ("overlap_beach", os.path.join(data_path, "OverlapAnalysis/Input/RecreationLayers_RIS/BeachesRec")),
               ("overlap_people", os.path.join(data_path, "OverlapAnalysis/Input/PopulatedPlaces_WCVI")),
               ("overlap_comm_fish", os.path.join(data_path, "OverlapAnalysis/Input/FisheriesLayers_RI/CommShrimp_Fish")),
               ("overlap_comm_gf", os.path.join(data_path, "OverlapAnalysis/Input/FisheriesLayers_RI/CommGF_Fish")),
               ("overlap_comm_troll", os.path.join(data_path, "OverlapAnalysis/Input/FisheriesLayers_RI/CommSalmonTroll_Fish")),
               ("overlap_aoi", os.path.join(data_path, "OverlapAnalysis/Input/AOI_WCVI")),
               ("overlap_zones", os.path.join(data_path, "OverlapAnalysis/Input/ManagementZones_WCVI")),
               ("globio_aoi", os.path.join(data_path, "globio/sub_aoi")),
               ("aquaculture_netpens", os.path.join(data_path, "Aquaculture/Input/Finfish_Netpens")),
               ("seasonal_ws", os.path.join(data_path, "seasonal_water_yield/watershed")),
               ("carbon_aoi", os.path.join(data_path, "forest_carbon_edge_effect/forest_carbon_edge_demo_aoi")),
               ("carbon_reg", os.path.join(data_path, "forest_carbon_edge_effect/core_data/forest_carbon_edge_regression_model_parameters")),
               ("scenic_wem", os.path.join(data_path, "ScenicQuality/Input/AquaWEM_points")),
               ("scenic_pa", os.path.join(data_path, "ScenicQuality/Input/BC_protectedAreas")),
               ("scenic_aoi", os.path.join(data_path, "ScenicQuality/Input/AOI_WCVI")),
               ("scenic_parks", os.path.join(data_path, "ScenicQuality/Input/BC_parks")),
               ("rec_bonefish", os.path.join(data_path, "recreation/bonefish")),
               ("rec_aoi", os.path.join(data_path, "recreation/andros_aoi")),
               ("rec_seaports", os.path.join(data_path, "recreation/dredged_ports")),
               ("rec_airport", os.path.join(data_path, "recreation/airport")),
               ("rec_road_buf", os.path.join(data_path, "recreation/roads_simple_buf")),
               ("rec_beach", os.path.join(data_path, "recreation/beaches")),
               ("rec_road_dev", os.path.join(data_path, "recreation/scenario/roads_simple_dev")),
               ("rec_seaport_dev", os.path.join(data_path, "recreation/scenario/dredged_ports_dev")),
               ("rec_road_buf_dev", os.path.join(data_path, "recreation/scenario/roads_simple_buf_dev")),
               ("rec_bonefish_dev", os.path.join(data_path, "recreation/scenario/bonefish_dev")),
               ("rec_airport_Dev", os.path.join(data_path, "recreation/scenario/airport_dev")),
               ("rec_beach_dev", os.path.join(data_path, "recreation/scenario/beaches_dev")),
               ("rec_roads", os.path.join(data_path, "recreation/roads_simple")),
               ("wind_aoi", os.path.join(data_path, "WindEnergy/input/New_England_US_Aoi")),
               ("fish_tx", os.path.join(data_path, "Fisheries/input/shapefile_galveston/Galveston_Subregion")),
               ("fish_dc", os.path.join(data_path, "Fisheries/input/shapefile_hood_canal/DC_HoodCanal_Subregions")),
               ("fish_blz", os.path.join(data_path, "Fisheries/input/shapefile_belize/Lob_Belize_Subregions")),
               ("terre_roads", os.path.join(data_path, "Base_Data/Terrestrial/roads")),
               ("terre_cities", os.path.join(data_path, "Base_Data/Terrestrial/cities")),
               ("marine_vi_line", os.path.join(data_path, "Base_Data/Marine/Vancouver_Island/VI_landPolyline_UTM10N")),
               ("marine_vi_poi", os.path.join(data_path, "Base_Data/Marine/Vancouver_Island/VI_PointsofInterest")),
               ("marine_vi_poly", os.path.join(data_path, "Base_Data/Marine/Vancouver_Island/VI_landPolygon_UTM10N")),
               ("marine_land_line", os.path.join(data_path, "Base_Data/Marine/Land/global_polyline")),
               ("marine_land_poly", os.path.join(data_path, "Base_Data/Marine/Land/global_polygon")),
               ("marine_utm", os.path.join(data_path, "Base_Data/Marine/Grids/UTM_zones")),
               ("fresh_outlets", os.path.join(data_path, "Base_Data/Freshwater/outlets")),
               ("fresh_ws", os.path.join(data_path, "Base_Data/Freshwater/watersheds")),
               ("fresh_sws", os.path.join(data_path, "Base_Data/Freshwater/subwatersheds")),
               ("hra_docks", os.path.join(data_path, "HabitatRiskAssess/Input/StressorLayers/DocksWharvesMarinas")),
               ("hra_shellfish", os.path.join(data_path, "HabitatRiskAssess/Input/StressorLayers/ShellfishAquacultureComm")),
               ("hra_finfish", os.path.join(data_path, "HabitatRiskAssess/Input/StressorLayers/FinfishAquacultureComm")),
               ("hra_recfish", os.path.join(data_path, "HabitatRiskAssess/Input/StressorLayers/RecFishing")),
               ("hra_subregion", os.path.join(data_path, "HabitatRiskAssess/Input/subregions")),
               ("hra_softbottom_ir", os.path.join(data_path, "HabitatRiskAssess/Input/Spatially_Explicit_Criteria/Exposure/softbottom_DocksWharvesMarinas_intensity_rating")),
               ("hra_softbottom", os.path.join(data_path, "HabitatRiskAssess/Input/HabitatLayers/softbottom")),
               ("hra_hardbottom", os.path.join(data_path, "HabitatRiskAssess/Input/HabitatLayers/hardbottom")),
               ("hra_kelp", os.path.join(data_path, "HabitatRiskAssess/Input/HabitatLayers/kelp")),
               ("hra_eelgrass", os.path.join(data_path, "HabitatRiskAssess/Input/HabitatLayers/eelgrass")),
               ("coastal_cox", os.path.join(data_path, "CoastalProtection/Input/LandPoint_CoxBay")),
               ("coastal_blz", os.path.join(data_path, "CoastalProtection/Input/LandPoint_Belize_Sand")),
               ("coastal_slr", os.path.join(data_path, "CoastalProtection/Input/SeaLevRise_WCVI")),
               ("coastal_ww3", os.path.join(data_path, "CoastalProtection/Input/WaveWatchIII")),
               ("coastal_soil", os.path.join(data_path, "CoastalProtection/Input/soil_type_WCVI")),
               ("coastal_forcing", os.path.join(data_path, "CoastalProtection/Input/Climatic_forcing")),
               ("coastal_blz_poly", os.path.join(data_path, "CoastalProtection/Input/LandPolygon_Belize")),
               #dbf missing ("coastal_struct", os.path.join(data_path, "CoastalProtection/Input/Structures_BarkClay")),
               ("coastal_barclay_aoi", os.path.join(data_path, "CoastalProtection/Input/AOI_BarkClay")),
               ("coastal_wcvi_poly", os.path.join(data_path, "CoastalProtection/Input/LandPolygon_WCVI")),
               ("coastal_barclay_geo", os.path.join(data_path, "CoastalProtection/Input/Geomorphology_BarkClay")),
               ("coastal_barksound_pt", os.path.join(data_path, "CoastalProtection/Input/LandPoint_BarkSound")),
               ("coastal_blz_mud_pt", os.path.join(data_path, "CoastalProtection/Input/LandPoint_Belize_Mud")),
               ("coastal_mods_grass", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitatMods/eelgrass_2")),
               ("coastal_mods_hdunes", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitatMods/HighDunes_3")),
               ("coastal_mods_ldunes", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitatMods/LowDunes_4")),
               ("coastal_mods_kelp", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitatMods/kelp_1")),
               ("coastal_blz_coral", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat_BZ/corals_1")),
               ("coastal_blz_grove", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat_BZ/mangrove_2")),
               ("coastal_blz_grass", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat_BZ/seagrass_3")),
               ("coastal_grass", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat/eelgrass_2")),
               ("coastal_hdunes", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat/HighDunes_3")),
               ("coastal_ldunes", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat/LowDunes_4")),
               ("coastal_kelp", os.path.join(data_path, "CoastalProtection/Input/NaturalHabitat/kelp_1")),
               ("coastal_vargas_pt", os.path.join(data_path, "CoastalProtection/Input/LandPoint_VargasIsland")),
               ("coastal_shelf", os.path.join(data_path, "CoastalProtection/Input/continentalShelf")),
               ("mwq_tide", os.path.join(data_path, "MarineWaterQuality/input/TideE_WGS1984_BCAlbers")),
               ("mwq_clay_homes", os.path.join(data_path, "MarineWaterQuality/input/AOI_clay_soundwideWQ")),
               ("mwq_homes", os.path.join(data_path, "MarineWaterQuality/input/floathomes_centroids")),
               ("mwq_adv", os.path.join(data_path, "MarineWaterQuality/input/ADVuv_WGS1984_BCAlbers")),
               ("mwq_land", os.path.join(data_path, "MarineWaterQuality/input/3005_VI_landPolygon"))]


coverage_store = [("base_data_freshwater_dem", os.path.join(data_path, "Base_Data/Freshwater/dem.tif"))]

workspace = "invest"
workspace_url = "http://esws.unige.ch"

cat = geoserver.catalog.Catalog(rest_url, username, password)

if workspace not in [ws.name for ws in cat.get_workspaces()]:
    ws = cat.create_workspace(workspace, workspace_url)
##else:
##    raise NameError, "Existing workspace %s" % workspace


for data_store_name, data_store_path in data_stores:
    print "Processing store %s" % data_store_name

    shapefile_plus_sidecars = {}
    for key in ["shp", "shx", "prj", "dbf"]:
        shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

    ft = cat.create_featurestore(data_store_name, workspace=workspace, data=shapefile_plus_sidecars)
    
    #ds = cat.create_datastore(data_store_name, workspace)

    #ds.connection_parameters.update(host='localhost', port='5432', database='postgis', user='postgres', passwd='password', dbtype='postgis', schema='postgis')
    #cat.save(ds)

    #ft = cat.publish_featuretype('newLayerName', ds, 'EPSG:4326', srs='EPSG:4326')
    #cat.save(ft)               

#isinstance(resource, geoserver.resource.Coverage)
#isinstance(resource, geoserver.resource.FeatureType)

##for l in cat.get_layers():
##    print l.name
