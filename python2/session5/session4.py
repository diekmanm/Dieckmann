import gdal
import glob
import os
import numpy as np
import numpy.ma as ma
from numpy import *
#import ArcPy
#from PIL import Image
from collections import Counter


dem = gdal.Open("/Users/Maria/python/DEM_Humboldt_sub.tif")
slope = gdal.Open("/Users/Maria/python/SLOPE_Humboldt_sub.tif")
thp = gdal.Open("/Users/Maria/python/THP_Humboldt_sub.tif")

gt_dem = dem.GetGeoTransform()
gt_slope = slope.GetGeoTransform()
gt_thp = thp.GetGeoTransform()


root_folder = "/Users/Maria/python/"

file_list = glob.glob(os.path.join(root_folder + "*.tif"))
print(file_list)

def readcoordinates(file_list):
    UL_x_list = list()
    UL_y_list = list()
    LR_x_list = list()
    LR_y_list = list()
    pixelsize_list = list()
    for i in file_list:
        ds = gdal.Open(i)
        gt = ds.GetGeoTransform()
        UL_x, UL_y = gt[0], gt[3]
        LR_x = UL_x + (gt[1] * ds.RasterXSize)
        LR_y = UL_y + (gt[5] * ds.RasterYSize)
        UL_x_list.append(UL_x)
        UL_y_list.append(UL_y)
        LR_x_list.append(LR_x)
        LR_y_list.append(LR_y)
        pixelsize_list.append(gt[1])
        print(os.path.basename(i), "UL_x is", UL_x, "UL_y is", UL_y, "LR_x is", LR_x, "LR_y is", LR_y)
    print("UL_x is", max(UL_x_list), "UL_y is", min(UL_y_list))
    print("LR_x is", min(LR_x_list), "LR_y is", max(LR_y_list))
    print("pixel sizes in feet", pixelsize_list)
    print("Range x:", (min(LR_x_list)-max(UL_x_list))/gt[1], "pixels")
    print("Range y:", (min(UL_y_list)-max(LR_y_list))/gt[1], "pixels")

readcoordinates(file_list)


###get arrays###
inv_gt_dem = gdal.InvGeoTransform(gt_dem)
print(inv_gt_dem)
offset_dem = gdal.ApplyGeoTransform(inv_gt_dem, 1399618.9749825108, 705060.6257949192)
xoff, yoff = map(int, offset_dem)
array_dem = dem.ReadAsArray(xoff, yoff, 599, 1240)
print("Array DEM ", array_dem)

inv_gt_slope = gdal.InvGeoTransform(gt_slope)
print(inv_gt_slope)
offset_slope = gdal.ApplyGeoTransform(inv_gt_slope, 1399618.9749825108, 705060.6257949192)
xoff1, yoff1 = map(int, offset_slope)
array_slope = slope.ReadAsArray(xoff1, yoff1, 599, 1240)
print("Array SLOPE ", array_slope)

inv_gt_thp = gdal.InvGeoTransform(gt_thp)
print(inv_gt_thp)
offset_thp = gdal.ApplyGeoTransform(inv_gt_thp, 1399618.9749825108, 705060.6257949192)
xoff2, yoff2 = map(int, offset_thp)
array_thp = thp.ReadAsArray(xoff2, yoff2, 599, 1240)
print("Array THP ", array_thp)

comp_dem = ma.masked_where(array_dem >= 3000, array_dem)
comp_dem_copy = ma.masked_where(array_dem >= 2000, array_dem).copy()
print("DEM", comp_dem)
comp_slope = ma.masked_where(array_slope < 0, array_slope)
comp_slope_copy = ma.masked_where(array_slope < 0, array_slope).copy()
print("SLOPE", comp_slope)
comp_thp = ma.masked_where(array_thp >= 10000, array_thp)
comp_thp_copy = ma.masked_where(array_thp >= 10000, array_thp).copy()
print(comp_thp)

print("Mean of DEM: ", np.mean(comp_dem_copy), "Min of DEM: ", np.min(comp_dem_copy), "Max of DEM: ", np.max(comp_dem_copy))
print("Mean of slope: ", np.mean(comp_slope_copy), "Min of slope: ", np.min(comp_slope_copy), "Max of slope: ", np.max(comp_slope_copy))


#Now take the elevation and slope layers only, and build a binary mask in which areas with elevation
#< 1000m and slope <30deg have the value ‘1’, and all other areas the value ‘0’. Write this binary
#mask into a new raster file and upload it to moodle.

arr_dem_slope = ma.dstack((comp_dem_copy, comp_slope_copy))
print("Stack   ",arr_dem_slope)



print(arr_dem_slope.shape)

a = arr_dem_slope[:,:,0].copy()
b = arr_dem_slope[:,:,1].copy()
print("DEM:", a)
print("SLOPE:",b)
#print(ma.array(a, mask=np.isnan(a)))
#print(ma.array(b, mask=np.isnan(b)))


test = (a < 1000) & (b < 30)

print("Test:", test)
print("Shape of test", test.shape)
#test.sort()
#print("SORTED TEST:", test)
testy = test * 1
#print("Testy: ",test)
testy.sort()
print("SORTED:", testy)
print(ma.max(testy))


####write array into raster
dst_filename = 'xxx.tiff'
x_pixels = 599  # number of pixels in x
y_pixels = 1240  # number of pixels in y
driver = gdal.GetDriverByName('GTiff')
outds = driver.Create(dst_filename,x_pixels, y_pixels, 1)
outds.GetRasterBand(1).WriteArray(test)

# follow code is adding GeoTranform and Projection
geotrans=dem.GetGeoTransform()  #get GeoTranform from existed 'data0'
proj=dem.GetProjection() #you can get from a exsited tif or import
outds.SetGeoTransform(geotrans)
outds.SetProjection(proj)
outds.FlushCache()
outds=None
value1 = (testy == 1).sum()
value0 = (testy == 0).sum()
print(value1, value0)

binary_ras = gdal.Open(root_folder + "xxx.tiff")
gt_bin_ras = binary_ras.GetGeoTransform()
pixelSizeX = gt_bin_ras[1]
pixelSizeY =-gt_bin_ras[5]
print(pixelSizeX)
print(pixelSizeY)
area = (599*1240)
print("Area ", "%.2f" % area, "Fuß")

print("number of pixels with value 1: " + str(value1))
print("number of pixels with value 0: " + str(value0))
percentage = ((value1 / area) * 100.0)
print("percentage of pixels with value 1:", "%.2f" % percentage, "%")




#task 2
#array_combined = ma.concatenate([comp_dem_copy, comp_slope_copy, comp_thp_copy], axis = 1)
#print(array_combined)

