import sys
import time
from matplotlib import pyplot as plt

import cf_data as cfd
import numpy as np
# script to plot logging data of crazyflie flights

# List all log_files in the directory
log_files = cfd.list_files_in_directory("log_files")
print(log_files)
log_file = input("Enter the log file to plot: ")

# Extracting meta data from the log file
command, date, param, loco_file= cfd.extract_metadata(f"log_files/{log_file}")

# Extracting data from the log file
t,x,y,z,batterylevel = cfd.import_logging_data(f"log_files/{log_file}")
t = [i/1000 for i in np.array(t)]

# Extracting loco_anchor_positions from the loco file
anchor_values = cfd.obtain_anchor_positions(loco_file) 

# compute flight trajectory
if param[0] == 2:
    pos_comp = cfd.create_trajectory(param[1])

# type of flight
if param[0] == 1:
    demo_type = "Waypoints"
elif param[0] == 2:
    demo_type = "Circle Trajectory"
elif param[0] == 3:
    demo_type = "8 Trajectory"


# Plotting the data
plot_data = {
    'x': list(),
    'y': list(),    
    'z': list(),
    'colors': [],
    'labels': []
}
plot = int(input("Flight (0), Battery (1), Height (2): "))
print(plot)
if (plot == 0):
    #plotting flight trajectory
    cfd.add_scatter_points(plot_data,anchor_values[:,0], anchor_values[:,1], color='red', label='Anchors')
    cfd.add_scatter_points(plot_data,x, y, color='green', label='Flight')
    if param[0] == 2:
        cfd.add_scatter_points(plot_data,pos_comp[:,0], pos_comp[:,1], color='black', label='Computed Trajectory')
    plt.xlabel('x [m]')
    plt.ylabel('x [m]')
    plt.title(f"Trajectory on {date}, executed command: {command}, {demo_type}")
    plt.grid(True)
    plt.show()

elif(plot == 1):
    print(f"Flight trajectory: {demo_type}")
    #plotting battery level
    plt.plot(np.array(t),np.array(batterylevel))
    plt.xlabel('Time [s]')
    plt.ylabel('Battery Level [V]')
    plt.title(f"Battery Level on {date}, executed command: {command}, {demo_type}")
    plt.grid(True)
    plt.show()
elif (plot ==2):
    print(f"Flight trajectory: {demo_type}")
    #plotting battery level
    plt.plot(np.array(t),np.array(z))
    plt.xlabel('Time [s]')
    plt.ylabel('Height [m]')
    plt.title(f"Height on {date}, executed command: {command}, {demo_type}")
    plt.grid(True)
    plt.show()


