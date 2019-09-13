# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 14:38:20 2019

@author: msjr2, jt667
"""
import numpy
import os
# if you don't have these already- they're pretty easy to install if you have anaconda
# launch the anaconda prompt and type: conda install numpy <Enter>, conda install gdal <Enter>
try:
    from osgeo import gdal, ogr
except:
    import gdal, ogr

from date_checker import date_boundary
from section_week import *
gdal.UseExceptions()

def readFile(filename):
    #Open the raster
    filehandle = gdal.Open(filename)
    
    #Read the 4th band of the raster (the M3C2 band)
    band1 = filehandle.GetRasterBand(4)
    
    #Read the geometry details from the raster / band
    geotransform = filehandle.GetGeoTransform()
    geoproj = filehandle.GetProjection()
    Z = band1.ReadAsArray()
    xsize = filehandle.RasterXSize
    ysize = filehandle.RasterYSize
    
    #Close the file
    filehandle = None
    del filehandle
    
    #Return geometry details
    return xsize,ysize,geotransform,geoproj,Z

def writeFile(filename,geotransform,geoprojection,data):
    
    (x,y) = data.shape
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    
    # you can change the dataformat but be sure to be able to store negative values including -9999
    
    #Create raster with the same geometry data as entered
    dst_datatype = gdal.GDT_Float32
    dst_ds = driver.Create(filename,y,x,1,dst_datatype)
    dst_ds.GetRasterBand(1).WriteArray(data)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(geoprojection)
    
    #Set the no data value to 9999 (although there should be no no data values)
    dst_ds.GetRasterBand(1).SetNoDataValue(9999)
    
    #Close the file
    dst_ds = None
    del dst_ds
    
    return 1

def generateContours(overwrite,src,dest):
    #Create destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
    
    dated_sections = determine_section_week_contour(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        #List of all the rasters in the current week and section that has the M3C2 layer
        all_files = [x for x in os.listdir(src) if "Zone" + section in x and date_boundary(x,week) and "Raster_Z.tif" in x]
        
        for filename in all_files:     
            
            #Check if the path already exists 
            if overwrite or not os.path.exists(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shp").replace("Raster_Z","")):
                pathname = src + "\\" + filename
                writefilename = src + "\\" + filename.replace(".tif","_temp.tif")
            
                #Read M3C2 band from raster
                [xsize,ysize,geotransform,geoproj,Z] = readFile(pathname)
                
                #Set NaN values to 9999
                Z[numpy.isnan(Z)] = 9999
                
                #Rewrite the M3C2 band to a file
                writeFile(writefilename,geotransform,geoproj,Z)
                
                print("Contour plotting for: ")
                print(filename)
                print("")
                #Import your image from file. Select band to contour. If a DSM will probably be band 1.
                image=gdal.Open(src + "\\" + filename.replace(".tif","_temp.tif"))
                band=image.GetRasterBand(1)
            
                #Generate shapefile to save Contourlines in
                outShapefile = pathname.replace(".tif","")
                driver = ogr.GetDriverByName("ESRI Shapefile")
            
                
                #Generates new layer in shapefile
                outDataSource = driver.CreateDataSource( outShapefile + ".shp" )
                layer=outDataSource.CreateLayer('contour')
                
                #Add fields to new layer in shapefile. 
                #These are shown in attribute tabe in ArcGIS. 
                #Set Precision sets the precision to # number of decimal places
                id_field = ogr.FieldDefn("ID", ogr.OFTInteger)
                layer.CreateField(id_field)
                length_field=ogr.FieldDefn("Length", ogr.OFTReal)
                length_field.SetPrecision(8)
                layer.CreateField(length_field)
                area_field = ogr.FieldDefn("Area", ogr.OFTReal)
                area_field.SetPrecision(8)
                layer.CreateField(area_field)
                m3c2_field = ogr.FieldDefn("M3C2", ogr.OFTReal)
                m3c2_field.SetPrecision(5)
                layer.CreateField(m3c2_field)
                
                """
                Generate Contourlines. 
                band= band of raster layer to contour- as defined above
                0.003 - contour interval value
                -0.4- first contour value
                [] - List takes priority over the previous two arguments, contours are only at these levels
                0
                0
                layer - the output layer
                0 - the index of the id field
                3 - the index of the elevation (M3C2) field
                """
                
                
                
                gdal.ContourGenerate(band, 0.003, -0.4, [x / 1000 for x in range(-3000,0,1)], 0, 0, layer, 0, 3)
                
                #gdal.ContourGenerate(band, 0.003, -0.4, [x / 10000 for x in range(-3000,0,1)], 0, 0, layer, 0, 3)
                
                #delete particular features in attribute table.
                for features in layer:
                    geom=features.GetGeometryRef()
                    
                    length=geom.Length()
                    area = geom.Area()
                    
                    features.SetField("Length", length)# add length value to each feature
                    features.SetField("Area", area)# add area value to each feature
                    layer.SetFeature(features)
                    
                    #Delete contours with length less than 0.2m or area less than 0.001m^2
                    if length<0.2 or area < 0.001:
                        layer.DeleteFeature(features.GetFID())
                    
                
                #delete data source at the end. Important to do this otherwise code gets stuck!      
                image = None
                del image
                outDataSource=None
                del outDataSource
                
                #Delete old output files if they exists and the overwrite option is on
                #Rename new file
                if overwrite and os.path.exists(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shp").replace("Raster_Z","")):
                    os.remove(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shp")).replace("Raster_Z","")
                os.rename(outShapefile + ".shp",dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shp").replace("Raster_Z",""))
                
                
                if os.path.exists(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.dbf").replace("Raster_Z","")):
                    os.remove(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.dbf").replace("Raster_Z",""))
                os.rename(outShapefile + ".dbf",dest + "\\" + filename.replace(".tif","_Contour_Shapefile.dbf").replace("Raster_Z",""))
                
                
                if os.path.exists(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shx").replace("Raster_Z","")):
                    os.remove(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shx").replace("Raster_Z",""))
                os.rename(outShapefile + ".shx",dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shx").replace("Raster_Z",""))
                
                os.remove(writefilename)
        print("Section " + section + " Week " + week + " Completed")
        print("")
