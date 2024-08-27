import logging
import sys
import time
from threading import Event
import threading
import numpy as np
from datetime import date
from pynput import keyboard
import cf_data as cf_data

import matplotlib.pyplot as plt

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.positioning.position_hl_commander import PositionHlCommander

# Address of the Crazyflie
URI = ""


# Define Constants
DEFAULT_HEIGHT = 1 # in m
BATTERY_THRESHOLD_LOW = 2.8 # in V
LOGGING_RATE = 10 # in ms
LOCO_SETUP_FILE = ""

# Define Events
deck_attached_event = Event()
land_event = threading.Event()
flying_done_event = threading.Event()
emergency_stop_event = threading.Event()

# Define logging parameters
logging.basicConfig(level=logging.ERROR)
x_log = list()
y_log = list()
z_log = list()
timestamp_log = list()
batteryLevel_log = list()

# Define plotting dataset
plot_data = {
    'x': [],
    'y': [],
    'z': [],
    'colors': [],
    'labels': []   
}
    

# Fly created trajectories
def hl_motion_commander_fly_trajectory(scf,x,y,z, x_init,y_init):
    '''
    Fly the crazyflie along the trajectory

    Args:
    scf: SyncCrazyflie object
    x: x position data
    y: y position data
    z: z position data
    x_init: initial x position
    y_init: initial y position

    Returns:
    0: if the flight was successful
    1: if the flight was interrupted
    '''

    # Reset the estimation
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)
    
    # Fly the trajectory
    with PositionHlCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        if land_event.is_set():
            land_callback(scf)
            return 1

        time.sleep(1)
        mc.go_to(x_init,y_init, z)
        time.sleep(1)

        for i in range(len(x)):
            if land_event.is_set():
                land_callback(scf)
                return 1
            # Fly each point of the path
            mc.go_to(x[i], y[i])

        mc.go_to(x_init, y_init, z)
        time.sleep(1)
        # Landing
        for z in range(15,0,-1):
            scf.cf.commander.send_hover_setpoint(0, 0, 0, z / 15)
            time.sleep(0.1)
        return 0

def fly_eight(scf):
    '''
    Fly the crazyflie in a figure 8 trajectory
    
    Args:
    scf: SyncCrazyflie object
    
    Returns:
    0: if the flight was successful
    1: if the flight was interrupted
    '''

    # Reset the estimation
    
    scf.cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.cf.param.set_value('kalman.resetEstimation', '0')
    time.sleep(2)

    if land_event.is_set():
        scf.cf.commander.send_stop_setpoint()
        return 1


    for y in range(10):
        
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0, 0, 0, y / 25)
        time.sleep(0.1)
        if land_event.is_set():
            scf.cf.commander.send_stop_setpoint()
            return 1

    for _ in range(20):
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0, 0, 0, 0.4)
        time.sleep(0.1)
        if land_event.is_set():
            scf.cf.commander.send_stop_setpoint()
            return 1

    for _ in range(50):
        
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0.5, 0, 36 * 2, 0.4)
        time.sleep(0.1)
        if land_event.is_set():
            scf.cf.commander.send_stop_setpoint()
            return 1

    for _ in range(50):
       
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0.5, 0, -36 * 2, 0.4)
        time.sleep(0.1)
        if land_event.is_set():
            scf.cf.commander.send_stop_setpoint()
            return 1

    for _ in range(20):
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0, 0, 0, 0.4)
        time.sleep(0.1)

        if land_event.is_set():
                scf.cf.commander.send_stop_setpoint()
                return 1

    for y in range(10):
        if emergency_stop_event.is_set():
            print("Stopping motors")
            scf.cf.commander.send_stop_setpoint()
            return 1
        scf.cf.commander.send_hover_setpoint(0, 0, 0, (10 - y) / 25)
        time.sleep(0.1)
    print("Stopping motors")
    scf.cf.commander.send_stop_setpoint()
    # Hand control over to the high level commander to avoid timeout and locking of the Crazyflie
    scf.cf.commander.send_notify_setpoint_stop()
    return 0

# log callback
def log_pos_callback(timestamp, data, logconf):
    """
    logging the latest position, and battery data
    """
    global x_log
    global y_log
    global z_log
    global timestamp_log
    global batteryLevel_log


    x_log.append(data['stateEstimate.x'])
    y_log.append(data['stateEstimate.y'])
    z_log.append(data['stateEstimate.z'])
    timestamp_log.append(timestamp)
    batteryLevel_log.append(data['pm.vbat'])

