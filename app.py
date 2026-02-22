# app.py
import streamlit as st
from datetime import date as dt_date
from utils import (
    add_transaction,
    load_transactions,
    spending_by_weekday,
    check_goal_feasibility, 
    calculate_financial_health
)
from model import forecast_next_6_months
import pandas as pd
from google import genai
import altair as alt


st.set_page_config(page_title="Transaction Tracker", layout="wide")

col1, col2 = st.columns([0.8, 8], gap="small")

with col1:
    st.image("gm.jpg", width=150)  # replace with your image file

with col2:
    st.markdown(
        "<h1 style='margin:0;'>Transaction Tracker</h1>",
        unsafe_allow_html=True
    )

tabs = st.tabs(["Transactions", "Visualization", "Goals", "Chatbot"])

with tabs[0]:

    st.header("Add Transaction")

    with st.form("add_transaction_form"):
        date_input = st.date_input("Date", dt_date.today())
        amount_input = st.number_input("Amount", min_value=0.0, step=0.01)
        category_input = st.text_input("Category")
        type_input = st.selectbox("Type", ["expense", "income"])
        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            df = add_transaction(date_input, amount_input, category_input, type_input)
            st.success("Transaction added!")
            # Convert datetime to date
            df['date'] = pd.to_datetime(df['date']).dt.date
            st.dataframe(df)

    st.subheader("All Transactions")
    df = load_transactions()
    # Convert datetime to date
    df['date'] = pd.to_datetime(df['date']).dt.date
    st.dataframe(df)
    st.session_state["financial_data"] = df

