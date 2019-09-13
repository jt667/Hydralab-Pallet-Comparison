import os
import subprocess
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
from date_checker import date_boundary
from section_week import *
import csv

def shifted_cloud(current_file,current_file_path,median_error,registration_folder,cc_path):
    #Generates a file containg in a 4 x 4 affine transformation matrix, translation is given by the first three rows in the last column
    #Translation vertically given by the median M3C2 value of the wooden pallet comparision of the date of the current file compared to the file on the first day of the week
    transformation_matrix = registration_folder + r"\translation.txt"
    transformation_matrix_file = open(transformation_matrix,'w')
    transformation_matrix_file.write("1 0 0 0\n")
    transformation_matrix_file.write("0 1 0 0\n")
    transformation_matrix_file.write("0 0 1 " + str(-float(median_error)) + "\n")
    transformation_matrix_file.write("0 0 0 1\n")
    transformation_matrix_file.close()
    
    #Lists all the files in the current folder
    all_files = os.listdir(current_file_path.replace("\\" + current_file,""))
    
    #Translates cloud vertically
    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
    # -O current_file_path opens the file with path given by current_file_path
    # -APPLY_TRANS applies the transformation given by the file with path given by transformation_matrix_path
    subprocess.run([cc_path,"-SILENT","-O", current_file_path, "-APPLY_TRANS", transformation_matrix], shell=True)
    
    #Returns the name of the translated file
    return Diff(all_files,os.listdir(current_file_path.replace("\\" + current_file,"")))[0]
                        

def write_parameter(registration_error_parameter, parameter_file_path):
    #Write the registration_error_parameter to the text file parameter_file_path
    with open(parameter_file_path,'a')as parameter_file: 
        parameter_file.write(str(registration_error_parameter) + "\n")

def median_ad(cloud_path, observed_median):
    error_list = []
    with open(cloud_path) as csv_file:
        #Reads the lines in the csv file
        csv_reader = csv.reader(csv_file, delimiter = ';')
        for row in csv_reader:
            #Adds |observed_median - M3C2 value| to the list assuming the value exists
            if row[5] != "nan":
                error_list += [abs(observed_median - float(row[5]))]
    #Puts error_list in ascending order
    error_list.sort()
    
    #Returns the median value in error_list
    if len(error_list) % 2 == 0:
        return (error_list[int(len(error_list)/2)] + error_list[int(len(error_list)/2 - 1)])/2
    else:
        return error_list[int((len(error_list)-1)/2)]

def median(cloud_path):
    value_lst = []
    with open(cloud_path) as csv_file:
        #Reads the lines in the csv file
        csv_reader = csv.reader(csv_file, delimiter = ';')
        for row in csv_reader:
            #Adds the M3C2 value to the list assuming the value exists
            if row[5] != "nan":
                value_lst += [float(row[5])]
    #Puts value_lst in ascending order
    value_lst.sort()
    

    #Returns the median value in value_lst
    if len(value_lst) % 2 == 0:
        return (value_lst[int(len(value_lst)/2)] + value_lst[int(len(value_lst)/2 - 1)])/2
    else:
        return value_lst[int((len(value_lst)-1)/2)]

def median_z_shift(overwrite,dest_file,src_file):
    #Writes the median of the values given in the csv file to dest_file
    
    #Check if the output file already exists
    path_exists = os.path.exists(dest_file)
    
    if not path_exists or overwrite:
        file = open(dest_file,'w')
        file.close()
        write_parameter(median(src_file),dest_file)
        

def median_absolute_deviation_error(overwrite,dest_file,src_file):
    #Writes |median| + MAD to dest_file, both values calculated using the src_file
    if not os.path.exists(dest_file) or overwrite:
        file = open(dest_file,'w')
        file.close()
        file_median = median(src_file)
        write_parameter(abs(file_median) + median_ad(src_file,file_median),dest_file)
            
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

                        
def Diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif
    