# log default
def log_default():
    """
    reset the logging data
    """
    global x_log
    global y_log
    global z_log
    global timestamp_log
    global batteryLevel_log

    x_log = list()
    y_log = list()
    z_log = list()
    timestamp_log = list()
    batteryLevel_log = list()


# low battery callback and landing
def land_callback(scf):
    x,y = x_log[-1],y_log[-1]
    print(f"Landing at {x},{y}")
    for z in range(15,0,-1):
        scf.cf.commander.send_hover_setpoint(0, 0, 0, z / 15)
        time.sleep(0.1)
    flying_done_event.set()

         
   


# Thread: function to check battery level
def check_battery_level():
    while not (len(batteryLevel_log) > 0):
        pass
    while True:
        time.sleep(0.1)
        battery_level = batteryLevel_log[-1]
        if (battery_level <= BATTERY_THRESHOLD_LOW and battery_level >= 2):
            land_event.set()
            print(f"Low Battery threshold was undercut: {battery_level}")
            break
        if flying_done_event.is_set():
            break


# Thread: keyboard inputs
def keyboard_input():
    # Collect events until released
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    while not flying_done_event.is_set():
        time.sleep(0.1)
    listener.stop()
    #print("Listener closed")

# Thread: emergency stop
def motor_stop(scf):
    while not emergency_stop_event.is_set():
        if(flying_done_event.is_set()):
            break
        time.sleep(0.5)
    print("Stopping motors")
    flying_done_event.set()
    for i in range(10):
        scf.cf.commander.send_stop_setpoint()
        time.sleep(0.1)
    print("Motors stopped")
    # Hand control over to the high level commander to avoid timeout and locking of the Crazyflie
    scf.cf.commander.send_notify_setpoint_stop()


    

# Keyboard methods on press
def on_press(key):
    try:
        if key.char == 'q':
            time.sleep(0.2)
            # Move the cursor back and remove the last character
            sys.stdout.write('\b \b')
            sys.stdout.flush()
            print("Emergency Stop")
            emergency_stop_event.set()
        if key.char == 'l':
            time.sleep(0.2)
            sys.stdout.write('\b \b')
            sys.stdout.flush()
            print("Landing")
            land_event.set()
    except AttributeError:
        pass

# Keyboard methods on release
def on_release(key):
    pass


# check attached deck on cf
def param_deck_bcloco(_, value_str):
    '''

   checks, if loco deck is attached on the crazyflie
    '''

    value = int(value_str)
    #print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')
    

def strip_chars(s, chars_to_remove):
    """
    Remove specified characters from the beginning of the string.

    Args:
    s (str): The input string.
    chars_to_remove (str): The characters to remove from the beginning.

    Returns:
    str: The string with specified characters removed from the beginning.
    """
    # Strip characters from the beginning of the string
    while s and s[0] in chars_to_remove:
        s = s[1:]
    return s



