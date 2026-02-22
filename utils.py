# utils.py
import pandas as pd

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
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_avg["weekday"] = pd.Categorical(weekday_avg["weekday"], categories=weekday_order, ordered=True)
    weekday_avg = weekday_avg.sort_values("weekday")
    max_day = weekday_avg.loc[weekday_avg["amount"].idxmax()]
    min_day = weekday_avg.loc[weekday_avg["amount"].idxmin()]
    return weekday_avg, max_day, min_day

def check_goal_feasibility(goal_type, goal_amount, months, category=None, day=None):
    """
    Returns:
        explanation: string explaining feasibility
        checkpoints: DataFrame with targets if feasible, else None
    """
    df = load_transactions()
    if df.empty:
        return "No transaction data to evaluate.", None

    # signed amounts for net calculations
    df['signed_amount'] = df.apply(lambda r: r['amount'] if r['type']=="income" else -r['amount'], axis=1)
    df = df.sort_values("date")
    df['month'] = df['date'].dt.to_period("M")
    feasible = False
    checkpoints = None

    if goal_type == "Save X amount of Money":
        monthly_net = df.groupby("month")['signed_amount'].sum().mean()
        monthly_target = goal_amount / months
        feasible = monthly_target <= monthly_net
        explanation = (
            f"You need to save ${monthly_target:.2f} per month. "
            f"Average net income per month: ${monthly_net:.2f}. "
            f"{'This goal is feasible ✅' if feasible else 'This goal is NOT feasible ❌'}"
        )
        if feasible:
            monthly_target_rounded = int(round(monthly_target))
            checkpoints = pd.DataFrame({
                "Month": [f"Month {i+1}" for i in range(months)],
                "Monthly Savings ($)": [monthly_target_rounded for _ in range(months)],
                "Total Savings ($)": [monthly_target_rounded*(i+1) for i in range(months)]
            })

    elif goal_type == "Spend less on a specific Category":
        cat_exp = df[df['category']==category]
        if cat_exp.empty:
            return f"No historical data for category '{category}'", None
        monthly_avg = cat_exp.groupby("month")['amount'].sum().mean()
        monthly_target = max(0, monthly_avg - goal_amount)
        feasible = monthly_target >= 0
        explanation = (
            f"Average spending on {category}: ${monthly_avg:.2f} per month. "
            f"Target per month: ${monthly_target:.2f}. "
            f"{'This goal is feasible ✅' if feasible else 'This goal is NOT feasible ❌'}"
        )
        if feasible:
            monthly_target_rounded = int(round(monthly_target))
            checkpoints = pd.DataFrame({
                "Month": [f"Month {i+1}" for i in range(months)],
                f"Target Spending on {category} ($)": [monthly_target_rounded for _ in range(months)],
                f"Cumulative Spending ($)": [monthly_target_rounded*(i+1) for _ in range(months)]
            })

    elif goal_type == "Spend less on a specific Day":
        df['weekday'] = df['date'].dt.day_name()
        day_exp = df[(df['weekday']==day) & (df['type']=="expense")]
        if day_exp.empty:
            return f"No historical data for {day}s", None
        daily_avg = day_exp['amount'].mean()
        daily_target = max(0, daily_avg - goal_amount)
        feasible = daily_target >= 0
        explanation = (
            f"Average spending on {day}: ${daily_avg:.2f}. "
            f"Target per {day}: ${daily_target:.2f}. "
            f"{'This goal is feasible ✅' if feasible else 'This goal is NOT feasible ❌'}"
        )
        if feasible:
            daily_target_rounded = int(round(daily_target))
            checkpoints = pd.DataFrame({
                "Week": [f"Week {i+1}" for i in range(months*4)],
                f"Target Spending on {day} ($)": [daily_target_rounded for _ in range(months*4)],
                f"Cumulative Spending ($)": [daily_target_rounded*(i+1) for _ in range(months*4)]
            })

    elif goal_type == "Budget/save more for a Category":
        cat_exp = df[df['category']==category]
        monthly_avg = cat_exp.groupby("month")['amount'].sum().mean() if not cat_exp.empty else 0
        monthly_target = monthly_avg + goal_amount/months
        feasible = True  # always mathematically possible
        explanation = (
            f"You want to increase your budget for {category} by ${goal_amount:.2f} over {months} months. "
            f"Monthly target: ${monthly_target:.2f}. This goal is feasible ✅"
        )
        monthly_target_rounded = int(round(monthly_target))
        checkpoints = pd.DataFrame({
            "Month": [f"Month {i+1}" for i in range(months)],
            f"Monthly Budget for {category} ($)": [monthly_target_rounded for _ in range(months)],
            f"Cumulative Budget ($)": [monthly_target_rounded*(i+1) for _ in range(months)]
        })

    else:
        return "Unknown goal type.", None

    return explanation, checkpoints