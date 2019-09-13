import os
import subprocess
from date_checker import date_boundary
from timeit import default_timer as timer
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


def ply_to_bin(overwrite,src,dest,registration_folder):
    
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
        
        
        #Translate the bin file using the median given from the M3C2 calculation on the wooden edges of the pallet
        z_shift_bin(overwrite,dest + "\\BIN Files",registration_folder,section,week,cc_path)
    
    
        end = timer()
        print("Total time elapsed: " + str(round(end-start)) + " seconds.")     
