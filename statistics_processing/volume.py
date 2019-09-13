# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:50:32 2019

@author: jt667
"""
from date_checker import date_boundary
from shapely.geometry import Polygon, Point
from osgeo import gdal
from osgeo import ogr
from section_week import *
import os
import re

class Contour_Polygon:
    
    def __init__(self,FID,layer,pallet_bounds,pallet_points):
        self.FID = FID
        self.layer = layer
        
        #Gets the feature from the layer given by the FID
        self.feature = layer.GetFeature(FID)
        
        #Convert the feature to a shapely polygon
        self.polygon = self.feature_to_poly()
        self.differenced_polygon = self.polygon
        
        #Get the M3C2 value 
        self.M3C2 = self.feature.GetField(3)
        
        #Get the volume of the contour (this assumes there are now contours below it)
        self.volume = - self.polygon.area * self.M3C2
        
        #Checks the pallet that the contour is contained in
        self.pallet = self.pallet_checker(pallet_bounds)
        
        #Check which points the contour contains
        self.points = self.contained_points(pallet_points)
        
        self.contained = 0
        self.within = 0
        self.volume_below = self.volume

    def feature_to_poly(self):
        #Get the string representation of the contour
        featurenodes = self.feature.GetGeometryRef().ExportToWkt().replace("LINESTRING ","").split(",")[:-1]
        featurenodes[0] = featurenodes[0][1:]
        
        #Split the coordinates into x,y pairs
        featurenodes = [(float(featurenodes[i].split()[0]),float(featurenodes[i].split()[1])) for i in range(len(featurenodes))]
        
        #Generate polygon from nodes
        poly = Polygon(featurenodes)
        
        #If the contour overlaps itself use buffer which removes the overlap
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly
    
    def differencing(self,poly):
        #Check if the contour contains the poly contour
        if self.FID != poly.FID and self.differenced_polygon.contains(poly.polygon):
            #Remove the overlapping area 
            self.differenced_polygon = self.polygon.difference(poly.polygon)
            
            #Update volume
            self.volume = -self.differenced_polygon.area * self.M3C2
            self.volume_below = self.volume
            
            #Update number of contours contained
            self.contained += 1
            
            #Update number of contours within
            poly.within += 1
    
    def pallet_checker(self,pallets):
        #Check if a pallet contains or overlaps with a polygon
        if pallets[0].contains(self.polygon) or pallets[0].overlaps(self.polygon):
            return 0
        if pallets[1].contains(self.polygon) or pallets[1].overlaps(self.polygon):
            return 1
        if pallets[2].contains(self.polygon) or pallets[2].overlaps(self.polygon):
            return 2
        if pallets[3].contains(self.polygon) or pallets[3].overlaps(self.polygon):
            return 3
        print(self.FID)
        
        
    def contained_points(self,points_to_check):
        contained = ""
        for point in points_to_check[self.pallet]:
            #If the polygon contains a point, add it to the list and update the number of contours the point is within
            if self.polygon.contains(point.shapely_point):
                contained += point.id + ","
                point.within += 1
        if len(contained) > 0:
            return contained[:-1]
        return contained
    
    def total_volume(self, poly):
        #Add the volume of the differenced polygons contained beneath this polygon
        if self.FID != poly.FID and self.differenced_polygon.contains(poly.differenced_polygon):
            self.volume_below -= poly.differenced_polygon.area * poly.M3C2
    
class Plant_Point:
    point_id = 0
    
    def __init__(self,coords,pallet_bounds):
        coords= coords.replace("\)","").replace(" ","").replace("\(","")
        
        #Set x,y coordinates
        self.x = float(coords.split(",")[0])
        self.y = float(coords.split(",")[1])
        
        #Generate shapely point and ogr point
        self.shapely_point = Point(self.x,self.y)
        self.arc_point = ogr.Geometry(ogr.wkbPoint)
        self.arc_point.SetPoint(0,self.x,self.y)
        
        #Check the pallet the point is contained in 
        self.pallet = self.pallet_checker(pallet_bounds)
        
        #Generate point id
        self.id = str(self.pallet + 1)  + "_" + str(self.point_id)
        Plant_Point.point_id += 1
        
        self.within = 0

        
    def pallet_checker(self,pallets):
        #Check if a pallet contains or overlaps with a point
        if pallets[0].contains(self.shapely_point):
            return 0
        if pallets[1].contains(self.shapely_point):
            return 1
        if pallets[2].contains(self.shapely_point):
            return 2
        if pallets[3].contains(self.shapely_point):
            return 3
        
        
def estimated_volume_check(overwrite,volume_file,section,week):
    #Check if the estimated volume file exists or the overwrite option is on
    if not os.path.exists(volume_file) or overwrite:
        #Creates estimated volume file
        with open(volume_file,"w") as file:
            file.write("Week " + week + " Section " + section + "\n")
        return False
    return True


def pallet_dimensions(section,week):       
    pallet_polygons = []
    pallet_dimensions = []
    
    #Read pallet dimensions
    for i in range(1,5):
        with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_" + str(i) + ".txt") as pallet_dims:
            pallet_dimensions += [pallet_dims.readline().split(":")]
    for i in range(4):
        pallet_dimensions[i] = pallet_dimensions[i][0:2] + pallet_dimensions[i][3:5]
        pallet_dimensions[i] = [(float(pallet_dimensions[i][0]),float(pallet_dimensions[i][1])),(float(pallet_dimensions[i][0]),float(pallet_dimensions[i][3])),(float(pallet_dimensions[i][2]),float(pallet_dimensions[i][3])),(float(pallet_dimensions[i][2]),float(pallet_dimensions[i][1]))]
        
        #Create polygons from the pallet dimensions
        pallet_polygons += [Polygon(pallet_dimensions[i])]
    return pallet_polygons
    

def volume_calculation(overwrite,src,dest,point_folder):
    
    gdal.UseExceptions()
    
    #Created destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
    
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        #List of shapefiles for the current section and week
        shapefiles = [x for x in os.listdir(src) if ".shp" in x and "Zone" + section in x and date_boundary(x,week) and not ".lock" in x ]
        
        #Generate polygons for the pallets 
        pallet_bounds = pallet_dimensions(section,week)
        
        #Read points file
        with open(point_folder + "\\" + week + section + ".txt.") as points_file:
            plant_points = points_file.readlines()
        
        pallet_points = [[],[],[],[]]
        for point in plant_points:
            #Read pairs of coordinates that are written on lines like: x,y 
            if "," in point and not re.search("[a-zA-Z]",point):
                #Generate points
                temp_point = Plant_Point(point,pallet_bounds)
                pallet_points[temp_point.pallet] += [temp_point]
            
        for filename in shapefiles:
            data_file = dest + "\\" + filename.replace("Shapefile","Data")
            volume_file = dest + "\\" + filename.replace("_Contour_Shapefile.shp","_Volumes.txt")
            if not os.path.exists(data_file) or overwrite:
                shape_file_path = src + "\\" + filename
                driver = ogr.GetDriverByName("ESRI Shapefile")
                dataSource = driver.Open(shape_file_path, 0)
                contour_layer = dataSource.GetLayer()
                
                feature_list = []
                
                #Create list of contours
                for i in range (contour_layer.GetFeatureCount()):
                    feature_list += [Contour_Polygon(i,contour_layer,pallet_bounds,pallet_points)]
                
                #Difference overlapping polygons
                for poly1 in feature_list:
                    for poly2 in feature_list:
                        poly1.differencing(poly2)
                
                #Calculate total volume below contours
                for poly1 in feature_list:
                    for poly2 in feature_list:
                        poly1.total_volume(poly2)
                
                #Write estimated volume totals to file 
                if not estimated_volume_check(overwrite,volume_file,section,week):
                    estimated_volumes = [0,0,0,0,0]
                    for poly in feature_list:
                        estimated_volumes[poly.pallet] += poly.volume
                    with open(volume_file,"a") as file:
                        for i in range(4):
                            file.write("Pallet " + str(i + 1) + ":" + str(estimated_volumes[i]) + "m^3 \n")
                
                #Create output contour file
                outShapefile = src + "\\" + filename.replace("shp","")
                driver = ogr.GetDriverByName("ESRI Shapefile")
                outDataSource = driver.CreateDataSource( outShapefile + ".shp" )
                
                contour_layer=outDataSource.CreateLayer('contour')
                
                #Create output fields
                length_field=ogr.FieldDefn("Length", ogr.OFTReal)
                length_field.SetPrecision(8)
                contour_layer.CreateField(length_field)
                area_field = ogr.FieldDefn("Area", ogr.OFTReal)
                area_field.SetPrecision(8)
                contour_layer.CreateField(area_field)
                d_area_field = ogr.FieldDefn("D Area", ogr.OFTReal)
                d_area_field.SetPrecision(8)
                contour_layer.CreateField(d_area_field)
                volume_field = ogr.FieldDefn("Volume", ogr.OFTReal)
                volume_field.SetPrecision(8)
                contour_layer.CreateField(volume_field)
                d_volume_field = ogr.FieldDefn("D Volume", ogr.OFTReal)
                d_volume_field.SetPrecision(8)
                contour_layer.CreateField(d_volume_field)
                m3c2_field = ogr.FieldDefn("M3C2", ogr.OFTReal)
                m3c2_field.SetPrecision(5)
                contour_layer.CreateField(m3c2_field)
                pallet_field = ogr.FieldDefn("Pallet", ogr.OFTInteger)
                contour_layer.CreateField(pallet_field)
                point_list_field = ogr.FieldDefn("Point", ogr.OFTString)
                contour_layer.CreateField(point_list_field)
                contained_field = ogr.FieldDefn("Contained", ogr.OFTInteger)
                contour_layer.CreateField(contained_field)
                within_field = ogr.FieldDefn("Within", ogr.OFTInteger)
                contour_layer.CreateField(within_field)
    
    
                #Add contours to file with fields
                for contour in feature_list:
                    featureDefn = contour_layer.GetLayerDefn()
                    feature = ogr.Feature(featureDefn)
                    feature.SetGeometry(contour.feature.GetGeometryRef())
                    feature.SetFID(contour.FID)
                    feature.SetField("Length", contour.polygon.length)
                    feature.SetField("Area", contour.polygon.area)
                    feature.SetField("D Area", contour.differenced_polygon.area)
                    feature.SetField("Volume", contour.volume_below)
                    feature.SetField("D Volume", contour.volume)
                    feature.SetField("M3C2", contour.M3C2)
                    feature.SetField("Pallet",contour.pallet + 1)
                    feature.SetField("Point", contour.points)
                    feature.SetField("Contained",contour.contained)
                    feature.SetField("Within", contour.within)
                    contour_layer.CreateFeature(feature)
                    feature = None
    
                #Close contour file
                outDataSource=None
                del outDataSource
    
                #Delete files if they already exist and the overwrite option is on
                #Rename the new files
                if overwrite and os.path.exists(data_file):
                    os.remove(dest + "\\" + filename.replace(".tif","_Contour_Shapefile.shp")).replace("Raster_Z","")
                os.rename(outShapefile + ".shp",data_file)
                
                
                if os.path.exists(data_file.replace(".shp",".dbf")):
                    os.remove(data_file.replace(".shp",".dbf"))
                os.rename(outShapefile + ".dbf",data_file.replace(".shp",".dbf"))
                
                
                if os.path.exists(data_file.replace(".shp",".shx")):
                    os.remove(data_file.replace(".shp",".shx"))
                os.rename(outShapefile + ".shx",data_file.replace(".shp",".shx"))
    
    
                #Create point file
                outShapefile = src + "\\" + filename.replace("shp","") + "points"
                driver = ogr.GetDriverByName("ESRI Shapefile")
                outDataSource = driver.CreateDataSource( outShapefile  +".shp" )
                
                point_layer = outDataSource.CreateLayer('points')
                
                #Create output fields
                point_pallet_field =  ogr.FieldDefn("Pallet", ogr.OFTInteger)
                point_layer.CreateField(point_pallet_field)
                point_point_list_field = ogr.FieldDefn("Point", ogr.OFTString)
                point_layer.CreateField(point_point_list_field)
                point_within_field = ogr.FieldDefn("Within", ogr.OFTInteger)
                point_layer.CreateField(point_within_field)
                x_field = ogr.FieldDefn("X", ogr.OFTReal)
                x_field.SetPrecision(8)
                point_layer.CreateField(x_field)
                y_field = ogr.FieldDefn("Y", ogr.OFTReal)
                y_field.SetPrecision(8)
                point_layer.CreateField(y_field)
    
                #Add points to file with fields
                for point_list in pallet_points:
                    for point in point_list:
                        featureDefn = point_layer.GetLayerDefn()
                        feature = ogr.Feature(featureDefn)
                        feature.SetGeometry(point.arc_point)
                        feature.SetField("Pallet",point.pallet + 1)
                        feature.SetField("Point", point.id)
                        feature.SetField("Within", point.within)
                        feature.SetField("X", point.x)
                        feature.SetField("Y", point.y)
                        point_layer.CreateFeature(feature)
                        feature = None
                
                #Close point file
                outDataSource=None
                del outDataSource
                
                
                #Delete files if they already exist and the overwrite option is on
                #Rename the new files
                if overwrite and os.path.exists(data_file.replace(".shp","points.shp")):
                    os.remove(dest + "\\" + filename.replace(".tif","_Contour_Shapefilepoints.shp")).replace("Raster_Z","")
                os.rename(outShapefile + ".shp",data_file.replace(".shp","points.shp"))
                
                
                if os.path.exists(data_file.replace(".shp","points.dbf")):
                    os.remove(data_file.replace(".shp","points.dbf"))
                os.rename(outShapefile + ".dbf",data_file.replace(".shp","points.dbf"))
                
                
                if os.path.exists(data_file.replace(".shp","points.shx")):
                    os.remove(data_file.replace(".shp","points.shx"))
                os.rename(outShapefile + ".shx",data_file.replace(".shp","points.shx"))
    
