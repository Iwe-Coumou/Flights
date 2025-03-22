# Flight Information Monitoring

This project is focused on monitoring and analyzing flight information, specifically for flights departing from New York City (NYC) in 2023. It uses Python scripts, a SQLite database, and interactive visualizations to provide insights into flight data—covering aspects such as airport information, flight distances, delays, weather impacts, and more.

## Project Structure

The repository contains the following files:

### Database File

- **flights_database.db**  
  The SQLite database containing multiple tables (e.g., `airports`, `flights`, `planes`, `weather`, and `airlines`) used for storing and querying flight data.

### Python Scripts

- **constants.py**  
  Contains global constants used across the project, such as the database path, NYC airport codes, missing airport definitions, and conversion factors.

- **data_cleaning.py**  
  Provides functions to clean and preprocess the flight data. This includes tasks such as removing duplicate flights, adding missing airports, correcting time zones, and handling missing values.

- **db_queries.py**  
  Houses various functions for querying the SQLite database. Examples include retrieving flight destinations, obtaining aircraft information, listing top carriers, and fetching available flight dates.

- **distance_calculations.py**  
  Contains functions for calculating distances between airports using two methods:  
  - **Euclidean distance:** A simplified 3D approximation.  
  - **Geodesic distance:** A more accurate calculation over the earth's surface.

- **distance_comparison.py**  
  Compares distances stored in the database (converted from miles to kilometers) with the computed geodesic distances from a CSV file, highlighting discrepancies that exceed a defined error margin.

- **flight_stats.py**  
  Includes functions to compute flight statistics such as average departure delays, total flight counts, number of delayed flights, and other aggregated metrics based on the flight data.

- **geo_utils.py**  
  Provides geospatial utility functions, including:  
  - Calculating flight direction (bearing) using vectorized operations.  
  - Computing inner products and wind impacts.  
  - Creating a mapping table of flight directions between airport pairs in the database.

- **part1.py**  
  Contains functions for exploratory visualizations. Examples include generating maps of all airports (worldwide and within the U.S.) and visualizing flight paths from a home base (defaulting to JFK).

- **plots.py**  
  Offers a collection of plotting functions for various visualizations such as:  
  - Interactive maps of flight routes.  
  - Distance versus arrival delay plots (scatter and histogram).  
  - Histograms and subplots for comparing distance distributions.  
  - Violin plots analyzing the impact of wind on air time.

- **dashboard.py**  
  A Streamlit-based interactive dashboard that ties together the data queries, visualizations, and flight statistics. The dashboard allows users to explore flight delays, weather impacts, and other key metrics through dynamic filters (by airport, date, etc.).

- **flights_full.pdf**  
  A detailed description of the assignment requirements and project steps, providing context and instructions for the project.

## Setup and Installation

### Requirements

The project depends on the following libraries:

- **pandas** – For data manipulation and analysis.
- **plotly** – For creating interactive plots and visualizations.
- **numpy** – For numerical and vectorized computations.
- **streamlit** – For building the interactive dashboard.
- **pytz** – For handling time zone operations.
- **timezonefinder** – For determining the time zone from latitude and longitude coordinates.

### Installing the Dependencies

Run this command in your terminal:

```
pip install -r requirements.txt
```

This command will install all the required libraries listed in the file.

## Running the Project

### Step 1: Database Operations

Before visualizing the data, ensure that the database (`flights_database.db`) is in place. Use the functions in **data_cleaning.py** (and optionally **db_queries.py**) to clean and preprocess the data.

### Step 2: Data Analysis and Visualization

- Use the functions in **distance_calculations.py** and **distance_comparison.py** to analyze distances between airports.
- Explore flight statistics with **flight_stats.py** and geospatial insights using **geo_utils.py**.
- Run the visualization functions in **part1.py** and **plots.py** to generate maps and other plots.

### Step 3: Launching the Interactive Dashboard

To start the Streamlit dashboard, run the following command:

```
streamlit run dashboard.py
```
or 

```
python -m streamlit run dashboard.py
```

This will launch a local server and open the dashboard in your default web browser, where you can interactively explore flight delays, weather impacts, and other metrics.

## Contributing

Contributions to this project are welcome. Feel free to fork the repository and submit pull requests. Contributions can include code improvements, bug fixes, or documentation enhancements.

## License

This project is licensed under the MIT License.


