import os
import subprocess
from date_checker import date_boundary 
from section_week import *
def diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif

def rasterize(overwrite,src,dest,grid_step,SF):
    print("Rasterizing cloud with " + SF)
    print("")
    
    #Path to the CloudCompare exe file
    cc_path = r"C:\Program Files\CloudCompare\CloudCompare.exe"

    #Create destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
  
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        
        #List of the files for this section and week
        m3c2_files = [ x for x in os.listdir(src) if  "Zone" + section in x and date_boundary(x,week)]
        
        for filename in m3c2_files:
            #Current file path
            cropped_path = src + "\\" + filename
            
            #Destination file path
            new_file_path = dest + "\\" + filename.replace(".bin","Raster_" + SF + ".tif")
            
            #Check if the new file path exists 
            path_exists = os.path.exists(new_file_path)
            if not path_exists or overwrite:
    
                #Performs the M3C2 comparison
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -O cloud opens the file with path given by cloud
                # -RASTERIZE rasterizes the loaded clouds with -GRID_STEP given by grid_step
                # -OUTPUT_RASTER_Z outputs the result as a geotiff raster (altitudes + all SFs by default)
                subprocess.run([cc_path,"-SILENT", "-O", cropped_path,"-RASTERIZE", "-GRID_STEP", grid_step,"-OUTPUT_RASTER_" + SF], shell = True)
                
                #Filename for the raster
                new_raster_file = [file for file in os.listdir(src) if (filename.replace(".bin","") in file and "RASTER" in file)][0]
                
                #Deletes the old raster if it exists and the overwrite option is on
                if path_exists and overwrite:
                    os.remove(new_file_path)
                
                #Rename the new raster
                os.rename(src + "\\" + new_raster_file, new_file_path)
    
    
        print("Section " + section + " week " + week + " completed.")
        print("")
        
                
             
             
             
             
