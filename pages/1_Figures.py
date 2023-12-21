import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def clean_amount(x):
    if isinstance(x, str):
        x = x.replace(',', '').replace('(', '-').replace(')', '')
    return float(x) if x else 0

def plot_data(df, projects, categories):
    plt.figure(figsize=(14, 7))
    for project in projects:
        for category in categories:
            filtered_df = df[(df['Project #'] == project) & (df['Category'] == category)]
            if not filtered_df.empty:
                date_columns = filtered_df.columns[6:-1]
                amounts = filtered_df.iloc[0, 6:-1].values
                amounts = [clean_amount(x) for x in amounts]
                plt.plot(date_columns, amounts, marker='o', markersize=3, label=f'{project} - {category}')

    plt.xticks(rotation=45)
    plt.title('Revenue Data Visualization')
    plt.xlabel('Date')
    plt.ylabel('Amount')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)

    # Display the data table
    st.write("Data Table:")
    st.dataframe(df[(df['Project #'].isin(projects)) & (df['Category'].isin(categories))])

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
         "Use the sidebar to select the project numbers and categories to display the corresponding data.")

st.title("Revenue Data Visualization")
st.write("This app visualizes revenue data based on selected projects and categories. "
         "Upload your data file or use the sample data provided.")

# File Uploader
uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Revenue Actuals ', skiprows=33)

    # Sidebar for User Inputs
    with st.sidebar:
        st.title("Filters")
        selected_projects = st.multiselect('Select Project #', df['Project #'].unique(), default=df['Project #'].unique()[0])
        selected_categories = st.multiselect('Select Category', df['Category'].unique(), default=df['Category'].unique()[0])

    # Plotting
    if selected_projects and selected_categories:
        plot_data(df, selected_projects, selected_categories)
    else:
        st.warning("Please select at least one project and one category.")
else:
    st.info("Please upload a data file.")