def pallet_registration(overwrite,src,dest,m3c2Parameters,registration_folder):
    #Runtime: approx five minutes per week per section.
    #Output: median and median + MAD files for every comparision per week per section.
    
    print("Comparing pallets with M3C2")
    print("")
    #Path to the CloudCompare exe file
    cc_path =r"C:\Program Files\CloudCompare\CloudCompare.exe"

    #Creates the destination folder if it does not already exists
    if not os.path.exists(dest):
        os.makedirs(dest)
    
        print("M3C2 Parameters sourced from: ")
        print(m3c2Parameters)
        print("")
        
    dated_sections = determine_section_week(src)
    for pairs in dated_sections:
        section = pairs[0]
        week = pairs[1]
        
        #Creates the registration error folders if they do not already exist
        os.makedirs(registration_folder + "\\Median",exist_ok = True)
        os.makedirs(registration_folder + "\\Median + MAD",exist_ok=True)
        
        #Lists all the files in the src directory of the current week and section if they are not z shifted 
        allFiles = [x for x in os.listdir(src) if "Zone" + section in x and date_boundary(x,week)and "_Shift" not in x]
        
        #Compares all files in the same week and section with each other projecting on each cloud
        for i in range(len(allFiles)):
            
            #File path for the file that all other files will be compared to using M3C2
            firstDayPath = src + "\\" + allFiles[i]
            
            #Date of the first day
            first_day = allFiles[i][allFiles[i].find("201808") + 6: allFiles[i].find("201808") + 8]
            
            #List of the remianing files
            compareFiles = [allFiles[j] for j in range(len(allFiles)) if j != i]
           
            for filename in compareFiles:
                
                #Output file name for M3C2 comparison
                comparedName = dest + "\\" + filename[0:filename.find("Zone") + 5] + "_M3C2_Projected_Onto_201808" + first_day + ".bin"
                
                #Check if the M3C2 output file exists 
                path_exists = os.path.exists(comparedName)
                
                if not path_exists or overwrite:
                    #Path to the current file
                    comparePath = src + "\\"  + filename
                    
                    #Performs the M3C2 comparison
                    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                    # -O cloud opens the file with path given by cloud
                    # -M3C2 performs the M3C2 calculation on the on the two first loaded clouds. If a 3rd cloud is loaded, it will be used a core points.
                    # Parameters are given by the txt file at m3c2_parameters
                    subprocess.run([cc_path,"-SILENT","-O", firstDayPath, "-O", comparePath, "-M3C2", m3c2Parameters] ,shell = True)
                                      
                    #Deletes old output file if it exists and the overwrite option is on
                    if overwrite and path_exists:
                        os.remove(comparedName)
                    
                    #Moves the M3C2 file to the destination folder and renames it using the comparedName
                    os.rename(firstDayPath.replace('.bin',"_M3C2.bin"),comparedName)
                    
                #Checks if the csv file for the M3C2 output file exists
                path_exists = os.path.exists(comparedName.replace('.bin','.csv'))
                
                if not path_exists or overwrite:
                    #Deletes old output file if it already exists and the overwrite option is on
                    if overwrite and path_exists:
                        os.remove(comparedName.replace('.bin','.csv'))
                    
                    #Converts the bin file to a csv file
                    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                    # -O cloud opens the file with path given by cloud
                    # -NO_TIMESTAMP prevents the saved files having timestamps in their name
                    # -C_EXPORT_FMT  sets the default output format for clouds to the next given (in this case "ASC")
                    # -SEP specifies the seperator character as the next given (in this case "SEMICOLON")
                    # -EXT specifies the file extension as the next given (in this case "CSV")
                    # -SAVE_CLOUDS saves all the loaded clouds
                    subprocess.run([cc_path, "-SILENT","-O", comparedName, "-NO_TIMESTAMP", "-C_EXPORT_FMT", "ASC", "-SEP", "SEMICOLON", "-EXT", "CSV", "-SAVE_CLOUDS"], shell=True)
                
                #The date of the current file
                current_date = filename[filename.find("201808") + 6:filename.find("201808") + 6 +2]
                
                #Destination file name for the median of the M3C2 comparison between the current file and the first day file
                dest_file = registration_folder +  "\\Median\\" + first_day + current_date + section + ".txt"
                
                #Write the median M3C2 value to file
                median_z_shift(overwrite,dest_file,comparedName.replace('.bin','.csv'))
                
                #csv file for the M3C2 comparison of the current file and first day after the current file has been shifted towards the first day file
                comparedName = comparedName.replace(".bin","_Shift.csv")
                
                #Checks if the output file exists
                path_exists = os.path.exists(comparedName)
                if overwrite or not path_exists:
                    #Deletes the output file if it exists and the overwrite option is on
                    if overwrite and path_exists:
                        os.remove(comparedName)
                    
                    #Reads the median value of the unshifted M3C2 comparison
                    with open(dest_file) as median_file:
                        median = float(median_file.readlines()[0])
                    
                    #Shifts the current file towards the first day file using the median of the unshifted M3C2 comparison
                    shifted_file = src + "\\" + shifted_cloud(filename,src + "\\" + filename,median,registration_folder,cc_path)
                    
                    #Converts the bin file to a csv file
                    # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
                    # -NO_TIMESTAMP prevents the saved files having timestamps in their name
                    # -C_EXPORT_FMT  sets the default output format for clouds to the next given (in this case "ASC")
                    # -SEP specifies the seperator character as the next given (in this case "SEMICOLON")
                    # -EXT specifies the file extension as the next given (in this case "CSV")
                    # -O cloud opens the file with path given by cloud
                    # -M3C2 performs the M3C2 calculation on the on the two first loaded clouds. If a 3rd cloud is loaded, it will be used a core points.
                    # Parameters are given by the txt file at m3c2_parameters
                    subprocess.run([cc_path, "-SILENT","-NO_TIMESTAMP", "-C_EXPORT_FMT", "ASC", "-SEP", "SEMICOLON","-EXT", "CSV", "-O", firstDayPath,"-O", shifted_file, "-M3C2", m3c2Parameters], shell=True)
                    
                    #Check if the shifted file exists
                    path_exists = os.path.exists(src + "\\" + filename.replace(".bin","_Shift.bin"))
                    
                    #Deletes the old shifted bin file if it exists and the overwrite option is on
                    if path_exists and overwrite:
                        os.remove(src + "\\" + filename.replace(".bin","_Shift.bin"))
                        os.rename(shifted_file,src + "\\" + filename.replace(".bin","_Shift.bin"))
                    
                    #Deletes the new shifted bin file if the old one exists and the overwrite option is on
                    if path_exists and not overwrite:
                        os.remove(shifted_file)
                        
                    #Renames the new shifted file
                    if not path_exists:
                        os.rename(shifted_file,src + "\\" + filename.replace(".bin","_Shift.bin"))
                    
                    #Check if shifted M3C2 csv file exists
                    path_exists = os.path.exists(comparedName)
                    
                    #Deletes shifted M3C2 csv file if it exists and the overwrite option is on
                    if path_exists and overwrite:
                        os.remove(comparedName)
                    #Renames the M3C2 csv file 
                    os.rename(firstDayPath.replace(".bin", "_M3C2.csv"), comparedName)
                    
                #Output file name for |Median| + MAD
                dest_file = dest_file.replace(".txt", "Z.txt").replace("\\Median\\", "\\Median + MAD\\")
                
                #Calculate |Median| + MAD save to dest_file
                median_absolute_deviation_error(overwrite,dest_file,comparedName)
                
            print("Finished comparing with " + allFiles[i])
            
            






