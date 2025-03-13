# Flight Information Monitoring

This project is focused on monitoring and analyzing flight information, specifically for flights departing from New York City (NYC) in 2023. It uses a combination of Python scripts, SQLite database access, and data visualization techniques to provide insights into the flight data, including airport information, flight distances, delays, and other relevant metrics.

## Project Structure

This repository contains several Python scripts and a database file that interact to process and visualize flight data. The key components are:

1. **Database:**
   - `flights_database.db`: SQLite database that contains multiple tables, including `airports`, `flights`, `planes`, `weather`, and `airlines`.
   
2. **Python Scripts:**
   - `constants.py`: Contains global constants used across the project, such as airport codes and conversion factors.
   - `data_cleaning.py`: Functions for cleaning and preprocessing the flight data, including removing duplicates, handling missing values, and correcting time zones.
   - `distance_calculations.py`: Functions for calculating Euclidean and geodesic distances between airports.
   - `distance_comparison.py`: Compares distances from the database with geodesic distances and checks for discrepancies.
   - `helper_funcs.py`: Contains various utility functions for querying the database and performing data calculations.
   - `part1.py`: Functions for visualizing airport data, including maps of airports worldwide, within the U.S., and comparing distances.
   - `plots.py`: Various plotting functions for visualizing flight and airport data.
   - `dashboard.py`: Streamlit-based dashboard for visualizing and interacting with the flight data, including flight delays, weather impacts, and other metrics.
   - `flights_full.pdf`: A detailed description of the assignment requirements and project steps.

3. **Libraries:**
   - `pandas`: Used for data manipulation and analysis.
   - `sqlite3`: For interacting with the SQLite database.
   - `plotly`: For creating interactive plots and visualizations.
   - `timezonefinder`, `pytz`: For handling time zone corrections.
   - `numpy`: For mathematical calculations, especially distance and direction calculations.
   - `streamlit`: For creating the dashboard interface.

## Setup and Installation

To get started with this project, you will need to have Python installed on your machine. You will also need to install the following dependencies:

```
pip install pandas plotly numpy sqlite3 timezonefinder pytz
```


Clone the repository and make sure the following files are present:

- `flights_database.db`
- All Python scripts (`constants.py`, `data_cleaning.py`, etc.)
- `flights_full.pdf`

## Running the Project

### Step 1: Database Operations
The project requires access to the `flights_database.db` to perform various queries and operations. You can load the database and run queries via the Python scripts, such as:

- `data_cleaning.py`: Cleans and preprocesses the flight data (e.g., removes unused airports, adds missing airports).
- `distance_comparison.py`: Compares distances from the database to geodesic distances and reports discrepancies.
- `part1.py`: Performs data analysis and visualization, including plotting maps and computing distances.

### Step 2: Data Analysis and Visualization
Run the visualization functions in `part1.py` and `plots.py` to explore and visualize various aspects of the flight data:

- Generate maps of airports worldwide and in the U.S.
- Compare Euclidean and geodesic distances.
- Analyze flight time zones and visualize the distribution of airports across time zones.

### Step 3: Interactive Dashboard with Streamlit
To launch the Streamlit dashboard, run the following command:

```
streamlit run dashboard.py
```


This will start a local server and open the dashboard in your default web browser. The dashboard allows you to:

- Interactively explore flight delay data.
- Visualize statistics and insights from the flight database.
- Analyze weather impacts and other factors on flight delays.
- Use filters to view data by departure and arrival airports.

### Step 4: Additional Tasks and Features
- Perform advanced analysis on flight delays, weather impacts, and the effect of wind direction on flight times.
- Use `helper_funcs.py` to query specific data from the flights database and generate additional insights.

## Features

### 1. Visualizations:
   - **Map of Airports**: Plot all airports in the world, with a focus on airports in the U.S.
   - **Flight Paths**: Visualize flight paths between airports, specifically from New York City.
   - **Distance Analysis**: Compare Euclidean and geodesic distances between airports.
   - **Time Zone Analysis**: Plot and analyze the distribution of airports across different time zones.

### 2. Data Cleaning and Wrangling:
   - Remove unused airports.
   - Add missing airports from a predefined list.
   - Remove duplicate flights and handle missing values.

### 3. Database Queries:
   - Query the database for specific flight information, such as flight delays, departure times, and aircraft manufacturers.
   - Compute statistics, such as average delay times for each airline.

### 4. Data Analysis:
   - Investigate relationships between flight distances, arrival delays, and other variables.
   - Perform weather-related analysis and study the impact of wind on flight durations.

### 5. Interactive Dashboard:
   - **Flight Delay Analysis**: Display flight delay statistics and visualizations for various airports.
   - **Weather Impact**: Analyze the effects of weather on flight delays and air travel.
   - **Dynamic Filtering**: Filter data based on departure/arrival airports and dates.
   - **Visualize Key Metrics**: Show key metrics such as average delays, number of flights, and more.

## Contributing

Feel free to fork this repository and submit pull requests. Any contributions, whether it’s code, documentation, or bug fixes, are highly appreciated.

## License

This project is licensed under the MIT License.

---

### Additional Notes:
- Ensure that the SQLite database file (`flights_database.db`) is correctly set up and populated with the necessary data.
- Make sure all necessary Python packages are installed before running the scripts.