if __name__ == '__main__':

    # Choosing the correct ID and anchor configuration
    cf_id = input("Enter the ID of the Crazyflie (1,2,3): ")
    if cf_id == '1':
        URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E701')
    elif cf_id == '2':
        URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E702')
    elif cf_id == '3':
        URI = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E703')
    else:
        print("Invalid input")
        sys.exit(1)
    
    #anchor config
    anchor_setup = input("Enter the anchor setup file: 4 anchors (1), 8 anchors (plane)(2), 8 anchors (space)(3), custom(4): ")
    if anchor_setup == '1':
        LOCO_SETUP_FILE = "../setup_files/anchor_positions_4a.yaml"
    elif anchor_setup == '2':
        LOCO_SETUP_FILE = "../setup_files/anchor_positions_8a_small.yaml"
    elif anchor_setup == '3':
        LOCO_SETUP_FILE = "../setup_files/anchor_positions_8a_tripod.yaml"
    elif anchor_setup == '4':
        LOCO_SETUP_FILE = "../setup_files/anchor_positions_custom.yaml"
    else:
        print("Invalid input")
        sys.exit(1)
    print("Remember to check and set the configuration of the anchors with the crazyflie-client aswell")
        

    # Create the battery monitoring thread, and the key listener thread
    battery_thread = threading.Thread(target=check_battery_level, args=())
    key_listener_thread = threading.Thread(target=keyboard_input, args=())
    
    


    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie()) as scf:   #'./cache'
        # Create the motor stop thread
        stop_thread = threading.Thread(target=motor_stop, args=(scf,))

        scf.cf.param.add_update_callback(group='deck', name='bcLoco', cb=param_deck_bcloco)
        time.sleep(0.2)

        # logging config
        logconf = LogConfig(name='Position', period_in_ms=LOGGING_RATE)
        logconf.add_variable('stateEstimate.x', 'float')
        logconf.add_variable('stateEstimate.y', 'float')
        logconf.add_variable('stateEstimate.z', 'float')
        logconf.add_variable('pm.vbat', 'float')
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)

        #check loco deck
        if not deck_attached_event.wait(timeout=5):
            print('No loco deck detected!')
            sys.exit(1)
        time.sleep(0.2)

        
        scf.cf.commander.send_hover_setpoint

        
        #waitung for user input
        print("Crazyflie demo")
        # demo_type for cgosing the flight type, 1 for flying waypoints, 2 for flying trajectory
        demo_type = int(input("Enter 1 for flying waypoints, 2 for flying trajectory: "))
        # set parameters
        trajectory_type = 1 # default value, choosing predefined trajectory
        num_waypoints = -1 # default value
        if (demo_type == 2):
            trajectory_type = int(input("Enter 1 for circle trajectory, 2 for square, or 3 for eight:"))
        elif(demo_type == 1):
            num_waypoints = int(input(f"Flying waypoints: How many waypoints do you want to fly? "))
        
        #plot anchors positions and trajectory
        anchor_pos = np.array(cf_data.obtain_anchor_positions(LOCO_SETUP_FILE))
        x_init = anchor_pos[1,0] /2
        y_init = anchor_pos[2,1] /2  
        cf_data.add_scatter_points(plot_data, anchor_pos[:,0], anchor_pos[:,1], color='red', label='Anchors')

        
        # add trajectory to plot data
        if (demo_type == 1):
            logconf.start()
            positions = cf_data.set_waypoints(num_waypoints,x_log,y_log,z_log)
            logconf.stop()
            log_default()
        elif (demo_type == 2):
            if (trajectory_type == 1):
                positions = cf_data.create_trajectory(3, x_init, y_init)
            if (trajectory_type == 2):
                #starting in middle and flying to the corners (endpoints 1.6,1.6)
                positions = np.array([[0.2,0.2],[x_init * 2 - 0.2, 0.2],[x_init * 2 - 0.2, y_init * 2 - 0.2],[0.2, y_init * 2 - 0.2], [x_init,y_init]])

        #cf_data.printing_trajectory(x,y, "X", "Y")
        
        if (demo_type == 1 or (demo_type == 2 and not trajectory_type == 3)):
             cf_data.add_scatter_points(plot_data, positions[:,0], positions[:,1], color='blue', label='Trajectory')
             plt.show(block=False)
        input("Place the crazyflie in direction of the positive x-axis. Enter to start: ")
    
        logconf.start()
        battery_thread.start()
        key_listener_thread.start()
        stop_thread.start()
        time.sleep(0.4)

        ## flying
        if (demo_type == 1 or (demo_type == 2 and not trajectory_type == 3)):
            hl_motion_commander_fly_trajectory(scf, positions[:,0],positions[:,1],1, x_init,y_init)
            #pass
        elif (demo_type == 2 and trajectory_type == 3):
            fly_eight(scf)
            #pass

        time.sleep(2)
        flying_done_event.set()
        battery_thread.join()
        key_listener_thread.join()
        stop_thread.join()
        logconf.stop()
        scf.cf.close_link()

    #Adding flight data to plot
    cf_data.add_scatter_points(plot_data, x_log, y_log, color='green', label='Flight')
    # Show plot
    plt.show(block=False)

    chars_to_strip = "ql"
    store = strip_chars(input("Do you want to save the logging data? (y/n/d(default file name)):").strip().lower(),chars_to_strip)
    
    # Format the date and time for the filename
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())

    # Save the logging data to a file
    file_name = "log_files/cf_logging_" + timestamp + ".txt"
    if (store == 'n'):
        print("Logging data not saved")
        print("Demo finished")
        sys.exit(0)
    elif (store == 'y'):
        file_name = input("Enter the file name to save the logging data(without extension): ")
        file_name = "log_files/" + file_name + "_" + timestamp + ".txt"

        
    with open(file_name, 'w') as file:
        file.write(f"Logging data from {sys.argv} at {timestamp}\n")
        file.write(f"Parameters: {demo_type}, {trajectory_type}, {num_waypoints}\n")
        file.write(f"Loco Setup file: {LOCO_SETUP_FILE}\n")
        file.write("Timestamp,X,Y,Z,Batterylevel\n")
        offset = timestamp_log[0]
        for i in range(len(x_log)):
            file.write(f"{timestamp_log[i]-offset}, {x_log[i]}, {y_log[i]}, {z_log[i]}, {batteryLevel_log[i]}\n")
    print(f"Logging data saved in {file_name}")
    print("Demo finished")
sys.exit(0)

        
        
        
        


