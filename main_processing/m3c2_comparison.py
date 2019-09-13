import os
import subprocess
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
from date_checker import date_boundary
from section_week import *

def median_value(current_date,section,week,first_day,registration_folder):
    #If the current date is the same as the first day return 0 so there is no translation
    if current_date == first_day:
        return "0"
    
    #Median error file
    median_error = registration_folder + "\\" + first_day + current_date + section + ".txt"
    
    #Returns the median of the M3C2 comparison of the wooden pallet of the current day and the first day
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

def shift_cloud_to_median(current_date,current_file,current_folder,registration_folder,section,week,first_day,cc_path):
    #Generates a file containg in a 4 x 4 affine transformation matrix, translation is given by the first three rows in the last column
    #Translation vertically given by the median M3C2 value of the wooden pallet comparision of the date of the current file compared first_day_file
    transformation_matrix_path = registration_folder + r"\translation.txt"
    transformation_matrix_file = open(transformation_matrix_path,'w')
    transformation_matrix_file.write("1 0 0 0\n")
    transformation_matrix_file.write("0 1 0 0\n")
    transformation_matrix_file.write("0 0 1 " + str(-float(median_value(current_date,section,week,first_day,registration_folder))) + "\n")
    transformation_matrix_file.write("0 0 0 1\n")
    transformation_matrix_file.close()
    
    #List of all files in the current folder
    all_files = os.listdir(current_folder)
    
    #Translates cloud vertically
    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
    # -O current_file_path opens the file with path given by current_file_path
    # -APPLY_TRANS applies the transformation given by the file with path given by transformation_matrix_path
    subprocess.run([cc_path,"-SILENT","-O", current_folder + "\\" + current_file, "-APPLY_TRANS", transformation_matrix_path], shell=True)
    
    
    return diff(all_files,os.listdir(current_folder))[0]
                        
def shift_cloud_to_origin(current_date,current_file,current_folder,registration_folder,section,week,first_day,cc_path):
    #Generates a file containg in a 4 x 4 affine transformation matrix, translation is given by the first three rows in the last column
    #Translation vertically back to its original position using the median M3C2 value of the wooden pallet comparision of the date of the current file compared to the file on the first day of the week
    transformation_matrix_file = open(registration_folder + r"\translation.txt",'w')
    transformation_matrix_file.write("1 0 0 0\n")
    transformation_matrix_file.write("0 1 0 0\n")
    transformation_matrix_file.write("0 0 1 " + str(median_value(current_date,section,week,first_day,registration_folder)) + "\n")
    transformation_matrix_file.write("0 0 0 1\n")
    transformation_matrix_file.close()
    
    #List of all files in the current folder
    all_files = os.listdir(current_folder)
    
    #Translates cloud vertically
    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
    # -O current_file_path opens the file with path given by current_file_path
    # -APPLY_TRANS applies the transformation given by the file with path given by transformation_matrix_path
    subprocess.run([cc_path,"-SILENT","-O", current_folder + "\\" + current_file, "-APPLY_TRANS", registration_folder + r"\translation.txt"], shell=True)
    
    
    return diff(all_files,os.listdir(current_folder))[0]

def diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif

def z_shift(src,registration_folder,first_day,current_date,first_day_file,current_file,section,week,cc_path):
    #Registration error folder for median
    registration_errors = registration_folder + "\\Median"
    
    if not first_day == str(13 + (int(week) -1)*7):
        
        #Create the shifted origin file for the first day if it does not already exist
        if not os.path.exists(src + "\\" + first_day_file.replace(".bin","_Origin.bin")):
            first_day_origin = src + "\\" + shift_cloud_to_origin(first_day,first_day_file,src,registration_errors,section,week,str(13 + (int(week) -1)*7),cc_path)
            os.rename(first_day_origin,src + "\\" + first_day_file.replace(".bin","_Origin.bin"))
        
        #Create the shifted median file for the current file
        origin_shifted = shift_cloud_to_origin(current_date,current_file,src,registration_errors,section,week, str(13 + (int(week) -1)*7),cc_path)
        os.rename(src + "\\" + shift_cloud_to_median(current_date,origin_shifted,src,registration_errors,section,week,first_day,cc_path),src + "\\" + current_file.replace(".bin","_Median.bin"))
        os.remove(src + "\\" + origin_shifted)
    
    #If the first day is the first day of the week there is no need to shift all the files towards it because they have already been shifted when they were cropped
    else:
        #Create the shifted origin file for the first day if it does not already exist (in this case it will not move as the median value given will be zero)
        if not os.path.exists(src + "\\" + first_day_file.replace(".bin","_Origin.bin")):
            first_day_origin = src + "\\" + shift_cloud_to_origin(first_day,first_day_file,src,registration_errors,section,week,first_day,cc_path)
            os.rename(first_day_origin,src + "\\" + first_day_file.replace(".bin","_Origin.bin"))
        
        #Create the shifted median file for the current file
        os.rename(src + "\\" + shift_cloud_to_median(current_date,current_file,src,registration_errors,section,week,current_date,cc_path),src + "\\" + current_file.replace(".bin","_Median.bin"))


