import sys
import datetime as date
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yaml 
import random
from pathlib import Path
import re

# Import the logging data from the txt file
def import_logging_data(file):
    """
    Imports the logging data from the txt file

    Args:
    file: The file path of the txt file (csv format)
    Returns:
    time: The time data
    x: The x position data
    y: The y position data
    z: The z position data
    batterylevel: The battery level data
    """

    # Read the txt file with a two-row header
    df = pd.read_csv(file, skiprows= 3, delimiter= ',')

    # Access the columns and store them in variables
    time = df['Timestamp']
    x = df['X']
    y = df['Y']
    z = df['Z']
    batterylevel = df['Batterylevel']
    return time,x,y,z,batterylevel

def extract_metadata(file):
    """
    Extracts the metadata from the txt file

    Args:
    file: The file path of the txt file (csv format)

    Returns:
    metadata: The metadata information
    """
    data = list()
    # Read the txt file with a two-row header
    with open(file, 'r') as file:
        for i in range(3):
            data.append(file.readline())
            print(data[i])

        # Access command and date from the metadata
        # Logging data from ['demo.py'] at 2024-08-13_10-50-58
        # Regular expressions to capture command and date
        command_pattern = r"from \[(.*?)\]"
        date_pattern = r"at (.+)"

        # Access parameters
        # Parameters: 1, 3, 2
        param = data[1].split(":")[1].split(",")
        param = [int(i) for i in param]

        #loco setup file
        loco_file = data[2].split(':')[1].strip()

        # Search for the patterns in the metadata
        command_match = re.search(command_pattern, data[0])
        command = command_match.group(1) if command_match else None
        date_match = re.search(date_pattern, data[0])
        date = date_match.group(1) if date_match else None
    
    return command, date,param, loco_file

# List all files and directories in a given directory
def list_files_in_directory(directory):
    """
    List all files and directories in the given directory.

    Args:
    directory (str): The path to the directory.

    Returns:
    list: A list of names of files and directories in the specified directory.
    """
    path = Path(directory)
    
    if not path.exists():
        print(f"The directory '{directory}' does not exist.")
        return []
    if not path.is_dir():
        print(f"The path '{directory}' is not a directory.")
        return []

    # List all entries in the directory
    entries = [entry.name for entry in path.iterdir()]
    return entries

# Obtain the anchor positions from the YAML file
def obtain_anchor_positions(file):
    """
    Obtains the anchor positions from the YAML file

    Args:
    file: The file path of the YAML file

    Returns:
    x_values: The x position data
    y_values: The y position data
    z_values: The z position data
    """

    # Initialize lists to store x, y, and z values
    values = []


    # Load the YAML file
    with open(file, 'r') as file:
        data = yaml.safe_load(file)
        
        # Iterate through each item in the YAML data
        for item in data.values():
            values.append([round(item['x'],4), round(item['y'],4), round(item['z'],4)])
            
          
    return np.array(values)

# collect user-defined waypoints
def set_waypoints(count, x_log, y_log, z_log):
    """
    Asks the user to press enter to capture positions at each waypoint and stores them in an array.

    Args:
    count (int): Number of waypoints to capture.

    Returns:
    Array of captured waypoints with columns representing x, y, and z coordinates.
    """
    if count <= 0:
        raise ValueError("Count must be a positive integer")

    positions = np.zeros((count, 3))
    for i in range(count):
        input(f"Click enter for set position {i} ...\n")

        positions[i, 0] = sum(x_log[-10:])/10
        positions[i, 1] = sum(y_log[-10:])/10
        positions[i, 2] = sum(z_log[-10:])/10
        print(f"Position {i}: x={positions[i, 0]}, y={positions[i, 1]}, z={positions[i, 2]}\n")

    return positions

# Create trajectories to fly (circles)
def create_trajectory(param, x_init, y_init):
    """
    Creates a trajectory for the crazyflie to fly

    Args:
    param: The parameter to choose the trajectory, 
        1: Circle trajectory, for big environment
        2: Elipse trajectory, for big environment
        3: Circle trajectory, for small environment

    Returns:
    x: The x position data
    y: The y position data
    t: The time data
    """
    start = 0
    stop = 2 * np.pi
    step = 0.2
    pos = list()

    if param == 1:  # Circle trajectory, for big environment
        t = np.arange(start, stop + step, step)
        # print(vector) 
        x = np.cos(t) / 1.6 + x_init
        y = np.sin(t) / 1.6 + y_init

    elif param == 2: # Elipse trajectory, for big environment
        t = np.arange(start, stop + step, step)
        # print(vector) 
        x = 2*(np.cos(t) / 1.6) + x_init
        y = np.sin(t) / 1.6 + y_init
    elif param == 3: # Circle trajectory, for small environment
        t = np.arange(start, stop + step, step)
        # print(vector) 
        x = np.cos(t) * 0.8 + x_init
        y = np.sin(t) * 0.8 + y_init
    else:
        print("Invalid input")
        sys.exit(1)
    for i in range(len(x)):
        pos.append([x[i],y[i],t[i]])
    return np.array(pos)


# Printing trajectory which is planned to fly
def printing_trajectory(x,y, labelx, labely):
    """
    Plots the trajectory of the crazyflie

    Args:
    x: The x position data
    y: The y position data
    labelx: The x label
    labely: The y label

    Returns:
    The plot of the trajectory
    """

    plt.scatter(x, y)
    plt.xlabel(labelx)
    plt.ylabel(labely)
    plt.title('Trajectory of the Crazyflie')
    plt.grid()
    plt.show()


def add_scatter_points(plot_data,x, y, color=None, label=None):
    # List of predefined colors
    color_options = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']

    # If color is not provided, choose a random color from the list
    if color is None:
        color = random.choice(color_options)
    
    # If label is not provided, set a default label
    if label is None:
        label = f"Set {len(plot_data['x'])+1}"

    # Add new points and color to the plot data
    plot_data['x'].extend(x)
    plot_data['y'].extend(y)
    plot_data['colors'].extend([color] * len(x))
    plot_data['labels'].extend([label] * len(x))
    
    # Clear the current plot
    plt.clf()
    
    # Scatter plot with the stored data
    # Plot each set of points separately to assign them to the legend
    for i in range(len(plot_data['x'])):
        plt.scatter(plot_data['x'][i], plot_data['y'][i], c=plot_data['colors'][i], label=plot_data['labels'][i])

    # Optionally, set labels, title, and grid
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Trajectory of the crazyflie')
    plt.grid(True)

    # Only show one entry per label in the legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    
    
    # Show the plot
    #plt.show(block=False)





