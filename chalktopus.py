import pandas as pd
import matplotlib.pyplot as plt
import calplot
# Display the updated table
import streamlit as st

# Define grade weightings
weightings = {"v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12}

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
    return sum(row[f"{col}_completed"] * weightings[col] for col in weightings.keys())

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

# Plot calendar heatmap using calplot
fig, ax = calplot.calplot(data.set_index("Dates")["Daily_Score"], cmap="coolwarm", colorbar=True)
plt.show()
st.pyplot(fig)
# Plot line graph of daily scores
plt.figure(figsize=(12, 6))
plt.plot(data["Dates"], data["Daily_Score"], marker="o", linestyle="-")
plt.xlabel("Date")
plt.ylabel("Daily Score")
plt.title("Daily Climbing Scores Over Time")
plt.grid(True)
plt.xticks(rotation=45)
plt.show()