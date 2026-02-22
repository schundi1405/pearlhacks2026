#ui.py
import streamlit as st
from datetime import date as dt_date

st.title("Transaction Tracker")

with st.form("add_transaction_form"):
    date_input = st.date_input("Date", dt_date.today())
    amount_input = st.number_input("Amount", min_value=0.0, step=0.01)
    category_input = st.text_input("Category")
    type_input = st.selectbox("Type", ["expense", "income"])
    
    submitted = st.form_submit_button("Add Transaction")
    
    if submitted:
        df = add_transaction(date_input, amount_input, category_input, type_input)
        st.success("Transaction added!")
        st.dataframe(df)