import subprocess
import os

def Diff(li1, li2): 
    #Returns the files that are not contained in both lists (the symmetric difference of the lists)
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif


def pcv(overwrite,src,dest):
    print("Shading files")
    print("")
    
    #Path to the CloudCompare exe file
    cc_path = r"C:\Program Files\CloudCompare\CloudCompare.exe"
    
    #List of all the files in the src directory
    all_files = os.listdir(src)
    
    #Create the destination folder if it does not already exist
    os.makedirs(dest,exist_ok=True)
    
    
    for filename in all_files:
        #Destination file name
        shaded_path = dest + "\\" + filename.replace(".bin","_Shaded.bin")
        
        #Check if the output file already exists
        if not os.path.exists(shaded_path) or overwrite:
            #Path to current file
            unshaded_path = src + "\\" + filename
            
            #Shades the cloud using light rays from above (useful for visualisation)
            # -SILENT stops a cloud compare console popping up (useful for debug as it will stop the program after completing its task)
            # -O current_file_path opens the file with path given by current_file_path
            # -PCV runs the PCV plugin on the loaded clouds
            # -180 rays only come from the northern hemisphere (+Z)
            subprocess.run([cc_path,  "-SILENT", "-O", unshaded_path, "-PCV", "-180"], shell = True)
            
            #The time stamped name of the shaded file
            time_stamped_file = Diff(all_files,os.listdir(src))[0]
            
            #Deletes the old output file if it exists
            if os.path.exists(shaded_path) and overwrite:
                os.remove(shaded_path)
            
            #Moves the file to a new folder and renames it to the original filename + "_Shaded" 
            os.rename(src + "\\" + time_stamped_file,shaded_path)

