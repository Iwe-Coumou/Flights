import pandas as pd

def convert_flight_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts scheduled and actual arrival/departure times to datetime format.
    
    Parameters:
        flights (pd.DataFrame): The DataFrame containing flight data.
        
    Returns:
        pd.DataFrame: The DataFrame with updated datetime columns.
    """
    datetime_columns = ['sched_dep_time', 'dep_time', 'sched_arr_time', 'arr_time']

    df[datetime_columns] = df[datetime_columns].apply(pd.to_datetime)

    return df

