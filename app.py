# app.py
import streamlit as st
from datetime import date as dt_date
from utils import add_transaction, load_transactions, spending_by_weekday, check_goal_feasibility
from model import forecast_next_6_months
import pandas as pd
from google import genai





st.set_page_config(page_title="Transaction Tracker", layout="wide")
st.title("Transaction Tracker")

tabs = st.tabs(["Transactions", "Visualization", "Goals", "Chatbot"])

# --- TAB 1: Transactions ---
with tabs[0]:
    st.header("Add Transaction")
    with st.form("add_transaction_form"):
        date_input = st.date_input("date", dt_date.today())
        amount_input = st.number_input("amount", min_value=0.0, step=0.01)
        category_input = st.text_input("category")
        type_input = st.selectbox("type", ["expense", "income"])
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            df = add_transaction(date_input, amount_input, category_input, type_input)
            st.success("Transaction added!")
            st.dataframe(df)
            # Store the updated DataFrame for Penny in Tab 3

    st.subheader("All Transactions")
    df = load_transactions()
    st.dataframe(df)
    # Store the loaded DataFrame in session_state so Tab 3 can access it
    st.session_state["financial_data"] = df

# --- TAB 2: Visualization ---
with tabs[1]:
    st.header("Cumulative Balance Over Time")
    df = load_transactions()
    if not df.empty:
        df['signed_amount'] = df.apply(lambda row: row['amount'] if row['type']=='income' else -row['amount'], axis=1)
        df = df.sort_values('date')
        df['cumulative_balance'] = df['signed_amount'].cumsum()
        st.line_chart(data=df.set_index('date')['cumulative_balance'])
    else:
        st.info("No transactions yet.")

    st.subheader("Spending by Day of Week")
    weekday_totals, max_day, min_day = spending_by_weekday()
    if weekday_totals is not None:
        st.bar_chart(data=weekday_totals.set_index("weekday")["amount"])
        st.write(f"Highest Spending Day: **{max_day['weekday']}** (${max_day['amount']:.2f})")
        st.write(f"Lowest Spending Day: **{min_day['weekday']}** (${min_day['amount']:.2f})")
    else:
        st.info("Not enough expense data yet.")

    st.subheader("Balance Forecast (Next 6 Months)")
    actual_df, forecast_df, explanation = forecast_next_6_months()
    if actual_df is not None:
        actual_plot = actual_df[["date", "cumulative_balance"]].set_index("date")
        forecast_plot = forecast_df.set_index("date")
        combined = actual_plot.join(forecast_plot, how="outer")
        st.line_chart(combined)
        st.write("### Why this prediction?")
        st.write(explanation)
    else:
        st.info("Not enough data to forecast.")

# --- TAB 3: Goals ---
with tabs[2]:
    st.header("Set a Financial Goal")
    goal_type = st.selectbox("What do you want to do?", [
        "Save X amount of Money",
        "Spend less on a specific Category",
        "Spend less on a specific Day",
        "Budget/save more for a Category"
    ])
    
    goal_amount = st.number_input("Amount ($)", min_value=0.0, step=0.01)
    goal_time_months = st.number_input("Timeframe (months)", min_value=1, max_value=60, step=1)
    
    goal_category = None
    goal_day = None
    if "Category" in goal_type:
        df = load_transactions()
        categories = df['category'].unique() if not df.empty else []
        goal_category = st.selectbox("Select Category", categories)
    if "Day" in goal_type:
        goal_day = st.selectbox("Select Day of Week", [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ])

    if st.button("Check Goal Feasibility"):
        explanation, checkpoints = check_goal_feasibility(
            goal_type, goal_amount, goal_time_months, goal_category, goal_day
        )
        st.write(explanation)

        if checkpoints is not None and not checkpoints.empty:
            st.write("### Suggested Checkpoints")
            st.dataframe(checkpoints)

with tabs[3]:
    st.title("🐵 Penny the Monkey 💰")

    # Create client once
    if "client" not in st.session_state:
        st.session_state.client = genai.Client()

    # Create Penny chat once
    if "chat" not in st.session_state:
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config={
                "system_instruction": "You are Penny the Monkey 🐵, a friendly financial guide...",
                "temperature": 0.7
            }
        )

    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm Penny the Monkey 🐵💰 I'm here to help you feel confident about your money!"
            }
        ]

    # Use a container to hold the chat messages
    chat_container = st.container()

    # Display previous messages
    with chat_container:
        for msg in st.session_state.messages:
            avatar = "🐵" if msg["role"] == "assistant" else "👩‍💻"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Chat input (always below messages)
    prompt = st.chat_input("Ask Penny about money 💰")
    if prompt:
        # Show user message
        with chat_container:
            with st.chat_message("user", avatar="👩‍💻"):
                st.markdown(prompt)
        # Save user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Stream AI response
        with chat_container:
            with st.chat_message("assistant", avatar="🐵"):
                placeholder = st.empty()
                full_response = ""
                for chunk in st.session_state.chat.send_message_stream(prompt):
                    full_response += chunk.text
                    placeholder.markdown(full_response)
        # Save AI response
        st.session_state.messages.append({"role": "assistant", "content": full_response})
