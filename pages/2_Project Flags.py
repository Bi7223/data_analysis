import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def color_vowel(value):
    return f"background-color: red;" if "nan" not in str(value) and "No red flag" not in str(value) else None

# Set up the page
st.set_page_config(page_title="Flags", layout="wide")
st.title("Project Flags")
st.write("This page combine project budget and revenue actuals to generate flags for each category.")

# Upload Excel file
uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    # Read Excel file
    revenue_actuals = pd.read_excel(uploaded_file, sheet_name='Revenue Actuals ', skiprows=33)

    # Project selection
    project_name = st.sidebar.selectbox("Select a Project", options=revenue_actuals["Project #"].unique(), index=0)

    # extract sheet names from uploaded file
    sheet_names = pd.ExcelFile(uploaded_file).sheet_names

    # if project_name is not in sheet_names, then display error message
    if project_name not in sheet_names:
        st.write("Budget information is not available for selected project, please select another project")
        st.stop()
    
    project_budget = pd.read_excel(uploaded_file, sheet_name=project_name)

    # Data processing

    # Number_of_Kits
    Number_of_Kits = project_budget[project_budget.iloc[:,0].str.contains('NRE|Kit|TRAVEL', case=False, na=False)]
    Number_of_Kits = Number_of_Kits[~Number_of_Kits.iloc[:,0].str.contains('Other NRE', na=False)]
    Number_of_Kits = Number_of_Kits[~Number_of_Kits.iloc[:,5].str.contains('AVG cost based on Qty| ', na=False)]
    Number_of_Kits = Number_of_Kits['AVG cost based on Qty'].sum()

    # Beginning_WIP
    Beginning_WIP = project_budget[project_budget.iloc[:,0].str.contains('NRE|Kit|TRAVEL ', case=False, na=False)]
    Beginning_WIP = Beginning_WIP[~Beginning_WIP.iloc[:,0].str.contains('Other NRE', na=False)]
    Beginning_WIP = Beginning_WIP[~Beginning_WIP.iloc[:,2].str.contains('Hour', na=False)]
    Beginning_WIP = Beginning_WIP['NRE '].sum() + Beginning_WIP['CR'].sum()

    # Engineering_Labor
    Engineering_Labor = project_budget[project_budget.iloc[:,0].str.contains('Engineering Labor', case=False, na=False)]
    Engineering_Labor = Engineering_Labor['NRE '].sum() + Engineering_Labor['CR'].sum()

    # Manufacturing_Labor
    Manufacturing_Labor = project_budget[project_budget.iloc[:,0].str.contains('Manufacturing Labor', case=False, na=False)]
    Manufacturing_Labor = Manufacturing_Labor['NRE '].sum() + Manufacturing_Labor['CR'].sum()

    # Material_Receipts
    Material_Receipts = project_budget[project_budget.iloc[:,0].str.contains('Material', case=False, na=False)]
    Material_Receipts = Material_Receipts['NRE '].sum() + Material_Receipts['CR'].sum()

    # Other_NRE_Costs
    Other_NRE_Costs = project_budget[project_budget.iloc[:,0].str.contains('Other NRE|TRAVEL', case=False, na=False)]
    Other_NRE_Costs = Other_NRE_Costs['NRE '].sum() + Other_NRE_Costs['CR'].sum()

    # Milestones
    Milestones = project_budget[project_budget.iloc[:,0].str.contains('NRE|TRAVEL ', case=False, na=False)]
    Milestones = Milestones[~Milestones.iloc[:,0].str.contains('Other NRE', na=False)]
    Milestones = -(Milestones['NRE '].sum() + Milestones['CR'].sum())

    # Kit_Sales
    Kit_Sales = project_budget[project_budget.iloc[:,0].str.contains('Kit', case=False, na=False)]
    Kit_Sales = Kit_Sales[~Kit_Sales.iloc[:,2].str.contains('Hour', na=False)]
    Kit_Sales = -(Kit_Sales['NRE '].sum() + Kit_Sales['CR'].sum())

    # Ending_WIP
    Ending_WIP = Engineering_Labor + Manufacturing_Labor + Material_Receipts + Other_NRE_Costs + Milestones + Kit_Sales

    # create project_budget dataframe with two column Category, and Budget
    project_budget = pd.DataFrame({'Category': ['Number of Kits', 'Beginning WIP', 'Engineering Labor', 'Manufacturing Labor', 'Material Receipts', 'Other NRE Costs', 'Milestones', 'Kit Sales', 'Ending WIP'],
                                   'Budget': [Number_of_Kits, Beginning_WIP, Engineering_Labor, Manufacturing_Labor, Material_Receipts, Other_NRE_Costs, Milestones, Kit_Sales, Ending_WIP]})

    # rounnd Amount to 2 decimal places
    project_budget['Budget'] = project_budget['Budget'].round(2)
    project_budget['Budget per Kit'] = round(project_budget['Budget'] / Number_of_Kits, 2)

    # filter revenue_actuals for column Project Name = project_name
    revenue_actuals = revenue_actuals[revenue_actuals['Project #'] == project_name]

    # merge project_budget and revenue_actuals on column Category
    project_budget = project_budget.merge(revenue_actuals, how='left', on='Category')

    cols = project_budget.columns.tolist()
    project_budget = project_budget[cols[3:7] + cols[0:3] + [cols[-1]]]

    project_budget['Total Activity'] = project_budget['Total Activity'].round(2)

    # create column Activity per kit
    project_budget['Activity per Kit'] = round(project_budget['Total Activity'] / Number_of_Kits, 2)

    # create column difference between Budget and Total Activity
    project_budget['Total Activity - Budget'] = project_budget['Total Activity'] - project_budget['Budget']

    monthly_data = revenue_actuals[revenue_actuals.columns.tolist()[5:-1]]

    # set first column as index
    monthly_data = monthly_data.set_index(monthly_data.columns.tolist()[0])

    # remove first column
    monthly_data = monthly_data.iloc[:, 1:]

    # cumulative sum of each row 
    cumulative_data = monthly_data.cumsum(axis=1)

    try:
        Beginning_WIP_red_flag = (cumulative_data[cumulative_data.index == 'Beginning WIP'].iloc[0] - Beginning_WIP)[ (cumulative_data[cumulative_data.index == 'Beginning WIP'].iloc[0] - Beginning_WIP) > 0 ].index[0]
    except IndexError:
        Beginning_WIP_red_flag = 'No red flag'

    try:
        Engineering_Labor_red_flag = (cumulative_data[cumulative_data.index == 'Engineering Labor'].iloc[0] - Engineering_Labor)[ (cumulative_data[cumulative_data.index == 'Engineering Labor'].iloc[0] - Engineering_Labor) > 0 ].index[0]
    except IndexError:
        Engineering_Labor_red_flag = 'No red flag'

    try:
        Manufacturing_Labor_red_flag = (cumulative_data[cumulative_data.index == 'Manufacturing Labor'].iloc[0] - Manufacturing_Labor)[ (cumulative_data[cumulative_data.index == 'Manufacturing Labor'].iloc[0] - Manufacturing_Labor) > 0 ].index[0]
    except IndexError:
        Manufacturing_Labor_red_flag = 'No red flag'

    try:
        Material_Receipts_red_flag = (cumulative_data[cumulative_data.index == 'Material Receipts'].iloc[0] - Material_Receipts)[ (cumulative_data[cumulative_data.index == 'Material Receipts'].iloc[0] - Material_Receipts) > 0 ].index[0]
    except IndexError:
        Material_Receipts_red_flag = 'No red flag'

    try:
        Other_NRE_Costs_red_flag = (cumulative_data[cumulative_data.index == 'Other NRE Costs'].iloc[0] - Other_NRE_Costs)[ (cumulative_data[cumulative_data.index == 'Other NRE Costs'].iloc[0] - Other_NRE_Costs) > 0 ].index[0]
    except IndexError:
        Other_NRE_Costs_red_flag = 'No red flag'

    try:
        Milestones_red_flag = (cumulative_data[cumulative_data.index == 'Milestones'].iloc[0] - Milestones)[ (cumulative_data[cumulative_data.index == 'Milestones'].iloc[0] - Milestones) < 0 ].index[0]
    except IndexError:
        Milestones_red_flag = 'No red flag'

    try:
        Kit_Sales_red_flag = (cumulative_data[cumulative_data.index == 'Kit Sales'].iloc[0] - Kit_Sales)[ (cumulative_data[cumulative_data.index == 'Kit Sales'].iloc[0] - Kit_Sales) > 0 ].index[0]
    except IndexError:
        Kit_Sales_red_flag = 'No red flag'

    try:
        Ending_WIP_red_flag = (cumulative_data[cumulative_data.index == 'Ending WIP'].iloc[0] - Ending_WIP)[ (cumulative_data[cumulative_data.index == 'Ending WIP'].iloc[0] - Ending_WIP) < 0 ].index[0]
    except IndexError:
        Ending_WIP_red_flag = 'No red flag'

    red_flags = pd.DataFrame({'Category': ['Beginning WIP', 'Engineering Labor', 'Manufacturing Labor', 'Material Receipts', 'Other NRE Costs', 'Milestones', 'Kit Sales', 'Ending WIP'],
                                'Red Flag': [Beginning_WIP_red_flag, Engineering_Labor_red_flag, Manufacturing_Labor_red_flag, Material_Receipts_red_flag, Other_NRE_Costs_red_flag, Milestones_red_flag, Kit_Sales_red_flag, Ending_WIP_red_flag]})
    
    project_budget = project_budget.merge(red_flags, how='left', on='Category')

    # Display the processed table
    st.write("Processed Data Table")

    st.dataframe(project_budget.iloc[:, 3:].style.applymap(color_vowel, subset=["Red Flag"]))

    # Download button for CSV
    csv = project_budget.to_csv(index=False)
    st.download_button("Download data as CSV", csv, "file.csv", "text/csv", key='download-csv')

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 5))
    project_budget_copy = project_budget.copy()
    project_budget_copy = project_budget_copy.drop(project_budget_copy[project_budget_copy['Category'].isin(['Number of Kits', 'Beginning WIP', 'Ending WIP', 'Milestones', 'Kit Sales'])].index)

    categories = project_budget_copy['Category']
    budget_values = project_budget_copy['Budget']
    total_activity_values = project_budget_copy['Total Activity']

    bar_width = 0.35
    r1 = np.arange(len(categories))
    r2 = [x + bar_width for x in r1]

    ax.bar(r1, budget_values, width=bar_width, label='Budget')
    ax.bar(r2, total_activity_values, width=bar_width, label='Total Activity')

    for i, value in enumerate(budget_values):
        ax.text(i, value, f'{value/1000000:.1f}M', ha='center', va='bottom')

    for i, value in enumerate(total_activity_values):
        ax.text(i + bar_width, value, f'{value/1000000:.1f}M', ha='center', va='bottom')

    ax.set_xticks(r1 + bar_width / 2)
    ax.set_xticklabels(categories, rotation=45)

    ax.legend()
    ax.text(0.5, 0.95, 'Total Cost', transform=ax.transAxes, ha='center')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1000000:.1f}M'))

    st.pyplot(fig)
else:
    st.info("Please upload a data file.")
    # Additional Streamlit components can be added as needed