def registration_update(first_day,current_date,previous_date,m3c2_file,registration_folder,section,week):
    #Determines the value written next to "RegistrationError="in the M3C2 parameter file
    #In the first instance the value is always 0 and is always reset to 0 at the end
    if previous_date == "00":
        previous_registration_error = "0"
    else:
        with open(registration_folder + "\\" + first_day + previous_date + section + "Z.txt") as file :
            previous_registration_error = file.readline()
    if current_date == "99":
        current_registration_error = "0"
    else:
        with open(registration_folder + "\\" + first_day + current_date + section + "Z.txt") as file:
            current_registration_error = file.readline()
    
    #Replaces the old registration error with the new one
    replace(m3c2_file,"RegistrationError=" + previous_registration_error ,"RegistrationError=" + current_registration_error)

def determine_first_day(first_day_file,section,week):
    #Reads the text in the first_day_file
    with open(first_day_file) as first_days:
        first_day_list = first_days.readlines()
    
    #Determines the day that all others will be compared to from the date (and section) given in the first_day_file
    first_day = [x for x in first_day_list if section in x and determine_week(int(x[0:2])) in week]
    
    #If no first day is given, then the first day of the week is the default
    if len(first_day) == 0:
        return str(13 + (int(week) -1) *7)
    
    #Returns the date that all others will be compared to
    return first_day[0][0:2]
    
def determine_week(date):
    #Returns the week that the current date is in
    if date < 18:
        return "1"
    if date < 25:
        return "2"
    return "3"

def m3c2(overwrite,src,dest,m3c2_folder,registration_folder,first_day_txt_file):       
    #Path to the CloudCompare exe file
    cc_path =r"C:\Program Files\CloudCompare\CloudCompare.exe"
    
    #Create destination folder if it doesn't already exist
    os.makedirs(dest,exist_ok=True)
    
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        #M3C2 parameter file path 
        m3c2_parameters = m3c2_folder + "\\m3c2_params_" + section + "_" + week + ".txt"
        
        #Folder containing the registration error values 
        registration_error_files = registration_folder + "\\Median + MAD"
        
        print("Starting M3C2 comparisons")
        print("Registration error given by Median Absolute Deviation " )
        print("")
        
        #Set previous date to a trigger value for the registration update so it knows that the M3C2 parameter file registration error value has not yet been updated
        previous_date = "00"
    
        
    
    
        #List of files for the current section and week
        all_files = [x for x in os.listdir(src) if "Zone" + section in x and date_boundary(x,week)]
        
        #Works out the date of the file that all other files are being compared against for this section and week
        first_day = determine_first_day(first_day_txt_file,section,week)
        
        #Finds the filename of the of the file that all other files are being compared against for this section and week
        first_day_file = [x for x in all_files if "201808" + first_day in x ][0]
        
        #File path of the first day after it has been shifted back to its original position 
        first_day_shifted = src + "\\" + first_day_file.replace(".bin","_Origin.bin")
        
        #List of the remaining files to be compared to 
        compare_files = [x for x in all_files if x not in first_day_file]
        
        for filename in compare_files:
            #Finds the date of the current file
            current_date = filename[filename.find('201808') + 6:filename.find('201808') + 8]
            
            #File path of the current file after it has been shifted to the first_day_shifted file 
            compare_shifted = src + "\\" + filename.replace(".bin","_Median.bin")
            
            #Output file name
            compared_name = dest + "\\" + filename[0:filename.find("Zone") + 5] + "_M3C2_Projected_Onto_SFM_201808" + first_day + ".bin"
            
            #Checks if the output file exists
            path_check = os.path.exists(compared_name)
            if not path_check or overwrite:
                
                #Shifts the current file towards the first_day_file 
                z_shift(src,registration_folder,first_day,current_date,first_day_file,filename,section,week,cc_path)
                
                #Updates the registration error calculated via the median + MAD of the M3C2 comparison of the wooden pallets of the current file and first day file
                registration_update(first_day,current_date,previous_date, m3c2_parameters,registration_error_files,section,week)
                
                #Performs the M3C2 comparison
                # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                # -O cloud opens the file with path given by cloud
                # -M3C2 performs the M3C2 calculation on the on the two first loaded clouds. If a 3rd cloud is loaded, it will be used a core points.
                # Parameters are given by the txt file at m3c2_parameters
                subprocess.run([cc_path, "-SILENT", "-O", first_day_shifted, "-O", compare_shifted, "-M3C2", m3c2_parameters] ,shell = True)
                
                #Deletes old file if it exists and the overwrite option is on 
                if overwrite and path_check:
                    os.remove(compared_name)
                
                #Moves the M3C2 output file to the destination folder and renames is to the name given by compared_name
                os.rename(first_day_shifted.replace('.bin',"_M3C2.bin"),compared_name)
                
                #Deletes the median shifted current file
                os.remove(compare_shifted)
                
                #Changes the previous date so the registration error can be changed
                previous_date = current_date
                
            
            print("First day of section " + section + " week " + week + " compared with:")
            print(filename)
            print("")
        
        #If the first_day_shifted file has been created it is deleted    
        if os.path.exists(first_day_shifted):
            os.remove(first_day_shifted)
    
        #Returns the registration error file to the default value    
        registration_update(first_day,"99",previous_date,m3c2_parameters,registration_error_files,section,week)
        
