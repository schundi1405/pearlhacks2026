import pandas as pd

CSV_FILE = "sample_data _sheet1.csv"

def add_transaction(date, amount, category, t_type):
    # Load existing data
    df = pd.read_csv(CSV_FILE, parse_dates=['date'])
    
    # Create new row
    new_row = pd.DataFrame({
        'date': [pd.to_datetime(date)],
        'amount': [float(amount)],
        'category': [category],
        'type': [t_type]
    })
    
    # Append and sort
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)
    
    # Save back
    df.to_csv(CSV_FILE, index=False)
    
    return df