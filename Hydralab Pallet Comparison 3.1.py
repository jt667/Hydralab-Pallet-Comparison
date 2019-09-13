import os
import tkinter
from tkinter import ttk
import pallet_processing
import main_processing
import raster_processing
from shader import pcv
import statistics_processing

def replace_directory(str1,directory):
    #Changes the folder given by replacing everything after the last backslash
    last_backslash = str1.rfind('\\')
    current_directory = str1[last_backslash:len(str1)]
    return str1.replace(current_directory,directory)

version = "3.1"

#Create output folder if it doesn't already exist
os.makedirs(os.getcwd()  + r"\Comparison Output",exist_ok=True)

#Default folders for the source and destination for each of the programs
#If you want to change the names of folders you need to change these values and the values in the corresponding program path function

ply_to_bin_default_src = os.getcwd()  + r"\Comparison Output\PLY to BIN"
ply_to_bin_default_dest = replace_directory(ply_to_bin_default_src,"")


crop_default_src = ply_to_bin_default_dest + r"\BIN Files"
crop_default_dest = replace_directory(crop_default_src,"\\Cropped Clouds")
crop_pallet_default_dest = replace_directory(crop_default_src,"\\Cropped Clouds Pallets")

m3c2_default_src = crop_default_dest
m3c2_default_dest = replace_directory(m3c2_default_src, "\\M3C2")

m3c2_pallet_default_src = crop_pallet_default_dest
m3c2_pallet_default_dest = replace_directory(m3c2_pallet_default_src,"\\M3C2 Pallets")

pallet_default_src = os.getcwd()  + r"\Comparison Output\Pallet Boundaries"
pallet_default_dest = replace_directory(pallet_default_src,"\\M3C2 Registration")

raster_default_src = m3c2_default_dest
raster_default_dest = replace_directory(raster_default_src,"\\Rasterized Clouds")

contour_default_src = raster_default_dest
contour_default_dest = replace_directory(raster_default_src,"\\Contour Shapefiles")

volume_default_src = contour_default_dest
volume_default_dest = replace_directory(volume_default_src,"\\Volume Estimates")


shader_default_src = crop_default_src
shader_default_dest = replace_directory(shader_default_src,"\\PCV Shaded")

parameter_folder = os.getcwd() + r"\parameter_files"

registration_error_default_src = parameter_folder + r"\registration_error"

m3c2_parameter_default_path = parameter_folder + r"\m3c2"
m3c2_pallet_parameter_default_path = parameter_folder + r"\m3c2\m3c2_params_pallets.txt"
first_day_file = m3c2_parameter_default_path + r"\first_day.txt"

plant_points_default_src = parameter_folder + r"\plant_points"

grid_steps_rgb_default = "0.001"
grid_steps_z_default = "0.001"


def main_processing_run():
    #Assign values for registration path, parameter path and first day path
    #If the values have been changed using options, this will reassign the names
    if registration_file_var.get():
        registration_path = registration_folder.get()
    else:
        registration_path = registration_error_default_src
    if m3c2_parameter_file_var.get():
        parameter_path = m3c2_parameter_path.get()
    else:
        parameter_path = m3c2_parameter_default_path
    first_day_path = first_day_file
    
    #Run the ply to bin conversion if option is ticked
    if ply_to_bin_var.get():
        src,dest = ply_to_bin_paths(src_file_var.get(),dest_file_var.get())
        main_processing.ply_to_bin(replace_file_var.get(),src,dest,registration_path)
    #Run the crop clouds if option is ticked
    if crop_clouds_var.get():
        src,dest = crop_paths(src_file_var.get(),dest_file_var.get())
        main_processing.crop(replace_file_var.get(),src,dest)
    #Run the M3C3 comparsion if option is ticked
    if m3c2_var.get():
        src,dest = m3c2_paths(src_file_var.get(),dest_file_var.get())   
        main_processing.m3c2(replace_file_var.get(),src,dest,parameter_path,registration_path,first_day_path)
    
    
