import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

def load_data(file_name, project_name):
    project_budget = pd.read_excel(file_name, sheet_name=project_name)
    return project_budget

def process_revenue_actuals(revenue_actuals):
    """Process the Revenue Actuals DataFrame."""
    revenue_actuals = revenue_actuals[revenue_actuals['Project #'] == project_name]
    current_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    revenue_actuals_filter = revenue_actuals.filter(regex='20\d\d', axis=1)
    revenue_actuals_filter.columns = pd.to_datetime(revenue_actuals_filter.columns)
    revenue_actuals['Total_Actuals'] = revenue_actuals_filter.loc[:, revenue_actuals_filter.columns < current_month].sum(axis=1)
    revenue_actuals['Total_Forcast'] = revenue_actuals_filter.loc[:, revenue_actuals_filter.columns >= current_month].sum(axis=1)
    return revenue_actuals

def summarize_budget(budget_df, revenue_actuals, category, budget_column='NRE '):
    """Summarize budget for NRE or Kits."""
    budget_summary = budget_df[budget_df.iloc[:, 0].str.contains(category, case=False, na=False)]
    budget_summary['Budget'] = budget_summary[budget_column].fillna(0) + budget_summary['CR'].fillna(0)

    # Creating a summary DataFrame
    summary = pd.DataFrame(columns=['Budget', 'Actual Revenues', 'Forcast', 'Remaining on Budget'])

    # Iterate over each category and calculate the sums
    for cat in category.split('|'):
        cat_budget = budget_summary[budget_summary.iloc[:, 0].str.contains(cat, case=False, na=False)]['Budget'].sum()
        cat_actuals = revenue_actuals[revenue_actuals['Category'].str.contains(cat, case=False, na=False)]['Total_Actuals'].sum()
        cat_forcast = revenue_actuals[revenue_actuals['Category'].str.contains(cat, case=False, na=False)]['Total_Forcast'].sum()

        summary.loc[cat] = [cat_budget, cat_actuals, cat_forcast, cat_actuals - cat_budget]

    # Calculate totals
    summary.loc['Total'] = summary.sum()

    return summary

def create_stacked_bar_chart(dataframe, title):
    """Create a stacked bar chart from the given DataFrame."""
    # filter out index containing "total"
    # dataframe = dataframe[~dataframe.index.str.contains('Total', case=False, na=False)]
    # keep first three rows of the datafra
    categories = dataframe.index.tolist()
    categories.remove(' ')  # Remove the blank rows if they exist
    budget = dataframe.loc[categories, 'Budget']
    actual_revenues = dataframe.loc[categories, 'Actual Revenues']
    forecast = dataframe.loc[categories, 'Forcast']

    fig = go.Figure(data=[
        go.Bar(name='Budget', x=categories, y=budget),
        go.Bar(name='Actual Revenues', x=categories, y=actual_revenues),
        go.Bar(name='Forecast', x=categories, y=forecast)
    ])

    fig.update_layout(
        title=title,
        yaxis_title='Amounts',
        # barmode='stack'
    )
    # change figure size
    fig.update_layout(
        autosize=False,
        width=600,
        height=475,
    )
    return fig

