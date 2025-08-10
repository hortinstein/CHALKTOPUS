import pandas as pd
import matplotlib.pyplot as plt
import calplot
# Display the updated table
import streamlit as st
import math
import numpy as np

# Define different scoring methods
def get_scoring_methods():
    """Return dictionary of different scoring methods for climbing grades"""
    return {
        "Original Exponential": {"vb": 0.5, "v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12},
        "Extended Exponential": {"vb": 0.5, "v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12, "v5": 20, "v6": 32},
        "Fibonacci Progression": {"vb": 1, "v0": 1, "v1": 2, "v2": 3, "v3": 5, "v4": 8, "v5": 13, "v6": 21},
        "Power Scaling (x^1.5)": {
            "vb": round(0.5 ** 1.5, 1), 
            "v0": round(1 ** 1.5, 1), 
            "v1": round(2 ** 1.5, 1), 
            "v2": round(3 ** 1.5, 1), 
            "v3": round(4 ** 1.5, 1), 
            "v4": round(5 ** 1.5, 1),
            "v5": round(6 ** 1.5, 1),
            "v6": round(7 ** 1.5, 1)
        },
        "Climbing Difficulty Curve (1.5x)": {
            "vb": 1,
            "v0": 2,
            "v1": 3,
            "v2": 5,
            "v3": 7,
            "v4": 11,
            "v5": 16,
            "v6": 24
        }
    }

# Sidebar for scoring method selection
st.sidebar.title("Scoring Options")
scoring_methods = get_scoring_methods()
selected_method = st.sidebar.selectbox(
    "Choose Scoring Method:",
    options=list(scoring_methods.keys()),
    index=0,
    help="Select different scoring algorithms for climbing grade progression"
)

# Get the selected weightings
weightings = scoring_methods[selected_method]

# Display current scoring method info
st.sidebar.subheader("Current Scoring Values")
for grade, weight in weightings.items():
    st.sidebar.write(f"{grade.upper()}: {weight}")

# Display scoring method descriptions
scoring_descriptions = {
    "Original Exponential": "Classic exponential doubling pattern (1, 2, 4, 8, 12)",
    "Extended Exponential": "Continues exponential pattern to higher grades",
    "Fibonacci Progression": "Natural growth following Fibonacci sequence",
    "Power Scaling (x^1.5)": "Mathematical power scaling based on grade^1.5",
    "Climbing Difficulty Curve (1.5x)": "Reflects real climbing difficulty progression (~1.5x multiplier)"
}

st.sidebar.info(scoring_descriptions[selected_method])

# Load the data
data = pd.read_csv("20250212_rockclimbing.csv")

# Helper function to parse a value
def parse_value(value):
    if pd.isna(value):
        return 0, 0
    if isinstance(value, str) and "tried" in value.lower():
        # Extract numbers after "tried"
        tried = [int(s) for s in value.split() if s.isdigit()]
        return 0, tried[0] if tried else 0
    try:
        # If the value is a number
        return int(value), 0
    except ValueError:
        return 0, 0

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


st.title("Climbing Data: Completed vs Tried")
st.subheader(f"Current Scoring Method: {selected_method}")

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


# Calculate the daily score
def calculate_score(row):
    score = 0
    for col in weightings.keys():
        if f"{col}_completed" in row:
            completed = row[f"{col}_completed"]
            if pd.notna(completed):
                score += completed * weightings[col]
    return score

data["Daily_Score"] = data.apply(calculate_score, axis=1)

# Print daily scores
print(data[["Location", "Dates", "Daily_Score"]])

st.dataframe(data[["Location", "Dates", "Daily_Score"]])

# graph the daily scores
import matplotlib.pyplot as plt


# Convert 'Dates' to datetime format
data["Dates"] = pd.to_datetime(data["Dates"])

# Sort by date
data = data.sort_values("Dates")

# Plot calendar heatmap using calplot with improved error handling
try:
    # Prepare data for calendar plot with proper validation
    calendar_data = data.set_index("Dates")["Daily_Score"]
    
    # Remove any NaN or infinite values that might cause issues
    calendar_data = calendar_data.dropna()
    calendar_data = calendar_data[calendar_data.notna()]
    
    if len(calendar_data) == 0:
        st.warning("No valid data available for calendar heatmap.")
    else:
        fig, ax = calplot.calplot(calendar_data, cmap="coolwarm", colorbar=True)
        plt.show()
        st.pyplot(fig)
        
except AttributeError as e:
    if "pivot" in str(e).lower():
        st.error("Calendar heatmap error: Pandas compatibility issue detected.")
        st.info("This error may be due to incompatible versions of pandas and calplot. The pivot() method signature has changed in newer pandas versions.")
        st.info("**Solution:** Try upgrading calplot to version >= 0.1.7.5 or downgrading pandas to < 2.0 if needed.")
    else:
        st.error(f"Calendar heatmap error: {e}")
        
except ValueError as e:
    st.error(f"Calendar heatmap data error: {e}")
    st.info("This may be due to invalid date ranges or data values. Please check your data format.")
    
except Exception as e:
    st.error(f"Error creating calendar heatmap: {e}")
    st.info("The calendar heatmap could not be generated. This may be due to a version compatibility issue between pandas and calplot.")
    st.info("**Troubleshooting:**")
    st.info("1. Ensure you have calplot >= 0.1.7.5 installed")
    st.info("2. Check pandas version compatibility")
    st.info("3. Verify your data contains valid dates and numeric values")
# Plot line graph of daily scores
plt.figure(figsize=(12, 6))
plt.plot(data["Dates"], data["Daily_Score"], marker="o", linestyle="-")
plt.xlabel("Date")
plt.ylabel("Daily Score")
plt.title("Daily Climbing Scores Over Time")
plt.grid(True)
plt.xticks(rotation=45)
plt.show()