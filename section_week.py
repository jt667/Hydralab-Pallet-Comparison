# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 15:55:33 2019

@author: jt667
"""

import os
def determine_section_week(src):
    #Determines the section and week combinations in the source folder given 
    combinations = []
    for filename in os.listdir(src):
        section = filename[filename.find("Zone")+4:filename.find("Zone")+5]
        week = determine_week(filename[filename.find("201808")+6:filename.find("201808")+8])
        if [section, week] not in combinations:
            combinations.append([section,week])
    return combinations

def determine_section_week_contour(src):
    #Determines the section and week combinations in the source folder given (only allows you to use Z rasters and not RGB rasters)
    combinations = []
    for filename in os.listdir(src):
        section = filename[filename.find("Zone")+4:filename.find("Zone")+5]
        week = determine_week(filename[filename.find("201808")+6:filename.find("201808")+8])
        if [section, week] not in combinations and "Raster_Z" in filename:
            combinations.append([section,week])
    return combinations

def determine_week(date):
    #Determines the week that the current date is contained in
    if int(date) < 18:
        return "1"
    elif int(date) < 25:
        return "2"
    else:
        return "3"