# Set up the page
st.set_page_config(page_title="WIP Analysis", layout="wide")
st.title("WIP Analysis")
st.write("This page is used to analyze WIP data for both NRE and Kit projects.")

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    revenue_actuals = pd.read_excel(uploaded_file, sheet_name='Revenue Actuals ', skiprows=33)
    project_name = st.sidebar.selectbox("Select a Project", options=revenue_actuals["Project #"].unique(), index=0)
    number_of_kits = st.sidebar.number_input('Enter Number of Kits', min_value=1, value=21)
    number_of_months = st.sidebar.number_input('Enter Number of Months', min_value=0, value=0)

    if st.sidebar.button('Analyze'):
        # Process the file
        project_budget = load_data(uploaded_file, project_name)
        revenue_actuals = process_revenue_actuals(revenue_actuals)

        # Summarize NRE and Kits
        NRE_summary = summarize_budget(project_budget, revenue_actuals, 'Engineering Labor|Other NRE|TRAVEL')
        kit_summary = summarize_budget(project_budget, revenue_actuals, 'Manufacturing Labor|Material Receipts', budget_column='NRE ')

        # Additional calculations for NRE Summary
        NRE_summary.loc[' '] = ''
        NRE_summary.loc['Average Engineering Labor'] = 0
        NRE_summary.loc['Average Engineering Labor', 'Actual Revenues'] = NRE_summary.loc['Engineering Labor', 'Actual Revenues'] / number_of_kits
        NRE_summary.loc['Average Engineering Labor', 'Forcast'] = NRE_summary.loc['Engineering Labor', 'Forcast'] / number_of_kits
        NRE_summary.loc['Average Engineering Labor', 'Budget'] = NRE_summary.loc['Engineering Labor', 'Budget'] / number_of_kits
        NRE_summary.loc['Average Other NRE'] = 0
        NRE_summary.loc['Average Other NRE', 'Actual Revenues'] = NRE_summary.loc['Other NRE', 'Actual Revenues'] / number_of_kits
        NRE_summary.loc['Average Other NRE', 'Forcast'] = NRE_summary.loc['Other NRE', 'Forcast'] / number_of_kits
        NRE_summary.loc['Average Other NRE', 'Budget'] = NRE_summary.loc['Other NRE', 'Budget'] / number_of_kits
        NRE_summary.loc['Average TRAVEL'] = 0
        NRE_summary.loc['Average TRAVEL', 'Actual Revenues'] = NRE_summary.loc['TRAVEL', 'Actual Revenues'] / number_of_kits
        NRE_summary.loc['Average TRAVEL', 'Forcast'] = NRE_summary.loc['TRAVEL', 'Forcast'] / number_of_kits
        NRE_summary.loc['Average TRAVEL', 'Budget'] = NRE_summary.loc['TRAVEL', 'Budget'] / number_of_kits
        NRE_summary.loc['Average Total'] = 0
        NRE_summary.loc['Average Total', 'Actual Revenues'] = NRE_summary.loc['Total', 'Actual Revenues'] / number_of_kits
        NRE_summary.loc['Average Total', 'Forcast'] = NRE_summary.loc['Total', 'Forcast'] / number_of_kits
        NRE_summary.loc['Average Total', 'Budget'] = NRE_summary.loc['Total', 'Budget'] / number_of_kits
        NRE_summary.loc['  '] = ''
        NRE_summary.loc['Milestones'] = 0
        NRE_summary.loc['Milestones', 'Actual Revenues'] = revenue_actuals[revenue_actuals['Category'] == 'Milestones']['Total_Actuals'].sum()
        NRE_summary.loc['Milestones', 'Forcast'] = revenue_actuals[revenue_actuals['Category'] == 'Milestones']['Total_Forcast'].sum()
        NRE_summary.loc['Cost Vs Billed', 'Actual Revenues'] = NRE_summary.loc['Total', 'Actual Revenues'] + NRE_summary.loc['Milestones', 'Actual Revenues']
        NRE_summary.loc['Cost Vs Billed', 'Forcast'] = NRE_summary.loc['Total', 'Forcast'] + NRE_summary.loc['Milestones', 'Forcast']

        # Additional calculations for Kit Summary
        kit_summary.loc[' '] = ''
        kit_summary.loc['Average Manufacturing Labor'] = 0
        kit_summary.loc['Average Manufacturing Labor', 'Actual Revenues'] = kit_summary.loc['Manufacturing Labor', 'Actual Revenues'] / number_of_kits
        kit_summary.loc['Average Manufacturing Labor', 'Forcast'] = kit_summary.loc['Manufacturing Labor', 'Forcast'] / number_of_kits
        kit_summary.loc['Average Manufacturing Labor', 'Budget'] = kit_summary.loc['Manufacturing Labor', 'Budget'] / number_of_kits
        
        kit_summary.loc['Average Material Receipts'] = 0
        kit_summary.loc['Average Material Receipts', 'Actual Revenues'] = kit_summary.loc['Material Receipts', 'Actual Revenues'] / number_of_kits
        kit_summary.loc['Average Material Receipts', 'Forcast'] = kit_summary.loc['Material Receipts', 'Forcast'] / number_of_kits
        kit_summary.loc['Average Material Receipts', 'Budget'] = kit_summary.loc['Material Receipts', 'Budget'] / number_of_kits

        kit_summary.loc['Average Total'] = 0
        kit_summary.loc['Average Total', 'Actual Revenues'] = kit_summary.loc['Total', 'Actual Revenues'] / number_of_kits
        kit_summary.loc['Average Total', 'Forcast'] = kit_summary.loc['Total', 'Forcast'] / number_of_kits
        kit_summary.loc['Average Total', 'Budget'] = kit_summary.loc['Total', 'Budget'] / number_of_kits

        
        kit_summary.loc['  '] = ''
        kit_summary.loc['Kit Sales'] = 0
        kit_summary.loc['Kit Sales', 'Actual Revenues'] = revenue_actuals[revenue_actuals['Category'] == 'Kit Sales']['Total_Actuals'].sum()
        kit_summary.loc['Kit Sales', 'Forcast'] = revenue_actuals[revenue_actuals['Category'] == 'Kit Sales']['Total_Forcast'].sum()
        
        

        # for each numerical cell, round
        NRE_summary = NRE_summary.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        kit_summary = kit_summary.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        kit_summary_adjusted = kit_summary.copy()
        kit_summary_adjusted.loc['Manufacturing Labor', 'Remaining on Budget'] = kit_summary_adjusted.loc['Manufacturing Labor', 'Remaining on Budget'] - kit_summary_adjusted.loc['Total', 'Remaining on Budget']
        kit_summary_adjusted.loc['Total', 'Remaining on Budget'] = kit_summary_adjusted.loc['Total', 'Remaining on Budget'] - kit_summary_adjusted.loc['Total', 'Remaining on Budget']

        # Display the summaries
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.write("NRE Summary:", NRE_summary)
                st.write("Kit Summary:", kit_summary_adjusted)

            with col2:
                nre_plot = create_stacked_bar_chart(NRE_summary, "NRE Summary")
                st.plotly_chart(nre_plot)

                kit_plot = create_stacked_bar_chart(kit_summary, "Kit Summary")
                st.plotly_chart(kit_plot)
        # Create a data table with remaining budget of Engineering Labor, Other NRE, Travel, Manufacturing Labor, Material Receipts
        data_table = pd.DataFrame(columns=['Category', 'Remaining Budget'])
        data_table.loc[0] = ['Engineering Labor', NRE_summary.loc['Engineering Labor', 'Remaining on Budget']]
        data_table.loc[1] = ['Other NRE', NRE_summary.loc['Other NRE', 'Remaining on Budget']]
        data_table.loc[2] = ['Travel', NRE_summary.loc['TRAVEL', 'Remaining on Budget']]
        data_table.loc[3] = ['Total NRE', NRE_summary.loc['Total', 'Remaining on Budget']]
        data_table.loc[4] = ['Manufacturing Labor', kit_summary.loc['Manufacturing Labor', 'Remaining on Budget']]
        data_table.loc[5] = ['Material Receipts', kit_summary.loc['Material Receipts', 'Remaining on Budget']]
        data_table.loc[6] = ['Total Kits', kit_summary.loc['Total', 'Remaining on Budget']]

        # Dynamic Forecast Calculations
        if NRE_summary.loc['Total', 'Remaining on Budget'] < 0:
            numb_of_remaining_months = -NRE_summary.loc['Total', 'Remaining on Budget'] / NRE_summary.loc['Average Total', 'Actual Revenues']
            numb_of_remaining_months = round(numb_of_remaining_months)
            numb_of_remaining_months = int(numb_of_remaining_months)

            # Update NRE 'Total' row in data_table for each remaining month
            for i in range(1, numb_of_remaining_months + 1):
                data_table.loc[data_table['Category'] == 'Total NRE', 'Forecast Month ' + str(i)] = \
                    data_table.loc[data_table['Category'] == 'Total NRE', 'Remaining Budget'] + \
                    NRE_summary.loc['Average Total', 'Actual Revenues'] * i

        if kit_summary.loc['Total', 'Remaining on Budget'] < 0:
            if kit_summary.loc['Manufacturing Labor', 'Remaining on Budget'] < 0:
                numb_of_remaining_months = -kit_summary.loc['Total', 'Remaining on Budget'] / kit_summary.loc['Average Manufacturing Labor', 'Actual Revenues']
                numb_of_remaining_months = round(numb_of_remaining_months)
                numb_of_remaining_months = int(numb_of_remaining_months)
                # Update Kit 'Total' row in data_table for each remaining month
                for i in range(1, numb_of_remaining_months + 1):
                    data_table.loc[data_table['Category'] == 'Manufacturing Labor', 'Forecast Month ' + str(i)] = \
                        kit_summary.loc['Average Manufacturing Labor', 'Actual Revenues']
        # remove remaining budget column
        data_table = data_table.drop(columns=['Remaining Budget'])
        st.write("Dynamic Forcast:", data_table)
else:
    st.info("Please upload a data file.")