def contour_processing_run():
    #Get source and destination values if either the RGB or Z raster program is running
    if raster_rgb_var.get() or raster_z_var.get():
        src,dest = raster_paths(src_file_var.get(),dest_file_var.get())
    
    #Run the raster RGB if the option is ticked
    if raster_rgb_var.get():
        if grid_steps_check_var_rgb.get():
            raster_processing.rasterize(replace_file_var.get(),src,dest,grid_steps_entry_rgb.get(),"RGB")
        else:
            raster_processing.rasterize(replace_file_var.get(),src,dest,grid_steps_rgb_default,"RGB")
    
    #Run the raster Z if the option is ticked
    if raster_z_var.get():
        if grid_steps_check_var_z.get():
            raster_processing.rasterize(replace_file_var.get(),src,dest,grid_steps_entry_z.get(),"Z")
        else:
            raster_processing.rasterize(replace_file_var.get(),src,dest,grid_steps_z_default,"Z")
    
    #Run the contour program if the option is ticked
    if contour_var.get():
        src, dest = contour_paths(src_file_var.get(),dest_file_var.get())
        os.makedirs(dest,exist_ok=True)
        raster_processing.generateContours(replace_file_var.get(),src,dest)
               
def statistics_processing_run():
    #Run the volume program if the option is ticked
    if volume_var.get():
        src,dest = volume_paths(src_file_var.get(),dest_file_var.get())
        statistics_processing.volume_calculation(replace_file_var.get(),src,dest,plant_points_default_src)
            

def pallet_processing_run():
    #Get M3C2 parameter path and registration file path
    #If the values have been changed by options this will reassign them
    if m3c2_parameter_file_var.get():
        parameter_path = m3c2_parameter_path.get()
    else:
        parameter_path = m3c2_pallet_parameter_default_path 
    if registration_file_var.get():
        registration_path = registration_folder.get()
    else:
        registration_path = registration_error_default_src 
    
    #Run the M3C2 pallet comparison if the option is ticked
    if m3c2_pallet_registration_var.get():
        src, dest = pallet_paths(src_file_var.get(),dest_file_var.get())
        pallet_processing.pallet_registration(replace_file_var.get(),src,dest,parameter_path,registration_path)

def shader_run():
    #Run the shader if the option is ticked
    if shader_py_var.get():
        src,dest = shader_paths(src_file_var.get(),dest_file_var.get())
        pcv(replace_file_var.get(),src,dest)

def run_in_sequence():
    pallet_processing_run()
    main_processing_run()
    contour_processing_run()
    statistics_processing_run()
    shader_run()
    
def ply_to_bin_paths(src_bool,dest_bool):
    
    #Work out the first program and last program running on the main processing tab
    first_program, last_program = program_bounds()
    #Returns the source and destination folders for the program ply to bin 
    if dest_bool:
        if src_bool:
            if last_program == 0:
                return src_folder.get(), dest_folder.get()
            else:
                return src_folder.get(), replace_directory(src_folder.get(),"")
        else:
            if last_program == 0:
                return ply_to_bin_default_src, dest_folder.get()
            else:
                return ply_to_bin_default_src, ply_to_bin_default_dest
    if src_bool:
        return src_folder.get(), replace_directory(src_folder.get(), "")

   
    return ply_to_bin_default_src, ply_to_bin_default_dest
        

def crop_paths(src_bool,dest_bool):
    #Work out the first program and last program running on the main processing tab
    first_program, last_program = program_bounds()
    
    #Returns the source and destination folders for the program cropped clouds
    if src_bool:
        if dest_bool:
            if first_program == 1:
                if last_program == 1:
                    return src_folder.get(), dest_folder.get()
                else:
                    return src_folder.get(), replace_directory(src_folder.get(), "\\Cropped Clouds")
            else:
                if last_program == 1:
                    return replace_directory(src_folder.get(),"\\BIN Files"), dest_folder.get()
                else:
                    return replace_directory(src_folder.get(),"\\BIN Files"), replace_directory(src_folder.get(),"\\Cropped Clouds")
        else:
            if first_program == 1:
                return src_folder.get(), replace_directory(src_folder.get(), "\\Cropped Clouds")
            else:
                return replace_directory(src_folder.get(),"\\BIN Files"), replace_directory(src_folder.get(),"\\Cropped Clouds")
    if dest_bool:
        return crop_default_src, dest_folder.get()

    return crop_default_src, crop_default_dest


def m3c2_paths(src_bool, dest_bool):
    #Work out the first program and last program running on the main processing tab
    first_program, last_program = program_bounds()
    
    #Returns the source and destination folders for the program M3C2 comparison
    if src_bool:
        if dest_bool:
            if first_program == 2:
                return src_folder.get(), dest_folder.get()
            else:
                return replace_directory(src_folder.get(), "\\Cropped Clouds"), dest_folder.get()
        else:
            if first_program == 2:
                return src_folder.get(), replace_directory(src_folder.get(),"\\M3C2")
            else:
                return replace_directory(src_folder.get(),"\\Cropped Clouds"), replace_directory(src_folder.get(),"\\M3C2")
    if dest_bool:
        return m3c2_default_src, dest_folder.get()

    return m3c2_default_src, m3c2_default_dest

