import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly

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
    categories = dataframe.index.tolist()
    categories.remove(' ')  # Remove the blank rows if they exist
    budget = dataframe.loc[categories, 'Budget']
    actual_revenues = dataframe.loc[categories, 'Actual Revenues']
    forecast = dataframe.loc[categories, 'Forcast']

    fig = go.Figure(data=[
        go.Bar(name='Budget', x=categories, y=budget),
        go.Bar(name='Actual Revenues', x=categories, y=actual_revenues, base=budget),
        go.Bar(name='Forecast', x=categories, y=forecast, base=budget + actual_revenues)
    ])

    fig.update_layout(
        title=title,
        yaxis_title='Amounts',
        barmode='stack'
    )
    # change figure size
    fig.update_layout(
        autosize=False,
        width=600,
        height=300,
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

    if st.sidebar.button('Analyze'):
        # Process the file
        project_budget = load_data(uploaded_file, project_name)
        revenue_actuals = process_revenue_actuals(revenue_actuals)

        # Summarize NRE and Kits
        NRE_summary = summarize_budget(project_budget, revenue_actuals, 'Engineering Labor|Other NRE|TRAVEL')
        kit_summary = summarize_budget(project_budget, revenue_actuals, 'Manufacturing Labor|Materials ', budget_column='NRE ')

        # Additional calculations for NRE Summary
        NRE_summary.loc[' '] = ''
        NRE_summary.loc['Milestones'] = 0
        NRE_summary.loc['Milestones', 'Actual Revenues'] = revenue_actuals[revenue_actuals['Category'] == 'Milestones']['Total_Actuals'].sum()
        NRE_summary.loc['Milestones', 'Forcast'] = revenue_actuals[revenue_actuals['Category'] == 'Milestones']['Total_Forcast'].sum()
        NRE_summary.loc[' '] = ''
        NRE_summary.loc['Cost Vs Billed', 'Actual Revenues'] = NRE_summary.loc['Total', 'Actual Revenues'] + NRE_summary.loc['Milestones', 'Actual Revenues']
        NRE_summary.loc['Cost Vs Billed', 'Forcast'] = NRE_summary.loc['Total', 'Forcast'] + NRE_summary.loc['Milestones', 'Forcast']

        # Additional calculations for Kit Summary
        kit_summary.loc[' '] = ''
        kit_summary.loc['Cost Average per kit'] = 0
        kit_summary.loc['Actual Average per kit'] = 0
        kit_summary.loc['Cost Average per kit', 'Actual Revenues'] = kit_summary.loc['Total', 'Actual Revenues'] / number_of_kits
        kit_summary.loc['Cost Average per kit', 'Forcast'] = kit_summary.loc['Total', 'Forcast'] / number_of_kits

        # for each numerical cell, round
        NRE_summary = NRE_summary.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        kit_summary = kit_summary.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

        # Display the summaries
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.write("NRE Summary:", NRE_summary)
                st.write("Kit Summary:", kit_summary)

            with col2:
                nre_plot = create_stacked_bar_chart(NRE_summary, "NRE Summary")
                st.plotly_chart(nre_plot)

                kit_plot = create_stacked_bar_chart(kit_summary, "Kit Summary")
                st.plotly_chart(kit_plot)
else:
    st.info("Please upload a data file.")

