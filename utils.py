# utils.py
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

CSV_FILE = "sample_data_sheet1.csv"

# -------------------------
# Transactions
# -------------------------
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


# -------------------------
# Monthly Checkpoints
# -------------------------
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


# -------------------------
# Spend Less on Specific Day Checkpoints
# -------------------------
def generate_daily_reduction_checkpoints(goal_amount, months, day, start_date):
    """
    Generate checkpoints for each occurrence of a weekday over the timeframe,
    including cumulative contribution.
    """
    dates = []
    current_date = pd.to_datetime(start_date)
    weekday_map = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekday_num = weekday_map.index(day)

    # Approx 4 occurrences per month
    for _ in range(months * 4):
        delta_days = (weekday_num - current_date.weekday() + 7) % 7
        if delta_days == 0:
            delta_days = 7
        current_date = current_date + pd.Timedelta(days=delta_days)
        dates.append(current_date)
        current_date = current_date + pd.Timedelta(days=1)  # move past the current day

    contributions = [goal_amount]*len(dates)
    cumulative = pd.Series(contributions).cumsum()

    checkpoints = pd.DataFrame({
        "Due Date": dates,
        "Reduction Target ($)": contributions,
        "Cumulative ($)": cumulative,
        "Completed": [False]*len(dates)
    })
    return checkpoints


# -------------------------
# Check Goal Feasibility
# -------------------------
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

    # Save Money Goal
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

    # Spend Less on Day Goal
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