def raster_paths(src_bool,dest_bool):
    #Returns the source and destination folders for the program raster RGB and raster Z
    if dest_bool:
        if src_bool:
            if contour_var.get():
                return src_folder.get(), replace_directory(src_folder.get(),"\\Rasterized Clouds")
            else:
                return src_folder.get(), dest_folder.get()
        else:
            if contour_var.get():
                return raster_default_src, raster_default_dest
            else:
                return raster_default_src, dest_folder.get()
    if src_bool:
        return src_folder.get(), replace_directory(src_folder.get(),"\\Rasterized Clouds")
    return raster_default_src, raster_default_dest

def contour_paths(src_bool, dest_bool):
    #Returns the source and destination folders for the program contours
    if src_bool:
        if dest_bool:
            if raster_rgb_var.get() or raster_z_var.get():
                return replace_directory(src_folder.get(), "\\Rasterized Clouds"), dest_folder.get()
            else:
                return src_folder.get(), dest_folder.get()
        else:
            if raster_rgb_var.get() or raster_z_var.get():
                return replace_directory(src_folder.get(), "\\Rasterized Clouds"), replace_directory(src_folder.get(),"\\Contour Shapefiles")
            else:
                return src_folder.get(), replace_directory(src_folder.get(),"\\Contour Shapefiles")
    if dest_bool:
        return contour_default_src, dest_folder.get()
    return contour_default_src, contour_default_dest

def volume_paths(src_bool,dest_bool):
    #Returns the source and destination folders for the program volumes
    if dest_bool:
        if src_bool:
            return src_folder.get(), dest_folder.get()
        else:
            return volume_default_src, dest_folder.get()
    if src_bool:
        return src_folder.get(), replace_directory(src_folder.get(),"\\Estimated Volumes")
    return volume_default_src, volume_default_dest



def pallet_paths(src_bool,dest_bool):
    #Returns the source and destination folders for the program M3C2 pallet registration
    if src_bool and dest_bool:
        return src_folder.get(), dest_folder.get()
    if src_bool:
        return src_folder.get(), replace_directory(src_folder.get(),"\\M3C2 Registration")
    if dest_bool:
        return pallet_default_src,dest_folder.get()
    return pallet_default_src,pallet_default_dest

def shader_paths(src_bool,dest_bool):
    #Returns the source and destination folders for the program shader
    if src_bool and dest_bool:
        return src_folder.get(), dest_folder.get()
    if src_bool:
        return src_folder.get(), replace_directory(src_folder.get(),"\\PCV Shaded")
    if dest_bool:
        return shader_default_src,dest_folder.get()
    return shader_default_src,shader_default_dest


#Commands to make the input fields readonly if the corresponding checkbox is left unticked 
def rgb_readonly():
    if grid_steps_check_var_rgb.get():
        grid_steps_entry_rgb.configure(state='normal')
    else:
        grid_steps_entry_rgb.configure(state='readonly')

def z_readonly():
    if grid_steps_check_var_z.get():
        grid_steps_entry_z.configure(state='normal')
    else:
        grid_steps_entry_z.configure(state='readonly')
        
def src_readonly():
    if not src_file_var.get():
        src_folder.configure(state='readonly')
    else:
        src_folder.configure(state='normal')
    
def dest_readonly():
    if not dest_file_var.get():
        dest_folder.configure(state='readonly')
    else:
        dest_folder.configure(state='normal')

def registration_readonly():
    if not registration_file_var.get():
        registration_folder.configure(state='readonly')
    else:
        registration_folder.configure(state='normal')

def m3c2_readonly():
    if not m3c2_parameter_file_var.get():
        m3c2_parameter_path.configure(state='readonly')
    else:
        m3c2_parameter_path.configure(state='normal')


#Forces the main processing to run in sequence i.e. you can't run the first and last program without running the middle one
def sequential_run():
    binary_check = str(int(ply_to_bin_var.get())) + str(int(crop_clouds_var.get())) + str(int(m3c2_var.get()))
    if binary_check == "001":
        ply_to_bin.configure(state='disabled')
    else:
        ply_to_bin.configure(state='normal')
    if binary_check == "111":
        crop_clouds.configure(state='disabled')
    else:
        crop_clouds.configure(state='normal')
    if binary_check == "100":
        m3c2.configure(state='disabled')
    else:
        m3c2.configure(state='normal')
     
    

