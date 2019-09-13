import os
import subprocess
from date_checker import date_boundary
from section_week import *
def diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif

def crop(overwrite,src,dest):
    print("Cropping the clouds")
    print("")
    #Path to the CloudCompare exe file
    cc_path =r"C:\Program Files\CloudCompare\CloudCompare.exe"
    
    #Creates the destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        #Read the cropping dimensions for each of the four pallets
        with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_1.txt") as pallet_dims:
            pallet_1_dims = pallet_dims.readline()
        with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_2.txt") as pallet_dims:
            pallet_2_dims = pallet_dims.readline()
        with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_3.txt") as pallet_dims:
            pallet_3_dims = pallet_dims.readline()
        with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_4.txt") as pallet_dims:
            pallet_4_dims = pallet_dims.readline()
        
        
        #List the bin files in src for this section and week that have either been shifted using the median or are the first day of the week
        bin_files = [x for x in os.listdir(src) if "Zone" + section in x and date_boundary(x,week) and ("Z_Shifted" in x or "201808" + str(13 + (int(week)-1)*7) in x )]
        #List all the files in the src directory
        all_files = os.listdir(src)
        
        for filename in bin_files:
            #Path to the current bin file
            bin_path = src + "\\" + filename
            #Checks if the cropped bin file exists
            path_exists = os.path.exists(dest + "\\" +  filename.replace(".bin","_Cropped.bin") )
            
            if not path_exists or overwrite:
                
                #Crops the four pallets out of the cloud and saves then in individual files
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -O opens the file listed directly after
                # -CROP crops all loaded clouds with parameters {Xmin:Ymin:Zmin:Xmax:Ymax:Zmax}
                # -CLEAR clears all the loaded clouds
                subprocess.run([cc_path,"-SILENT", "-O",bin_path,"-CROP", pallet_1_dims ,"-CLEAR","-O",bin_path, 
                                "-CROP", pallet_2_dims,"-CLEAR", "-O",bin_path,"-CROP", pallet_3_dims,"-CLEAR", "-O",bin_path, "-CROP", 
                                pallet_4_dims ] ,shell = True)
        
        
                bin_path = bin_path.replace(".bin","")
                print("Cropped the clouds for:")
                print(bin_path)
                print("")
                
                #Lists the cropped pallet files and assigns their file paths to variables
                pallet_files = diff(os.listdir(src),all_files)
                pallet_1 = src + "\\" + pallet_files[0]
                pallet_2 = src + "\\" + pallet_files[1]
                pallet_3 = src + "\\" + pallet_files[2]
                pallet_4 = src + "\\" + pallet_files[3]
               
                #Merges the four pallets into one cloud
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -O opens the file listed directly after
                # -MERGE_CLOUDS merges all the loaded clouds
                subprocess.run([cc_path,"-SILENT","-O", pallet_1,"-O",pallet_2,"-O",pallet_3,"-O",pallet_4,"-MERGE_CLOUDS"],shell = True)
                
                print("Merged cropped clouds for:")
                print(bin_path)
                print("")
                
                #Deletes the indivdually cropped pallet files
                os.remove(pallet_1)
                os.remove(pallet_2)
                os.remove(pallet_3)
                os.remove(pallet_4)
                
                #Finds the name of the merged file by comparing the list of files from before the cropping with the current list of files in the src directory
                merge_file = diff(os.listdir(src),all_files)[0] 
                
                #Deletes the old merged file if it already exists and the overwrite option was on
                if path_exists and overwrite:
                    os.remove(dest + "\\" + filename.replace(".bin","_Cropped.bin"))
                #Moves the merged file to the dest folder and adds "_Cropped" to the original filename
                os.rename(src + "\\" + merge_file,dest + "\\" + filename.replace(".bin","_Cropped.bin"))
                
        print("Section " + section + " week " + week + " completed.")
        print("")
