import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import numpy as np
from dateutil.relativedelta import relativedelta

def clean_amount(x):
    if isinstance(x, str):
        x = x.replace(',', '').replace('(', '-').replace(')', '')
    return float(x) if x else 0

def prepare_dataframe(df, projects, categories, cumulative=False):
    plot_df = pd.DataFrame()
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for project in projects:
        for category in categories:
            filtered_df = df[(df['Project #'] == project) & (df['Category'] == category)]
            filtered_df = filtered_df[(filtered_df['Category'] != 'Beginning WIP') & (filtered_df['Category'] != 'Ending WIP')]
            if not filtered_df.empty:
                date_columns = filtered_df.columns[6:-1]
                valid_columns = [col for col in date_columns if pd.to_datetime(col, format='%Y-%m-%d %H:%M:%S') < pd.to_datetime(current_date, format='%Y-%m-%d %H:%M:%S')]
                amounts = [clean_amount(x) for x in filtered_df.iloc[0, 6:-1].values]
                if cumulative:
                    amounts = np.cumsum(amounts)
                amounts = [amounts[i] for i, col in enumerate(date_columns) if col in valid_columns]
                temp_df = pd.DataFrame({
                    'Date': valid_columns,
                    'Amount': amounts,
                    'Project': project,
                    'Category': category
                })
                plot_df = pd.concat([plot_df, temp_df])
    
    return plot_df

def plot_data(df, projects, categories, cumulative=False):
    plot_df = prepare_dataframe(df, projects, categories, cumulative)
    
    if plot_df.empty:
        st.warning("No data available for the selected projects and categories.")
        return
    
    fig = px.line(plot_df, x="Date", y="Amount", color="Category", line_group="Category", hover_name="Category")
    
    # Add label for each line
    for category in categories:
        category_df = plot_df[plot_df['Category'] == category]
        if not category_df.empty:
            last_value = category_df.iloc[-1]['Amount']
            last_value_rounded = round(last_value, 0)  # Round the last value to 0 decimal places
            last_date = category_df.iloc[-1]['Date']
            fig.add_annotation(x=last_date, y=last_value_rounded, text=f'{last_value_rounded}', showarrow=False, xshift=35)  # Adjust xshift to move the label to the right

    fig.update_layout(xaxis=dict(range=[plot_df['Date'].min(), plot_df['Date'].max() + relativedelta(months=10)]))  # Extend the x-axis range by one month

    st.plotly_chart(fig, use_container_width=True)

    # Display the data table
    st.write("Data Table:")
    # pivot wide with Date source for column names, and Amount source for values. keep Project, and Category as index
    plot_wide = plot_df.pivot(index=['Project', 'Category'], columns='Date', values='Amount')
    plot_wide.reset_index(inplace=True)
    # add a row of same Project as last row and Category = Number of Kits
    plot_wide.loc[len(plot_wide.index)] = [plot_wide.iloc[-1]['Project'], 'Number of Kits'] + [0] * (len(plot_wide.columns) - 2)
    # add number_of_kits to the last row to the last column
    plot_wide.iloc[-1, -1] = number_of_kits
    # rename last column to total activity
    plot_wide.rename(columns={plot_wide.columns[-1]: 'Total Activity'}, inplace=True)
    plot_wide.set_index(['Project', 'Category'], inplace=True)
    st.dataframe(plot_wide)

    # Download Button
    @st.cache_data
    def convert_df_to_csv(download_df):
        return download_df.to_csv().encode('utf-8')

    csv = convert_df_to_csv(df[(df['Project #'].isin(projects)) & (df['Category'].isin(categories))])
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='data.csv',
        mime='text/csv',
    )

# App Title and Description
st.title("Revenue Data Visualization")
st.write("This app visualizes revenue data based on selected projects and categories. "
         "Upload your data file or use the sample data provided.")

# File Uploader
uploaded_file = st.sidebar.file_uploader("Choose a file")
cumulative = st.sidebar.checkbox('Cumulative View', False)


if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Revenue Actuals ', skiprows=33)

    # Sidebar for User Inputs
    with st.sidebar:
        st.title("Filters")
        selected_projects = st.multiselect('Select Project #', df['Project #'].unique(), default=df['Project #'].unique()[0])
        selected_categories = st.selectbox('Select Category', ['All', 'Costs', 'Revenues'] + df['Category'].unique().tolist())
        number_of_kits = st.number_input('Total Number of Kits', min_value=0, max_value=1000000000, value=0, step=1)

        if 'All' in selected_categories:
            selected_categories = df['Category'].unique().tolist()
        elif 'Revenues' in selected_categories:
            selected_categories = (['Kit Sales', 'Milestones'])
        elif 'Costs' in selected_categories:
            selected_categories = df['Category'].unique().tolist()
            selected_categories.remove('Kit Sales')
            selected_categories.remove('Milestones')

    # Plotting
    if selected_projects and selected_categories:
        plot_data(df, selected_projects, selected_categories, cumulative)
    else:
        st.warning("Please select at least one project and one category.")

else:
    st.info("Please upload a data file.")