def program_bounds():
    binary_check = str(int(ply_to_bin_var.get())) + str(int(crop_clouds_var.get())) + str(int(m3c2_var.get()))
    first = binary_check.find("1")
    last = binary_check.rfind("1")
    return first, last


def first_day():
    #Opens the first day text file
    os.startfile(first_day_file)

#Defines the main window    
root = tkinter.Tk()
#Window title
root.title('Hydralab Pallet Comparison ' + version)
#Window size
root.geometry('700x400')

#Opens a notebook - the tabbing system
nb = ttk.Notebook(root,padding=(0,12))
nb.pack(expand = True, fill='both')

##Defining Main Processing Page
##
f1 = tkinter.Frame(nb)
nb.add(f1, text="Main Processing")
nb.select(f1)
nb.enable_traversal()

main_program_window = tkinter.PanedWindow(f1)
main_program_window.grid(column=0, row =0,columnspan=2 ,padx=50)


#Boolean variable set ups
ply_to_bin_var = tkinter.BooleanVar()
crop_clouds_var = tkinter.BooleanVar()
m3c2_var = tkinter.BooleanVar()


#Checked boxes creation
ply_to_bin = ttk.Checkbutton(main_program_window, text=".ply to .bin", variable=ply_to_bin_var, onvalue=True,command=sequential_run)
crop_clouds = ttk.Checkbutton(main_program_window, text="Crop Clouds", variable=crop_clouds_var, onvalue=True,command=sequential_run)
m3c2 = ttk.Checkbutton(main_program_window, text="M3C2 Comparison", variable=m3c2_var, onvalue=True,command=sequential_run)

#Grid placement
ply_to_bin.grid(column=0, row=0, sticky = 'w')
crop_clouds.grid(column=0, row=1, sticky = 'w')
m3c2.grid(column=0, row=2, sticky = 'w')

#Run button creation
run_f1 = ttk.Button(main_program_window, text="Run",command=main_processing_run)
run_f1.grid(column=0, row=3, sticky = 'se')

first_day = ttk.Button(main_program_window, text="Change M3C2 first days?",command = first_day)
first_day.grid(column = 1, row = 2, padx = 20)

##Defining Rasterization Processing Page
##
f2 = tkinter.Frame(nb)
nb.add(f2, text="Contour Plots")
contour_processing = tkinter.PanedWindow(f2)
contour_processing.grid(column = 0, row = 0, padx =50)

raster_window = tkinter.PanedWindow(contour_processing)
raster_window.grid(column = 0, row = 0)
contour_program_window = tkinter.PanedWindow(contour_processing)
contour_program_window.grid(column=0, row=1, pady=50)

raster_label = tkinter.Label(raster_window,text = "Contour Plotting")
raster_label.grid(column = 0, row = 0)
contour_label = tkinter.Label(contour_program_window)
contour_label.grid(column=0,row=4)

raster_rgb_var = tkinter.BooleanVar()
raster_z_var = tkinter.BooleanVar()
contour_var = tkinter.BooleanVar()

raster_rgb = ttk.Checkbutton(raster_window, text="Raster RGB", variable = raster_rgb_var)
raster_z = ttk.Checkbutton(raster_window, text="Raster Z Projection", variable = raster_z_var)
contour = ttk.Checkbutton(raster_window, text="Contour plotting", variable = contour_var)

raster_rgb.grid(column  = 0, row = 1, sticky='w')
raster_z.grid(column = 0, row = 2, sticky='w')
contour.grid(column = 0, row = 3, sticky = 'w')


grid_steps_check_var_rgb = tkinter.BooleanVar()
grid_steps_check_var_z = tkinter.BooleanVar()

grid_steps_check_rgb = ttk.Checkbutton(raster_window, text = "RGB grid steps size: ", variable = grid_steps_check_var_rgb, command=rgb_readonly)
grid_steps_check_z = ttk.Checkbutton(raster_window, text = "Z projection grid steps size: ", variable = grid_steps_check_var_z, command=z_readonly)

grid_steps_entry_rgb = tkinter.Entry(raster_window,state='readonly', readonlybackground='light gray')
grid_steps_entry_z = tkinter.Entry(raster_window,state='readonly', readonlybackground='light gray')


