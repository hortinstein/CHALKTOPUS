import pandas as pd

# Load the data
data = pd.read_csv("Rock Climbing - central rock.csv")

# Helper function to parse a value
def parse_value(value):
    if pd.isna(value):
        return None, None
    if isinstance(value, str) and "tried" in value.lower():
        # Extract numbers after "tried"
        tried = [int(s) for s in value.split() if s.isdigit()]
        return None, tried[0] if tried else None
    try:
        # If the value is a number
        return int(value), None
    except ValueError:
        return None, None

# Add new columns for completed and tried counts
for col in ["vb", "v0", "v1", "v2", "v3", "v4"]:
    data[f"{col}_completed"] = None
    data[f"{col}_tried"] = None

# Process each row and column
for index, row in data.iterrows():
    for col in ["vb", "v0", "v1", "v2", "v3", "v4"]:
        value = row[col]
        completed, tried = parse_value(value)
        if completed is not None:
            data.loc[index, f"{col}_completed"] = completed
        if tried is not None:
            data.loc[index, f"{col}_tried"] = tried

# Display the updated table
import streamlit as st

st.title("Climbing Data: Completed vs Tried")

# Separate completed and tried data into tables
completed_columns = [col for col in data.columns if "_completed" in col]
tried_columns = [col for col in data.columns if "_tried" in col]

completed_table = data[["Location", "Dates"] + completed_columns]
tried_table = data[["Location", "Dates"] + tried_columns]

# Show tables in Streamlit
st.subheader("Completed Climbs")
st.dataframe(completed_table)

st.subheader("Tried Climbs")
st.dataframe(tried_table)
