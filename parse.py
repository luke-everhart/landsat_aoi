import rasterio
import geopandas as gpd
from os import listdir
from sys import argv
from math import log

def get_TOA(M, Q, A):
    return (M*Q) + A

def get_BT(K1, K2, TOA):
    return ( K2 / (log( K1/TOA + 1)) ) - 273.15

def get_NVDI(B4, B5):
    return (B5 - B4) / (B5 + B4)

def get_PV(NDVI, min, max):
    return ( (NDVI - min) / (max + min) ) ** 2

def get_LSE(PV):
    return (0.004 * PV) + 0.986

def get_LST(BT, W, E):
    return BT + W * (BT / 1.438) * log(E)
    #return ( BT / (( 1 + ((W * BT) / 1.4380) ) * log(E) ))

# Pull in all raster files
data_path = "./data"
contents = listdir(data_path)

band4 = []
band5 = []
band10 = []

# Load files to raster objects
for tar in contents:
    raster_files = listdir(f"{data_path}/{tar}")
    for file in raster_files:
        if ("B10.TIF" in file):
            band10.append(rasterio.open(f"{data_path}/{tar}/{file}"))
        if ("B4.TIF" in file):
            band4.append(rasterio.open(f"{data_path}/{tar}/{file}"))
        if ("B5.TIF" in file):
            band5.append(rasterio.open(f"{data_path}/{tar}/{file}"))

    #rasters.append(rasterio.open(f"{data_path}/{tar}/{raster_file}"))

# Pull in line data
input_data_path = argv[1]
input_data = gpd.read_file(input_data_path)

# Enforce EPSG:32617
input_data = input_data.to_crs("EPSG:32617")

def set_NVDI():

    STUB4 = 140
    STUB5 = 150

    NVDI = get_NVDI(STUB4, STUB5)

    pass

def set_LST(row):

    # Calculate average raster value over length of linestring.
    coords = row['geometry'].coords

    total4 = 0 
    total5 = 0
    total10 = 0

    raster_count = len(band4)

    for i in range(len(coords)):
        for j in range(raster_count):
            x4, y4 = band4[j].index(coords[i][0], coords[i][1])
            raw4 = band4[j].read(1)
            total4 = total4 + int(raw4[x4, y4])

            x5, y5 = band5[j].index(coords[i][0], coords[i][1])
            raw5 = band5[j].read(1)
            total5 = total5 + int(raw5[x5, y5])

            x10, y10 = band10[j].index(coords[i][0], coords[i][1])
            raw10 = band10[j].read(1)
            total10 = total10 + int(raw10[x10, y10])
    
    avg4 = total4 / raster_count / len(coords)
    avg5 = total5 / raster_count / len(coords)
    avg10 = total10 / raster_count / len(coords)

    # Calculate Top of Atmospheric (TOA) Spectral Radiance
    radiance_multi_b10 = 3.8000E-04
    radiance_add_b10 = 0.10000
    TOA = get_TOA(radiance_multi_b10, avg10, radiance_add_b10)

    # Calculate top of atmosphere Brightness-temperature
    K1 = 799.0284
    K2 = 1329.2405

    # top of atmosphere Brightness-temperature
    BT = get_BT(K1, K2, TOA)

    # NDVI
    NVDI = get_NVDI(avg4, avg5)
    
    row["NDVI"] = NVDI

    # Min and Max were found statically on one raster. We assume these values for all calculations.
    NVDI_min = -0.236404
    NVDI_max = 0.672453

    # Proportion of Vegetation (PV)
    PV = get_PV(NVDI, NVDI_min, NVDI_max)

    # Land Surface Emissivity (E)
    E = get_LSE(PV)

    # Land Surface Temperature
    wavelength = 10.8

    LST = get_LST(BT, wavelength, E)

    row['LST'] = LST

    return row

    
input_data = input_data.apply(set_LST, axis=1)

input_data.to_file("out.geojson", driver="GeoJSON")

