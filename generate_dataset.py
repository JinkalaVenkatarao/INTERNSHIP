"""
Project 1: Retail Sales Performance Analysis
Dataset Generator - Creates a realistic 2-year retail dataset
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# ── Configuration ─────────────────────────────────────────────────────────────
CATEGORIES    = ['Electronics', 'Clothing', 'Food & Grocery', 'Home & Living', 'Sports & Fitness', 'Beauty & Personal Care']
REGIONS       = ['North', 'South', 'East', 'West', 'Central']
SALES_REPS    = [f'Rep_{i:02d}' for i in range(1, 21)]  # 20 reps
PAYMENT_MODES = ['Credit Card', 'Debit Card', 'UPI', 'Cash', 'Net Banking']

CATEGORY_BASE_PRICE = {
    'Electronics':            {'min': 3000,  'max': 85000, 'margin': 0.18},
    'Clothing':               {'min': 299,   'max': 8000,  'margin': 0.42},
    'Food & Grocery':         {'min': 50,    'max': 2500,  'margin': 0.22},
    'Home & Living':          {'min': 500,   'max': 25000, 'margin': 0.35},
    'Sports & Fitness':       {'min': 800,   'max': 30000, 'margin': 0.30},
    'Beauty & Personal Care': {'min': 150,   'max': 5000,  'margin': 0.48},
}

REGION_MULTIPLIER = {'North': 1.15, 'South': 0.95, 'East': 1.05, 'West': 1.20, 'Central': 1.00}

# ── Date range: Jan 2023 – Dec 2024 ─────────────────────────────────────────
start_date = datetime(2023, 1, 1)
end_date   = datetime(2024, 12, 31)
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

records = []
order_id = 1000

for date in date_range:
    # Seasonal multiplier: higher in Oct-Dec (festival) and Jun-Jul (summer)
    month = date.month
    if month in [10, 11, 12]:
        daily_orders = np.random.poisson(22)   # Festival season
    elif month in [6, 7]:
        daily_orders = np.random.poisson(16)   # Summer sale
    elif month in [1, 2]:
        daily_orders = np.random.poisson(10)   # Post-festival slow
    else:
        daily_orders = np.random.poisson(14)   # Normal

    # Weekends get 40% more orders
    if date.weekday() >= 5:
        daily_orders = int(daily_orders * 1.4)

    for _ in range(max(1, daily_orders)):
        category = random.choices(
            CATEGORIES,
            weights=[20, 18, 25, 14, 12, 11],  # Food most frequent
            k=1
        )[0]
        region   = random.choices(REGIONS, weights=[22, 18, 20, 25, 15], k=1)[0]
        rep      = random.choice(SALES_REPS)
        payment  = random.choices(PAYMENT_MODES, weights=[30, 20, 35, 10, 5], k=1)[0]

        cp = CATEGORY_BASE_PRICE[category]
        unit_price = round(np.random.uniform(cp['min'], cp['max']), 2)

        # Seasonal price boost
        if month in [10, 11, 12] and category == 'Electronics':
            unit_price *= np.random.uniform(1.05, 1.20)

        unit_price = round(unit_price * REGION_MULTIPLIER[region], 2)
        quantity   = int(np.random.choice([1,1,1,2,2,3,4,5], p=[0.35,0.25,0.15,0.10,0.07,0.04,0.02,0.02]))
        discount_pct = round(np.random.choice([0,0,0,5,10,15,20,25], p=[0.35,0.15,0.10,0.15,0.10,0.07,0.05,0.03]), 1)

        revenue   = round(unit_price * quantity * (1 - discount_pct/100), 2)
        cost      = round(revenue * (1 - cp['margin']), 2)
        profit    = round(revenue - cost, 2)

        # Customer age segment
        age_segment = random.choices(
            ['18-25', '26-35', '36-45', '46-55', '55+'],
            weights=[15, 30, 28, 17, 10], k=1
        )[0]

        # Return flag (3% return rate, higher for Electronics)
        return_rate = 0.06 if category == 'Electronics' else 0.03
        returned = random.random() < return_rate

        records.append({
            'order_id':      f'ORD-{order_id:05d}',
            'date':          date.strftime('%Y-%m-%d'),
            'year':          date.year,
            'month':         date.month,
            'month_name':    date.strftime('%b'),
            'quarter':       f'Q{(month-1)//3+1}',
            'weekday':       date.strftime('%A'),
            'category':      category,
            'region':        region,
            'sales_rep':     rep,
            'payment_mode':  payment,
            'unit_price':    unit_price,
            'quantity':      quantity,
            'discount_pct':  discount_pct,
            'revenue':       revenue,
            'cost':          cost,
            'profit':        profit,
            'profit_margin': round(profit / revenue * 100, 2) if revenue > 0 else 0,
            'age_segment':   age_segment,
            'returned':      returned,
        })
        order_id += 1

df = pd.DataFrame(records)
df.to_csv('/home/claude/project1/data/retail_sales_data.csv', index=False)
print(f"✅ Dataset created: {len(df):,} records")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
print(f"   Total Revenue: ₹{df['revenue'].sum():,.2f}")
print(f"   Total Profit:  ₹{df['profit'].sum():,.2f}")
print(f"   Categories: {df['category'].nunique()}")
print(f"   Regions: {df['region'].nunique()}")
print(df.head(3))
