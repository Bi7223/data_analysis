import streamlit as st

def show_project_entry_page():
    st.title("New Project Entry")

    # Initialize session state for dynamic entries
    if 'nre_count' not in st.session_state:
        st.session_state.nre_count = 1

    if 'recurring_count' not in st.session_state:
        st.session_state.recurring_count = 1

    if st.button('Add NRE Entry'):
        st.session_state.nre_count += 1

    if st.button('Add Recurring Entry'):
        st.session_state.recurring_count += 1

    def process_form_data():
        # Process and save the form data here
        st.success(f"Project '{project_name}' created successfully!")

    with st.form(key='project_form'):
        project_name = st.text_input('Project Name', placeholder='Enter Project Name')
        hourly_rate = st.number_input('Hourly Rate', min_value=0.00, format="%.2f")
        project_date = st.date_input('Project Date')

        # NON RECURRING BUDGET Section
        non_recurring_budget = st.expander("NON RECURRING BUDGET Details", expanded=True)
        with non_recurring_budget:
            st.subheader(project_name + " - Non-Recurring Budget")
            nre_options = ["Labor", "Travel", "Other NRE"]
            for i in range(st.session_state.nre_count):
                with st.container():
                    selected_nre = st.selectbox(f'NRE Category {i+1}', nre_options, key=f'nre_category_{i}')
                    st.number_input('Cost', key=f'nre_cost_{i}', value=0.00, format="%.2f")

        # RECURRING BUDGET Section
        recurring_budget = st.expander("RECURRING BUDGET Details", expanded=True)
        with recurring_budget:
            st.subheader(project_name + " - Recurring Budget")
            re_options = ["Monuments", "Panels", "Kits (Materials Receipts)", "Kits (Manufacturing Labor)"]
            kits_subcategories = ["Materials", "Receipts", "Labor"]
            for i in range(st.session_state.recurring_count):
                with st.container():
                    selected_re = st.selectbox(f'Recurring Category {i+1}', re_options, key=f'recurring_category_{i}')
                    if selected_re == "Kits":
                        selected_kits_subcategory = st.selectbox(f'Kits Subcategory for Recurring Category {i+1}', kits_subcategories, key=f'kits_subcategory_{i}')
                    st.number_input('Cost', key=f'recurring_cost_{i}', value=0.00, format="%.2f")

        st.form_submit_button("Create Project", on_click=process_form_data)

# Call the function
show_project_entry_page()
