# utils.py
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import streamlit as st

CSV_FILE = "sample_data_sheet1.csv"

def load_transactions():
    df = pd.read_csv(CSV_FILE, parse_dates=['date'])
    return df

def add_transaction(date, amount, category, t_type):
    df = load_transactions()
    new_row = pd.DataFrame({
        'date': [pd.to_datetime(date)],
        'amount': [float(amount)],
        'category': [category],
        'type': [t_type]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)
    df.to_csv(CSV_FILE, index=False)
    return df

def spending_by_weekday():
    df = load_transactions()
    if df.empty:
        return None, None, None
    expenses = df[df["type"]=="expense"].copy()
    if expenses.empty:
        return None, None, None
    expenses["amount"] = expenses["amount"].astype(float)
    expenses["weekday"] = expenses["date"].dt.day_name()
    weekday_avg = expenses.groupby("weekday")["amount"].mean().reset_index()
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekday_avg["weekday"] = pd.Categorical(
        weekday_avg["weekday"],
        categories=weekday_order,
        ordered=True
    )
    weekday_avg = weekday_avg.sort_values("weekday")
    max_day = weekday_avg.loc[weekday_avg["amount"].idxmax()]
    min_day = weekday_avg.loc[weekday_avg["amount"].idxmin()]
    return weekday_avg, max_day, min_day



def generate_monthly_checkpoints(goal_amount, months, start_date):
    contribution = round(goal_amount / months, 2)
    dates = []
    current_date = pd.to_datetime(start_date)
    for _ in range(months):
        current_date = current_date + relativedelta(months=1)
        dates.append(current_date)
    checkpoints = pd.DataFrame({
        "Due Date": dates,
        "Contribution ($)": [contribution]*months,
        "Completed": [False]*months
    })
    return checkpoints


def generate_daily_reduction_checkpoints(goal_amount, months, day, start_date):
    """
    Generate checkpoints for each occurrence of a weekday over the timeframe,
    including cumulative contribution.
    """
    dates = []
    current_date = pd.to_datetime(start_date)
    weekday_map = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekday_num = weekday_map.index(day)


    for _ in range(months * 4):
        delta_days = (weekday_num - current_date.weekday() + 7) % 7
        if delta_days == 0:
            delta_days = 7
        current_date = current_date + pd.Timedelta(days=delta_days)
        dates.append(current_date)
        current_date = current_date + pd.Timedelta(days=1) 

    contributions = [goal_amount]*len(dates)
    cumulative = pd.Series(contributions).cumsum()

    checkpoints = pd.DataFrame({
        "Due Date": dates,
        "Reduction Target ($)": contributions,
        "Cumulative ($)": cumulative,
        "Completed": [False]*len(dates)
    })
    return checkpoints


def check_goal_feasibility(goal_type, goal_amount, months,
                           category=None, day=None,
                           start_date=None):
    df = load_transactions()
    if df.empty:
        return "No transaction data to evaluate.", None
    df['signed_amount'] = df.apply(
        lambda r: r['amount'] if r['type']=="income" else -r['amount'], axis=1
    )
    df['month'] = df['date'].dt.to_period("M")


    if goal_type == "Save X amount of Money":
        monthly_net = df.groupby("month")['signed_amount'].sum().mean()
        monthly_target = goal_amount / months
        feasible = monthly_target <= monthly_net
        explanation = (
            f"You need ${monthly_target:.2f} per month. "
            f"Average net income per month: ${monthly_net:.2f}. "
            f"{'Feasible ✅' if feasible else 'Not feasible ❌'}"
        )
        if feasible and start_date is not None:
            checkpoints = generate_monthly_checkpoints(goal_amount, months, start_date)
            return explanation, checkpoints
        return explanation, None


    elif goal_type == "Spend less on a specific Day":
        if day is None:
            return "No day selected.", None

        explanation = (
            f"You want to spend ${goal_amount:.2f} less each {day} "
            f"for {months} month(s)."
        )

        if start_date is not None:
            checkpoints = generate_daily_reduction_checkpoints(
                goal_amount,
                months,
                day,
                start_date
            )
            return explanation, checkpoints

        return explanation, None

    return "Goal type not supported yet.", None

def calculate_financial_health(goal_checkpoints = None):
    """
    Returns:
        score (int): 1-10 score
        summary (str): descriptive explanation of the score
    """
    df = load_transactions()
    if df.empty:
        return 1, "No transactions yet. Unable to evaluate finances."


    goal_completed_ratio = 1.0
    if goal_checkpoints is not None and not goal_checkpoints.empty:
        goal_completed_ratio = goal_checkpoints["Completed"].mean()


    from model import forecast_next_6_months
    actual_df, forecast_df, _ = forecast_next_6_months()
    trend_score = 5
    trend_direction = "steady"
    if forecast_df is not None:
        predicted_balance = forecast_df["predicted_balance"].iloc[-1]
        current_balance = actual_df["cumulative_balance"].iloc[-1]
        change_ratio = (predicted_balance - current_balance) / max(current_balance, 1)
        if change_ratio > 0.1:
            trend_score = 10
            trend_direction = "increasing"
        elif change_ratio > 0:
            trend_score = 8
            trend_direction = "slightly increasing"
        elif change_ratio > -0.1:
            trend_score = 5
            trend_direction = "stable"
        else:
            trend_score = 2
            trend_direction = "decreasing"


    score = int(round(0.5 * (goal_completed_ratio * 10) + 0.5 * trend_score))
    score = max(1, min(score, 10))


    expense_df = df[df["type"] == "expense"].copy()
    category_totals = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    if not category_totals.empty:
        top_category = category_totals.idxmax()
        top_value = category_totals.max()
    else:
        top_category = "N/A"
        top_value = 0


    summary = (
        f"Your financial health is currently {trend_direction}. "
        f"You have completed {goal_completed_ratio*100:.0f}% of your financial goals. "
        f"The largest contributor to spending is '{top_category}' "
        f"(total: ${top_value:.2f})."
    )

    return score, summary