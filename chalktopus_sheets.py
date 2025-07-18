import pandas as pd
import matplotlib.pyplot as plt
import calplot
import streamlit as st
from streamlit_folium import st_folium
import folium
import json
import seaborn as sns

st.set_page_config('🧗‍♂️chalktopus🐙', initial_sidebar_state="collapsed")

# Define grade weightings
weightings = {"v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12}

# Function to load data from public Google Sheets
def load_data_from_public_sheets():
    st.sidebar.header("Google Sheets Connection")
    
    # Allow user to enter sheet URL or ID
    sheet_url = "https://docs.google.com/spreadsheets/d/15r0qE2WNQYk2CLqxnI7b5r9_OWyaOMFAtb_4t8_ylnA/edit?usp=sharing"

    # Extract sheet ID from URL if necessary
    if "spreadsheets/d/" in sheet_url:
        sheet_id = sheet_url.split("spreadsheets/d/")[1].split("/")[0]
    else:
        sheet_id = sheet_url
    
    # Construct the export URL (CSV format)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        # Read the CSV directly from the URL
        data = pd.read_csv(export_url)
        st.sidebar.success("Connected to Google Sheets successfully!")
        return data
    except Exception as e:
        st.sidebar.warning(f"Failed to connect to Google Sheets: {e}")
        st.sidebar.info("Using local CSV data instead...")
        # Fallback to local CSV file
        try:
            data = pd.read_csv("20250212_rockclimbing.csv")
            st.sidebar.success("Loaded local CSV data successfully!")
            return data
        except Exception as local_e:
            st.sidebar.error(f"Failed to load local data: {local_e}")
            return None
    
# Load the data
data = load_data_from_public_sheets()

if data is not None:
    # Helper function to parse a value
    def parse_value(value):
        if pd.isna(value):
            return 0, 0
        
        # If it's a string, check for the format pattern
        if isinstance(value, str):
            parts = value.split()
            
            # Format: "1 tried 3 other" or similar variations
            if len(parts) >= 3 and "tried" in parts:
                # Find position of "tried" in the parts
                tried_index = parts.index("tried")
                
                # Get completed count (number before "tried")
                completed = int(parts[tried_index-1]) if tried_index > 0 and parts[tried_index-1].isdigit() else 0
                
                # Get tried count (number after "tried")
                tried = int(parts[tried_index+1]) if tried_index+1 < len(parts) and parts[tried_index+1].isdigit() else 0
                
                return completed, tried
            
            # Just "tried X" format
            elif "tried" in parts:
                # Find all numbers in the string
                numbers = [int(s) for s in parts if s.isdigit()]
                if numbers:
                    return 0, numbers[0]
            
            # Try to parse as a plain number if it contains only digits
            elif value.isdigit():
                return int(value), 0
                
            return 0, 0
        
        # If it's a number
        try:
            return int(value), 0
        except (ValueError, TypeError):
            return 0, 0

    # Add new columns for completed and tried counts
    for col in ["vb", "v0", "v1", "v2", "v3", "v4"]:
        if col in data.columns:
            data[f"{col}_completed"] = None
            data[f"{col}_tried"] = None

    # Process each row and column
    for index, row in data.iterrows():
        for col in ["vb", "v0", "v1", "v2", "v3", "v4"]:
            if col in data.columns:
                value = row[col]
                completed, tried = parse_value(value)
                if completed is not None:
                    data.loc[index, f"{col}_completed"] = completed
                if tried is not None:
                    data.loc[index, f"{col}_tried"] = tried

    

    # Display the title
    st.title("🧗‍♂️chalktopus🐙")

    # Add sidebar controls for grade filtering
    st.sidebar.header("Display Options")
    
    # Toggle between score view and completed count view
    show_completed_counts = st.sidebar.checkbox("Show Completed Counts Instead of Scores", value=False)
    
    # Grade selector (only show when in completed count mode)
    selected_grade = None
    if show_completed_counts:
        grade_options = ["vb", "v0", "v1", "v2", "v3", "v4"]
        selected_grade = st.sidebar.selectbox("Select Grade to Display", grade_options, index=1)


    # Separate completed and tried data into tables
    completed_columns = [col for col in data.columns if "_completed" in col]
    tried_columns = [col for col in data.columns if "_tried" in col]

    completed_table = data[["Location", "Dates"] + completed_columns]
    tried_table = data[["Location", "Dates"] + tried_columns]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Graphs", "Data", "Smoothed Score Trend", "Macro Data", "Map", "Difficulty Graphs"])
    
    with tab2:
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
                    if pd.notna(row[f"{col}_completed"]):
                        score += row[f"{col}_completed"] * weightings[col]
            return score

        data["Daily_Score"] = data.apply(calculate_score, axis=1)

        # Create display value based on toggle
        if show_completed_counts and selected_grade:
            # Use completed count for selected grade
            grade_col = f"{selected_grade}_completed"
            if grade_col in data.columns:
                data["Display_Value"] = data[grade_col].fillna(0)
                display_title = f"Daily {selected_grade.upper()} Completed"
                display_ylabel = f"{selected_grade.upper()} Completed"
            else:
                data["Display_Value"] = data["Daily_Score"]
                display_title = "Daily Climbing Scores"
                display_ylabel = "Daily Score"
        else:
            # Use daily score
            data["Display_Value"] = data["Daily_Score"]
            display_title = "Daily Climbing Scores"
            display_ylabel = "Daily Score"

    # Convert 'Dates' to datetime format
    data["Dates"] = pd.to_datetime(data["Dates"], errors="coerce")

    # Sort by date
    data = data.sort_values("Dates")
    
    with tab1: 
        # Plot calendar heatmap using calplot
        try:
            st.subheader("Calendar Heatmap")
            fig, ax = calplot.calplot(data.set_index("Dates")["Display_Value"], cmap="coolwarm", colorbar=True)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error creating calendar plot: {e}")

        # Plot line graph of daily scores
        try:
            st.subheader(display_title + " Trend")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(data["Dates"], data["Display_Value"], marker="o", linestyle="-")
            ax.set_xlabel("Date")
            ax.set_ylabel(display_ylabel)
            ax.set_title(display_title + " Over Time")
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error creating line plot: {e}")
        

    
    with tab3:
        # Implement a smoothing function using a rolling average
        try:
            if show_completed_counts and selected_grade:
                smoothed_title = f"Smoothed {selected_grade.upper()} Completed Trend"
                smoothed_ylabel = f"Smoothed {selected_grade.upper()} Completed"
            else:
                smoothed_title = "Smoothed Score Trend"
                smoothed_ylabel = "Smoothed Score"
                
            st.subheader(smoothed_title)
            data["Smoothed_Value"] = data["Display_Value"].rolling(window=7, min_periods=1).mean()
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(data["Dates"], data["Smoothed_Value"], marker="o", linestyle="-")
            ax.set_xlabel("Date")
            ax.set_ylabel(smoothed_ylabel)
            ax.set_title(smoothed_title + " Over Time")
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error creating smoothed trend plot: {e}")
    
    with tab4:
        st.subheader("Macro Data")
        
        # Calculate total climbs for each grade
        total_climbs = data[completed_columns].sum()
        st.subheader("Total Climbs")
        st.dataframe(total_climbs)
        
        # Plot total climbs for each grade
        try:
            st.subheader("Total Climbs Graph")
            fig, ax = plt.subplots(figsize=(12, 6))
            total_climbs.plot(kind='bar', ax=ax)
            ax.set_xlabel("Grade")
            ax.set_ylabel("Total Climbs")
            ax.set_title("Total Climbs for Each Grade")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error creating total climbs graph: {e}")
        
        # Calculate average climbs per week for each grade
        # Use pd.Grouper to properly group by week, accounting for different years
        data_for_weekly_climbs = data.set_index('Dates')
        weekly_climbs = data_for_weekly_climbs.groupby(pd.Grouper(freq='W'))[completed_columns].sum()
        # Only include weeks with at least one climb
        weekly_climbs = weekly_climbs[weekly_climbs.sum(axis=1) > 0]
        average_climbs_per_week = weekly_climbs.mean()
        st.subheader("Average Climbs per Week")
        st.dataframe(average_climbs_per_week)
        
        # Plot average climbs per week for each grade
        try:
            st.subheader("Average Climbs per Week Graph")
            fig, ax = plt.subplots(figsize=(12, 6))
            average_climbs_per_week.plot(kind='bar', ax=ax)
            ax.set_xlabel("Grade")
            ax.set_ylabel("Average Climbs per Week")
            ax.set_title("Average Climbs per Week for Each Grade")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error creating average climbs per week graph: {e}")
        
        # Calculate total climbing sessions
        total_sessions = data['Dates'].nunique()
        st.subheader("Total Climbing Sessions")
        st.write(f"Total Climbing Sessions: {total_sessions}")
        
        # Monthly visits with zero values shown
        st.subheader("Monthly Visits")
        
        # Add checkbox to toggle between monthly totals and weekly averages
        show_weekly_average = st.checkbox("Show Average Times per Week (Divide by 4)")
        
        # Calculate the number of times you went per month
        # Use pd.Grouper to properly group by month, accounting for different years
        data_for_monthly = data.set_index('Dates')
        monthly_visits = data_for_monthly.groupby(pd.Grouper(freq='M')).size()
        
        # Create a complete date range to show months with zero visits
        if not monthly_visits.empty:
            # Get the date range from first visit to last visit
            min_date = data['Dates'].min()
            max_date = data['Dates'].max()
            
            # Create monthly date range
            complete_months = pd.date_range(start=min_date, end=max_date, freq='M')
            
            # Reindex to include all months, filling missing with 0
            monthly_visits = monthly_visits.reindex(complete_months, fill_value=0)
            
            # Apply weekly average calculation if checkbox is checked
            display_visits = monthly_visits.copy()
            if show_weekly_average:
                display_visits = display_visits / 4
            
            # Create readable labels for months
            month_labels = []
            for month_end in monthly_visits.index:
                # Format: "Jan 2025" style
                label = month_end.strftime('%b %Y')
                month_labels.append(label)
            
            # Display monthly visits data
            visits_column_name = 'Average Visits per Week' if show_weekly_average else 'Visits'
            monthly_data = pd.DataFrame({
                'Month': month_labels,
                visits_column_name: display_visits.values
            })
            st.dataframe(monthly_data)
            
            # Plot line graph of monthly visits
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(monthly_visits.index, display_visits.values, marker="o", linestyle="-", linewidth=2, markersize=6)
                ax.set_xlabel("Month")
                if show_weekly_average:
                    ax.set_ylabel("Average Number of Visits per Week")
                    ax.set_title("Average Number of Visits per Week by Month")
                else:
                    ax.set_ylabel("Number of Visits")
                    ax.set_title("Number of Visits per Month")
                ax.grid(True)
                plt.xticks(rotation=45)
                
                # Add text annotations for months with visits
                for i, (date, visits) in enumerate(zip(monthly_visits.index, display_visits.values)):
                    if visits > 0:
                        # Format the annotation value
                        if show_weekly_average:
                            annotation_text = f'{visits:.1f}'
                        else:
                            annotation_text = f'{int(visits)}'
                        ax.annotate(annotation_text, (date, visits), textcoords="offset points", xytext=(0,10), ha='center')
                
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Error creating monthly visits plot: {e}")
        else:
            st.info("No data available for monthly visits.")

    with tab5:
        st.subheader("Map")
        
        def load_locations():
            try:
                with open('locations.json') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading locations.json: {e}")
                return {}
        
        def create_map(locations):
            m = folium.Map(location=[20,0], zoom_start=2)
            for loc in locations.values():
                folium.Marker(
                    location=[loc['latitude'], loc['longitude']],
                    popup=f"<b>{loc['name']}</b><br>{loc['address']}<br><a href='{loc['website']}' target='_blank'>Website</a>",
                    tooltip=loc['name'],
                    icon=folium.DivIcon(html=f"<div style='font-size: 24px;'>🧗‍♂️</div>")
                ).add_to(m)
            return m
        
        # Load locations and create map
        try:
            locations = load_locations()
            if locations:
                map_ = create_map(locations)
                # Use a unique key each time to prevent caching issues
                map_data = st_folium(
                    map_, 
                    width=700, 
                    height=500, 
                    key=None,  # Let streamlit auto-generate key
                    returned_objects=["last_object_clicked"]
                )
                
                # Display clicked location info
                if map_data['last_object_clicked'] is not None:
                    clicked_data = map_data['last_object_clicked']
                    if clicked_data and 'tooltip' in clicked_data:
                        st.success(f"Selected location: {clicked_data['tooltip']}")
            else:
                st.error("No locations found to display on map.")
        except Exception as e:
            st.error(f"Error creating map: {e}")
            st.info("Please check that all required packages are installed: folium, streamlit-folium")

    with tab6:
        st.subheader("Difficulty Graphs")
        
        # Function to plot bar graphs for each difficulty level
        def plot_difficulty_graphs(data, show_tried):
            difficulties = ["vb", "v0", "v1", "v2", "v3", "v4"]
            for difficulty in difficulties:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=data["Dates"], y=data[f"{difficulty}_completed"], ax=ax, label="Completed")
                if show_tried:
                    sns.barplot(x=data["Dates"], y=data[f"{difficulty}_tried"], ax=ax, label="Tried", color="orange")
                ax.set_title(f"Climbs for {difficulty.upper()}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Count")
                ax.legend()
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # Checkbox to toggle the display of the "tried" line
        show_tried = st.checkbox("Show Tried Climbs")
        
        # Plot the difficulty graphs
        plot_difficulty_graphs(data, show_tried)

else:
    st.error("No data available. Please provide a valid public Google Sheet URL.")
