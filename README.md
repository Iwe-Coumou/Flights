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
  This file contains all the functions from part 1, these work on the csv files that only contains part of the flights and airports.

- **plots.py**  
  Offers a collection of plotting functions for various visualizations such as:  
  - Interactive maps of flight routes.  
  - Distance versus arrival delay plots (scatter and histogram).  
  - Histograms and subplots for comparing distance distributions.  
  - Violin plots analyzing the impact of wind on air time.

- **dashboard.py**  
  A Streamlit-based interactive dashboard that ties together the data queries, visualizations, and flight statistics. The dashboard allows users to explore flight delays, weather impacts, and other key metrics through dynamic filters (by airport, date, etc.).

- **main.py**
  This file can be used to experiment with all the functions in this project. If you want to see the output of functions outside of the dashboard or use function that are not used in the dashboard you    can used them in this file.
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

There are two options for running this dashboard:

- Go to the [dashboard url](https://dashboard-flights.streamlit.app/) hosted on streamlit cloud
- Run the dashboard locally by following the steps below, this allows you to run the dashboard locally and experiment with the code and use
  function that are not on the hosted dashboard.

### Step 1: Dependencies

Make sure all the python libraries are installed using the command under **Installing the Dependencies**.

### Step 2: Launching the Dashboard

Make sure you are in the `scripts` folder and run the following command:

```
streamlit run dashboard.py
```
if it does not recognize streamlit try this command:

```
python -m streamlit run dashboard.py
```
This will launch a local server and open the dashboard in your default web browser, where you can interactively explore flight delays, weather impacts, and other metrics.

if it still doesn't work there might be something wrong with your `Streamlit` or `Python` installation

### Step 3: Using the dashboard

- When opening the dashboard you are on the main page with a preselected origin airport, this page shows a map with flights leaving that origin and some statistics.
  If you scroll down there will be more graphs and information
- In case you started the dashboard with a fresh database there is a button in the top left which cleans the database when pressed
- Now you have two options, choosing a destination airport or a date
  - If you decide to select a destination airport, you will enter route analysis mode, this will show a map with the specific route and some general statistics and graphs
    concerning this route. This also allows you to see and select specific flights and their statistics
  - If you decide to select a date, and not a destination, the dashboard will show the same statistics as when you open the dashboard but the data will be for that specific date

## Notes

There are some assumptioms or decissions made to keep the scope of this assignment aligned, they will be listed here:

- There are 1134 airports in the airports table that do not appear as a destination in the flights table. These airports were deleted
- Flighst with no recorded departure time are assumed to be cancelled flight, this applies to 10738 flights, these flights are not deleted but marked 1 if cancelled in a new column.
- Flights with no recorded arrival time were deleted. Theoretically we could try to approximate this using departure times but there were only 715 flights
  with no arrival time so we decided it was not worth the effort
- When converting the scheduled and actual departure and arrival times we needed to use some logic to decide if flights were overnight so we could increment the arrival day as needed.
  For this logic we needed to rely on the sign of the departure delay and arrival delay to check if a plane departed or arrivad early or the next day. Every non cancelled flight has a departure delay
  but 1081 of the flights had no arrival delay. Since we needed the arrival delay for our logic and there were relatively little flights without it we decided to remove these.
- Most of the datacleaning time was spent on the flights table since this was quiet a complicated process. Because of this, the weather table did not get our attention for cleaning and we decided it 
  was not necessary in the scope of this assignment to do this. This decission does mean that weather data will not always be available in the dashboard but if we wanted to clean the weather table it 
  we would have needed some extra time.
- We started with 435.352 flights and 1.251 airports, after this cleaning we had a remaining 433.544 flights and 121 airports

## Contributing

Contributions to this project are welcome. Feel free to fork the repository and submit pull requests. Contributions can include code improvements, bug fixes, or documentation enhancements.