# visualizations tab
with tabs[1]:

    st.header("Financial Overview")

    df = load_transactions()


    col1, col2 = st.columns(2)

    with col1:
    
        st.subheader("Cumulative Balance Over Time")

        if not df.empty:
            df['signed_amount'] = df.apply(
                lambda row: row['amount'] if row['type']=='income' else -row['amount'],
                axis=1
            )
            df = df.sort_values('date')
            df['cumulative_balance'] = df['signed_amount'].cumsum()

            chart = (
                alt.Chart(df)
                .mark_line(color="green", strokeWidth=3)
                .encode(
                    x="date:T",
                    y="cumulative_balance:Q"
                )
                .properties(height=350)
            )

            st.altair_chart(chart, use_container_width=True)

        else:
            st.info("No transactions yet.")

    with col2:

        st.subheader("Balance Forecast (Next 6 Months)")

        actual_df, forecast_df, explanation = forecast_next_6_months()

        if actual_df is not None:
            actual_plot = actual_df[["date", "cumulative_balance"]].set_index("date")
            forecast_plot = forecast_df.set_index("date")
            combined = actual_plot.join(forecast_plot, how="outer").reset_index()

            combined_melted = combined.melt(
                id_vars="date",
                var_name="type",
                value_name="balance"
            )

            chart = (
                alt.Chart(combined_melted)
                .mark_line(strokeWidth=3)
                .encode(
                    x="date:T",
                    y="balance:Q",
                    color=alt.Color(
                        "type:N",
                        scale=alt.Scale(range=["green", "green"])
                    ),
                    strokeDash=alt.condition(
                        alt.datum.type == combined.columns[2],
                        alt.value([5,5]),
                        alt.value([1,0])
                    )
                )
                .properties(height=350)
            )

            st.altair_chart(chart, use_container_width=True)

        else:
            st.info("Not enough data to forecast.")

    st.subheader("Spending by Day of Week")

    weekday_totals, max_day, min_day = spending_by_weekday()

    if weekday_totals is not None:

        chart = (
            alt.Chart(weekday_totals)
            .mark_bar(color="green")
            .encode(
                x=alt.X(
                    "weekday:N",
                    sort=[
                        "Monday","Tuesday","Wednesday",
                        "Thursday","Friday","Saturday","Sunday"
                    ],
                    axis=alt.Axis(labelAngle=0, title=None)  # <-- keeps labels horizontal
                ),
                y=alt.Y("amount:Q", title="Average Spending ($)")
            )
            .properties(height=350)
        )

        st.altair_chart(chart, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.metric(
                label="Highest Spending Day",
                value=f"{max_day['weekday']}: \\${max_day['amount']:.2f} on average"
            )

        with col4:
            st.metric(
                label="Lowest Spending Day",
                value=f"{min_day['weekday']}: \\${min_day['amount']:.2f} on average"
            )

    else:
        st.info("Not enough expense data yet.")
    

    st.subheader("Financial Health Score")

    score, summary = calculate_financial_health()

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        # Circle visualization using st.metric (centered)
        st.markdown(f"""
            <div style='text-align:center; margin-top:20px;'>
                <div style='
                    display:inline-block;
                    border-radius:50%;
                    width:120px;
                    height:120px;
                    line-height:120px;
                    background-color:#4CAF50;
                    color:white;
                    font-size:48px;
                    font-weight:bold;
                '>{score}</div>
                <p style='margin-top:10px; font-size:16px;'>{summary}</p>
            </div>
        """, unsafe_allow_html=True)

# goals tab
with tabs[2]:

    st.header("Set a Financial Goal")

    # Row 1
    col1, col2 = st.columns(2)

    with col1:
        goal_type = st.selectbox(
            "What do you want to do?",
            ["Save X Amount", "Spend Less on X Day"]
        )

    with col2:
        goal_amount = st.number_input(
            "Goal Amount ($)",
            min_value=0.0,
            step=0.01
        )
    col3, col4 = st.columns(2)

    with col3:
        goal_time_months = st.number_input(
            "Timeframe (months)",
            min_value=1,
            max_value=60,
            step=1
        )

    with col4:
        goal_start_date = st.date_input("Goal Start Date", dt_date.today())

    col5, col6 = st.columns(2)

    with col5:
        goal_reward = st.text_input("Reward for Completing This Goal")

    with col6:
        goal_day = None
        if goal_type == "Spend less on a specific Day":
            goal_day = st.selectbox(
                "Select Day of the Week",
                ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            )

    if st.button("Check Goal Feasibility"):
        explanation, checkpoints = check_goal_feasibility(
            goal_type,
            goal_amount,
            goal_time_months,
            day=goal_day,
            start_date=goal_start_date
        )
        st.write(explanation)
        if checkpoints is not None:
            st.session_state["goal_checkpoints"] = checkpoints
            st.session_state["goal_reward"] = goal_reward
            st.session_state["reward_given"] = False

    if "goal_checkpoints" in st.session_state:
        st.subheader("Track Your Progress")
        df_cp = st.session_state["goal_checkpoints"]

        for i in range(len(df_cp)):
            row = df_cp.iloc[i]
            current = row.get("Contribution ($)", row.get("Reduction Target ($)", 0))
            cumulative = row.get("Cumulative ($)", current)
            completed = st.checkbox(
                f"{row['Due Date'].date()} — \\${current:,.2f} - \\${cumulative:,.2f}",
                value=row["Completed"],
                key=f"cp_{i}"
            )
            st.session_state["goal_checkpoints"].at[i, "Completed"] = completed

        if st.session_state["goal_checkpoints"]["Completed"].all() and not st.session_state["reward_given"]:
            st.session_state["reward_given"] = True
            st.success("Goal Completed!")
            st.balloons() 
            st.markdown(f"## Reward Unlocked: {st.session_state['goal_reward']}")


# chatbot tab
with tabs[3]:

    col1, col2 = st.columns([2, 10], gap="small")  # smallest gap possible

    with col1:
        st.image("gm.jpg", width=100)
    with col2:
        st.markdown(
            "<h1 style='margin:0; padding:0;'>Penny the Monkey 🐵</h1>",
            unsafe_allow_html=True
    )
    if "client" not in st.session_state:
        st.session_state.client = genai.Client()

    if "chat" not in st.session_state:
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config={
                "system_instruction":
                "You are Penny the Monkey 🐵, a friendly financial guide.",
                "temperature": 0.7
            }
        )

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hi! I'm Penny the Monkey 🐵💰 I'm here to help you."
        }]

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            avatar = "🐵" if msg["role"] == "assistant" else "👩‍💻"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    prompt = st.chat_input("Ask Penny about money 💰")

    if prompt:
        with chat_container:
            with st.chat_message("user", avatar="👩‍💻"):
                st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("assistant", avatar="🐵"):
                placeholder = st.empty()
                full_response = ""
                for chunk in st.session_state.chat.send_message_stream(prompt):
                    full_response += chunk.text
                    placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})