grid_steps_check_rgb.grid(column = 1, row = 1, sticky='w', padx = 100)
grid_steps_entry_rgb.grid(column = 1, row = 2, padx = 100)
grid_steps_check_z.grid(column = 1, row = 3, sticky='w', padx = 100)
grid_steps_entry_z.grid(column = 1, row = 4, padx = 100)


run_f2 = ttk.Button(contour_processing, text = "Run",command=contour_processing_run)

run_f2.grid(column = 3,row =3)

f3 = tkinter.Frame(nb)
nb.add(f3, text="Statistics")
statistics_window = tkinter.PanedWindow(f3)
statistics_window.grid(column=0, row=0)

volume_var = tkinter.BooleanVar()


volume = ttk.Checkbutton(statistics_window,text="Volume Calculations", variable=volume_var)


volume.grid(column=0,row=0,sticky='w')


run_f3 = ttk.Button(statistics_window, text="Run",command=statistics_processing_run)
run_f3.grid(column=1,row=2)

f4 = tkinter.Frame(nb)
nb.add(f4, text="Pallet Processing")
pallet_process = tkinter.PanedWindow(f4)
pallet_process.grid(column=0, row=0)
pallet_window = tkinter.PanedWindow(pallet_process)

m3c2_pallet_registration_var= tkinter.BooleanVar()


m3c2_pallet_registration = ttk.Checkbutton(pallet_window, text="M3C2 Pallet Registration", variable=m3c2_pallet_registration_var)

run_f4 = ttk.Button(f4, text="Run", command=pallet_processing_run)

m3c2_pallet_registration.grid(column=0, row=0, sticky = 'w')
run_f4.grid(column=3, row=3, sticky = 'se')

pallet_window.grid(column = 0, row = 0, padx =20)

                    
f5 = tkinter.Frame(nb)
nb.add(f5, text="Shading")

shader_py_var = tkinter.BooleanVar()

shader_py = ttk.Checkbutton(f5,text="Shader",variable=shader_py_var)
run_f5 = ttk.Button(f5,text="Run",command=shader_run)

shader_py.grid(column=0,row=0)
run_f5.grid(column=1,row=1)

f6 = tkinter.Frame(nb)
nb.add(f6, text="Options")
opt = tkinter.PanedWindow(f6)
opt.grid(column = 0, row = 0)
opt_window = tkinter.PanedWindow(opt)


src_file_var = tkinter.BooleanVar()
dest_file_var = tkinter.BooleanVar()
registration_file_var = tkinter.BooleanVar()
m3c2_parameter_file_var = tkinter.BooleanVar()
replace_file_var = tkinter.BooleanVar()


src_file = ttk.Checkbutton(opt_window, text="Use different source folder for first program running?", variable=src_file_var, command=src_readonly)
dest_file = ttk.Checkbutton(opt_window, text="Use different destination folder for last program running?)", variable=dest_file_var, onvalue=True, command=dest_readonly)
registration_file = ttk.Checkbutton(opt_window,text="Use different folder path for registration error files?", variable=registration_file_var, command=registration_readonly)
m3c2_parameter_file = ttk.Checkbutton(opt_window,text="Use different M3C2 parameter file?", variable = m3c2_parameter_file_var, command=m3c2_readonly)
replace_file = ttk.Checkbutton(opt_window, text="Replace files if they already exist?", variable=replace_file_var)



src_folder = tkinter.Entry(opt_window, width = 50,state='readonly', readonlybackground='light gray')
dest_folder = tkinter.Entry(opt_window, width = 50,state='readonly', readonlybackground='light gray')
registration_folder = tkinter.Entry(opt_window, width = 50, state='readonly',readonlybackground='light gray')
m3c2_parameter_path = tkinter.Entry(opt_window, width = 50, state='readonly',readonlybackground='light gray')


src_file.grid(column=0, row=0, sticky = 'w')
dest_file.grid(column=0, row=2, sticky = 'w')
registration_file.grid(column=0,row=4, sticky='w')
m3c2_parameter_file.grid(column=0,row=6,sticky='w')
replace_file.grid(column=0, row=8, sticky = 'w')


src_folder.grid(column=0, row=1)
dest_folder.grid(column=0, row=3)
registration_folder.grid(column=0, row=5)
m3c2_parameter_path.grid(column=0, row=7)


run_all = ttk.Button(opt_window, text="Run all",command=run_in_sequence)
run_all.grid(column =1, row=11)

opt_window.grid(column = 0, row = 0, padx=20)


#Start GUI
root.mainloop()
