import os
import subprocess
from date_checker import date_boundary
from section import *

def ply_to_bin(overwrite,src,dest):
    
    print("Converting .ply files to .bin files")
    print("")
    
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
            
        #Path to the CloudCompare exe file
        cc_path =r"C:\Program Files\CloudCompare\CloudCompare.exe"
        start = timer()
        
        #Create destination folders if they don't already exist
        os.makedirs(dest + "\\BIN Files",exist_ok=True)
        os.makedirs(dest + "\\PLY Files",exist_ok=True)
    
        
        #List the ply files in the src directory for this section and week
        ply_files = [x for x in os.listdir(src) if "Zone" + section in x and date_boundary(x,week)]
        
        
        for filename in ply_files:
            
            #Path to the current ply file
            current_file_path = src + "\\"  + filename
            
            #Bin file name
            dest_file_path = dest + "\\BIN Files\\" + filename.replace('.ply','.bin')
            generated_bin_file = src + "\\" + filename.replace(".ply",".bin")
            
            #Check if the bin file already exists
            bin_path_exists = os.path.exists(dest_file_path)
            
            if not bin_path_exists or overwrite:
                
                #Save cloud in bin format
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -NO_TIMESTAMP prevents the saved files having timestamps in their name
                # -O cloud opens the file with path given by cloud
                # -SAVE_CLOUDS saves all open clouds
                bin_time_start = timer()
                subprocess.run([cc_path, "-SILENT", "-NO_TIMESTAMP","-O", current_file_path, "-SAVE_CLOUDS"], shell = True)
                bin_time_end = timer()
    
                print("Created corresponding BIN file for ")  
                print(current_file_path)
                print("in " + str(round(bin_time_end-bin_time_start)) + " seconds.") 
                print("")
           
                
                
                #Deletes old file if it already exists and the overwrite option was on 
                if bin_path_exists and overwrite:
                    os.remove(dest_file_path)
                #Move bin file to the destination bin folder
                os.rename(generated_bin_file,dest_file_path)
            
            else:
                print("The BIN file for " + filename + " already exists!")
                print("")
            
            #Check if the ply file already exists
            ply_path_exists = os.path.exists(dest + "\\PLY Files\\" + filename)
            
            if not ply_path_exists or overwrite:
                if ply_path_exists and overwrite:
                    #Deletes old file if it already exists and the overwrite option was on
                    os.remove(dest + "\\PLY Files\\" + filename)
                #Move ply file to the ply folder
                os.rename(src + "\\" + filename,dest + "\\PLY Files\\" + filename)
            else:
                #File already exists in its destination folder and overwrite is not on so delete
                os.remove(src + "\\" + filename)
    
    
        end = timer()
        print("Total time elapsed: " + str(round(end-start)) + " seconds.")     
