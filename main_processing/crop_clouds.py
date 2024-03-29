import os
import subprocess
from date_checker import date_boundary
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
from section_week import *

def z_shift(current_file,section,first_day,registration_folder):
    #Find the date of the current file
    date_index = current_file.find("201808")  + 6
    date =  current_file[date_index:date_index + 2]
    
    #Path to the median error of the M3C2 comparison of the wooden pallets of the current date compared to the first day
    median_error = registration_folder + "\\" + first_day + date + section + ".txt"
    
    #Returns the median error given by the median_error file 
    with open(median_error) as median_error_file:
        median_z_shift = median_error_file.readlines()[0]
    return median_z_shift


def replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)

def shifted_cloud(current_file,current_file_path,registration_folder,section,first_day,cc_path):
    #Generates a file containg in a 4 x 4 affine transformation matrix, translation is given by the first three rows in the last column
    #Translation vertically given by the median M3C2 value of the wooden pallet comparision of the date of the current file compared to the file on the first day of the week
    transformation_matrix_path = registration_folder + r"\translation.txt"
    transformation_matrix_file = open(transformation_matrix_path,'w')
    transformation_matrix_file.write("1 0 0 0\n")
    transformation_matrix_file.write("0 1 0 0\n")
    transformation_matrix_file.write("0 0 1 " + str(-float(z_shift(current_file,section,first_day,registration_folder))) + "\n")
    transformation_matrix_file.write("0 0 0 1\n")
    transformation_matrix_file.close()
    
    #List of all the file in the src folder before the file is translated
    all_files = os.listdir(current_file_path.replace("\\" + current_file,""))
    
    #Translates cloud vertically
    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
    # -O current_file_path opens the file with path given by current_file_path
    # -APPLY_TRANS applies the transformation given by the file with path given by transformation_matrix_path
    subprocess.run([cc_path,"-SILENT","-O", current_file_path, "-APPLY_TRANS", transformation_matrix_path], shell=True)
    
    #Returns the filename of the shifted cloud
    return diff(all_files,os.listdir(current_file_path.replace("\\" + current_file,"")))[0]
                        

def diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif

def z_shift_bin(overwrite,src,registration_folder,section,week,cc_path):
    
    print("Shifting clouds towards the first day of the week")
    print("")
    
    #Folder containing median values for the z shifts
    registration_errors = registration_folder + "\\Median"
    
    #First day of the week
    first_day = str(13 + (int(week)-1)*7)
    
    #List of files to be shifted, only files of the current section and week, that have not already been shifted and are not the first day of the week
    shift_files = [x for x in os.listdir(src) if "_Z_Shifted" not in x and "201808" + first_day not in x and "Zone" + section in x and date_boundary(x,week)]

    
    
    
    for filename in shift_files:
        #File path to the current file being shifted
        shift_path = src + "\\" + filename
        
        #Check if the shifted file already exists
        path_exists = os.path.exists(shift_path.replace(".bin","_Z_Shifted.bin"))
        
        if not path_exists or overwrite:
            
            #Generates the shifted cloud file and stores the output name given
            time_stamped_name = shifted_cloud(filename,shift_path,registration_errors,section,first_day,cc_path)
            
            #Deletes file if it already exists and the overwrite option is on
            if path_exists and overwrite:
                os.remove(shift_path.replace(".bin","_Z_Shifted.bin"))
            
            #Removes the time stamp from the shifted file name and adds "_Z_Shifted" to the filename
            os.rename(shift_path.replace(filename,time_stamped_name),shift_path.replace(".bin","_Z_Shifted.bin"))

def get_pallet_numbers(section,week):
    #Gets the pallet numbers from their filenames
    return [x[-5] for x in os.listdir(os.getcwd() + "\\parameter_files\\cropping_dimensions") if section + "_" +  week in x ]

def cropping_pallets(bin_path,cropping_dimensions):
    #Returns a list of commands for subprocess 
    #e.g ["-O",bin_path,"-CROP",crop_dims[0],"-CLEAR","-O",bin_path,"-CROP",crop_dims[1],"-CLEAR"]
    
    open_list = ["-O" for x in range(len(cropping_dimensions))]
    bin_list = [bin_path for x in range(len(cropping_dimensions))]
    crop_list = ["-CROP" for x in range(len(cropping_dimensions))]
    clear_list = ["-CLEAR" for x in range(len(cropping_dimensions))]
    command_list = []
    for x in zip(open_list,bin_list,crop_list,cropping_dimensions,clear_list):
        command_list += list(x)
    return command_list
    
def pallet_list(pallet_files):
    open_list = ["-O" for x in range(len(pallet_files))]
    merge_list = []
    for x in zip(open_list,pallet_files):
        merge_list += list(x)
    return merge_list

def crop(overwrite,registration_folder,src,dest):
    #Path to the CloudCompare exe file
    cc_path = r"C:\Program Files\CloudCompare\CloudCompare.exe"
    
    #Creates the destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        
        #Translate the bin file using the median given from the M3C2 calculation on the wooden edges of the pallet
        z_shift_bin(overwrite,src,registration_folder,section,week,cc_path)
        
        print("Cropping the clouds")
        print("")
        
        pallet_dimensions = []
        
        #Read the cropping dimensions for each of the pallets
        for number in get_pallet_numbers(section,week):
            with open(os.getcwd() + "\\parameter_files\\cropping_dimensions\\" + section + "_" + week + "_pallet_" +  number + ".txt") as pallet_dims:
                pallet_dimensions += [pallet_dims.readline().replace("\n","")]
        
        
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
                #Cropping pallets produces the list containg command line code for any number of pallets
                subprocess.run([cc_path,"-SILENT"] + cropping_pallets(bin_path,pallet_dimensions) ,shell = True)
        
        
                bin_path = bin_path.replace(".bin","")
                print("Cropped the clouds for:")
                print(bin_path)
                print("")
                
                #Lists the cropped pallet files and assigns their file path
                pallet_files = [src + "\\" + x for x in diff(os.listdir(src),all_files)]
               
                #Merges the four pallets into one cloud
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -O opens the file listed directly after
                # -MERGE_CLOUDS merges all the loaded clouds
                subprocess.run([cc_path,"-SILENT"] + pallet_list(pallet_files) +["-MERGE_CLOUDS"],shell = True)
                
                print("Merged cropped clouds for:")
                print(bin_path)
                print("")
                
                #Deletes the individually cropped pallet files
                for pallet in pallet_files:
                    os.remove(pallet)
                
                #Finds the name of the merged file by comparing the list of files from before the cropping with the current list of files in the src directory
                merge_file = diff(os.listdir(src),all_files)[0] 
                
                #Deletes the old merged file if it already exists and the overwrite option was on
                if path_exists and overwrite:
                    os.remove(dest + "\\" + filename.replace(".bin","_Cropped.bin"))
                #Moves the merged file to the dest folder and adds "_Cropped" to the original filename
                os.rename(src + "\\" + merge_file,dest + "\\" + filename.replace(".bin","_Cropped.bin"))
                
        print("Section " + section + " week " + week + " completed.")
        print("")
