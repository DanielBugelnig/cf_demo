# cf_demo
Repository to demonstrate autonomous flying using the loco positioning system

## Setup Instructions
1. Clone the repository
```bash
git clone https://github.com/DanielBugelnig/cf_demo.git
```
2. Navigate to the project directory
3. Installing dependencies

- Ensure you have Python and pip installed on your machine. 
- Create a virtual environment
   ```bash
   python3 -m venv venv
- Activate the virtual environment
  ```bash
  source venv/bin/activate
- Install dependencies
   ```bash
   pip install -r requirements.txt

## Description of Files
### demo.py
Main script for demonstrating autonomous indoor flight:
- Connecting to the Crazyflie drone.
- Flying the drone along predefined trajectories.
- Logging flight data such as position and battery level.
- Handling emergency stops and landing events.

### cf_data.py
This script contains functions for handling Crazyflie data. It includes functionalities for:
- Reading and processing flight data.
- Storing and retrieving data for analysis.

### plot_test.py
This script is used for plotting the logged flight data. It generates visualizations for:
- Drone's flight path.
- Battery level over time.

### Running demo.py
```bash
python demo.py
```

### Running plot_test.py
```bash
python plot_test.py
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
```

Make sure to replace `<repository_url>` and `<repository_directory>` with the actual URL and directory name of your repository.



