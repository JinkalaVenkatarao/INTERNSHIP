"""
Project 1: Retail Sales Performance Analysis
Visualization Engine - Generates all 8 charts
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Global Style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':       'DejaVu Sans',
    'font.size':         11,
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.grid':         True,
    'grid.alpha':        0.3,
    'grid.linestyle':    '--',
    'figure.facecolor':  '#FAFAFA',
    'axes.facecolor':    '#FAFAFA',
})

PALETTE     = ['#1B4F72','#2E86C1','#85C1E9','#1E8449','#27AE60','#82E0AA']
CAT_COLORS  = {'Electronics':'#1B4F72','Clothing':'#E74C3C','Food & Grocery':'#27AE60',
               'Home & Living':'#F39C12','Sports & Fitness':'#8E44AD','Beauty & Personal Care':'#E91E8C'}
REG_COLORS  = {'North':'#2E86C1','South':'#E74C3C','East':'#27AE60','West':'#F39C12','Central':'#8E44AD'}
OUTDIR      = '/home/claude/project1/visualizations/'

def crore(x, _=None):
    return f'₹{x/1e7:.1f}Cr'

def lakh(x, _=None):
    return f'₹{x/1e5:.0f}L'

# ── Load Data ─────────────────────────────────────────────────────────────────
df = pd.read_csv('/home/claude/project1/data/retail_sales_data.csv', parse_dates=['date'])
df['month_year'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
print(f"Loaded {len(df):,} records")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 1: Monthly Revenue & Profit Trend (dual-axis line chart)
# ═══════════════════════════════════════════════════════════════════════════════
monthly = df.groupby(['year','month']).agg(revenue=('revenue','sum'), profit=('profit','sum'), orders=('order_id','count')).reset_index()
monthly['label'] = monthly.apply(lambda r: f"{int(r.year)}-{int(r.month):02d}", axis=1)

fig, ax1 = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#FAFAFA')

ax2 = ax1.twinx()
ax2.spines['top'].set_visible(False)

x = range(len(monthly))
ax1.fill_between(x, monthly['revenue']/1e7, alpha=0.2, color='#2E86C1')
ax1.plot(x, monthly['revenue']/1e7, 'o-', color='#1B4F72', linewidth=2.5, markersize=5, label='Revenue (Cr)')
ax2.plot(x, monthly['profit']/1e7, 's--', color='#27AE60', linewidth=2.5, markersize=5, label='Profit (Cr)')

# Shade festival season
for yr_offset in [0, 12]:
    ax1.axvspan(yr_offset+9, yr_offset+11.9, alpha=0.08, color='#F39C12', label='Festival Season' if yr_offset==0 else '')

ax1.set_xticks(list(x))
ax1.set_xticklabels(monthly['label'], rotation=45, ha='right', fontsize=9)
ax1.yaxis.set_major_formatter(FuncFormatter(crore))
ax2.yaxis.set_major_formatter(FuncFormatter(crore))
ax1.set_ylabel('Monthly Revenue', color='#1B4F72', fontweight='bold')
ax2.set_ylabel('Monthly Profit', color='#27AE60', fontweight='bold')
ax1.tick_params(axis='y', colors='#1B4F72')
ax2.tick_params(axis='y', colors='#27AE60')

lines1, labs1 = ax1.get_legend_handles_labels()
lines2, labs2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labs1+labs2, loc='upper left', framealpha=0.9)

ax1.set_title('Monthly Revenue & Profit Trend (Jan 2023 – Dec 2024)', fontsize=15, fontweight='bold', pad=15, color='#1B4F72')
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz1_monthly_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 1 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 2: Category Performance - Grouped Bar (Revenue + Profit Margin)
# ═══════════════════════════════════════════════════════════════════════════════
cat_stats = df.groupby('category').agg(
    revenue=('revenue','sum'),
    profit=('profit','sum'),
    orders=('order_id','count'),
    avg_margin=('profit_margin','mean')
).reset_index().sort_values('revenue', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('#FAFAFA')

# Left: Revenue bar
colors = [CAT_COLORS[c] for c in cat_stats['category']]
bars = axes[0].barh(cat_stats['category'], cat_stats['revenue']/1e7, color=colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, cat_stats['revenue']/1e7):
    axes[0].text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2, f'₹{val:.1f}Cr', va='center', fontsize=10, fontweight='bold')
axes[0].set_xlabel('Total Revenue (Crores)', fontweight='bold')
axes[0].set_title('Revenue by Category', fontsize=13, fontweight='bold', color='#1B4F72')
axes[0].invert_yaxis()

# Right: Profit Margin donut-style bar
colors2 = [CAT_COLORS[c] for c in cat_stats['category']]
bars2 = axes[1].barh(cat_stats['category'], cat_stats['avg_margin'], color=colors2, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars2, cat_stats['avg_margin']):
    axes[1].text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2, f'{val:.1f}%', va='center', fontsize=10, fontweight='bold')
axes[1].set_xlabel('Average Profit Margin (%)', fontweight='bold')
axes[1].set_title('Profit Margin by Category', fontsize=13, fontweight='bold', color='#1B4F72')
axes[1].invert_yaxis()
axes[1].axvline(cat_stats['avg_margin'].mean(), color='red', linestyle='--', alpha=0.6, label=f'Avg: {cat_stats["avg_margin"].mean():.1f}%')
axes[1].legend(fontsize=9)

fig.suptitle('Category-wise Sales Performance', fontsize=15, fontweight='bold', color='#1B4F72', y=1.01)
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz2_category_performance.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 2 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 3: Regional Heatmap - Category × Region Revenue
# ═══════════════════════════════════════════════════════════════════════════════
pivot = df.pivot_table(values='revenue', index='category', columns='region', aggfunc='sum') / 1e7

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#FAFAFA')
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
            linewidths=0.5, linecolor='white',
            annot_kws={'size':11, 'weight':'bold'},
            cbar_kws={'label':'Revenue (Crores ₹)'})
ax.set_title('Revenue Heatmap: Category × Region (₹ Crores)', fontsize=14, fontweight='bold', pad=15, color='#1B4F72')
ax.set_xlabel('Region', fontweight='bold')
ax.set_ylabel('Category', fontweight='bold')
ax.tick_params(axis='x', labelsize=11)
ax.tick_params(axis='y', labelsize=10, rotation=0)
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz3_regional_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 3 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 4: Year-over-Year Quarterly Comparison (stacked/grouped bar)
# ═══════════════════════════════════════════════════════════════════════════════
qtr = df.groupby(['year','quarter']).agg(revenue=('revenue','sum'), profit=('profit','sum')).reset_index()
q2023 = qtr[qtr['year']==2023].set_index('quarter')['revenue']/1e7
q2024 = qtr[qtr['year']==2024].set_index('quarter')['revenue']/1e7
quarters = ['Q1','Q2','Q3','Q4']
x = np.arange(len(quarters))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#FAFAFA')
b1 = ax.bar(x - width/2, [q2023.get(q, 0) for q in quarters], width, label='2023', color='#2E86C1', edgecolor='white', linewidth=0.5)
b2 = ax.bar(x + width/2, [q2024.get(q, 0) for q in quarters], width, label='2024', color='#27AE60', edgecolor='white', linewidth=0.5)

for bar in b1:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2, f'₹{bar.get_height():.1f}Cr', ha='center', fontsize=9, fontweight='bold', color='#1B4F72')
for bar in b2:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2, f'₹{bar.get_height():.1f}Cr', ha='center', fontsize=9, fontweight='bold', color='#1E5631')

# Growth annotations
for i, q in enumerate(quarters):
    v23 = q2023.get(q, 0); v24 = q2024.get(q, 0)
    if v23 > 0:
        growth = ((v24-v23)/v23)*100
        arrow_color = '#27AE60' if growth >= 0 else '#E74C3C'
        ax.annotate(f'{growth:+.1f}%', xy=(i, max(v23,v24)+1.5), ha='center', fontsize=10, color=arrow_color, fontweight='bold')

ax.set_xticks(x); ax.set_xticklabels(quarters, fontsize=12)
ax.yaxis.set_major_formatter(FuncFormatter(crore))
ax.set_ylabel('Revenue (Crores)', fontweight='bold')
ax.set_title('Year-over-Year Quarterly Revenue Comparison', fontsize=14, fontweight='bold', color='#1B4F72', pad=15)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz4_yoy_quarterly.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 4 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 5: Payment Mode Distribution + Age Segment (side-by-side pie/donut)
# ═══════════════════════════════════════════════════════════════════════════════
pay_rev  = df.groupby('payment_mode')['revenue'].sum().sort_values(ascending=False)
age_rev  = df.groupby('age_segment')['revenue'].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.patch.set_facecolor('#FAFAFA')

pay_colors = ['#1B4F72','#2E86C1','#85C1E9','#27AE60','#82E0AA']
wedges, texts, autotexts = axes[0].pie(
    pay_rev.values, labels=pay_rev.index, autopct='%1.1f%%',
    colors=pay_colors, startangle=90,
    wedgeprops={'edgecolor':'white','linewidth':2},
    textprops={'fontsize':10})
for at in autotexts: at.set_fontweight('bold')
axes[0].set_title('Revenue by Payment Mode', fontsize=13, fontweight='bold', color='#1B4F72', pad=10)

# Donut for age segment
age_colors = ['#E74C3C','#F39C12','#27AE60','#2E86C1','#8E44AD']
wedges2, texts2, autotexts2 = axes[1].pie(
    age_rev.values, labels=age_rev.index, autopct='%1.1f%%',
    colors=age_colors, startangle=90,
    wedgeprops={'edgecolor':'white','linewidth':2,'width':0.6},
    textprops={'fontsize':10})
for at in autotexts2: at.set_fontweight('bold')
axes[1].set_title('Revenue by Customer Age Segment', fontsize=13, fontweight='bold', color='#1B4F72', pad=10)

fig.suptitle('Customer & Payment Segmentation', fontsize=15, fontweight='bold', color='#1B4F72')
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz5_payment_age_segments.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 5 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 6: Discount vs Revenue Scatter + Correlation
# ═══════════════════════════════════════════════════════════════════════════════
sample = df.sample(min(2000, len(df)), random_state=42)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('#FAFAFA')

# Scatter colored by category
for cat, grp in sample.groupby('category'):
    axes[0].scatter(grp['discount_pct'], grp['revenue']/1000, alpha=0.4, s=20,
                    color=CAT_COLORS[cat], label=cat)
axes[0].set_xlabel('Discount (%)', fontweight='bold')
axes[0].set_ylabel('Revenue (₹ Thousands)', fontweight='bold')
axes[0].set_title('Discount % vs Revenue by Category', fontsize=12, fontweight='bold', color='#1B4F72')
axes[0].legend(fontsize=7, ncol=2)

# Correlation heatmap of numeric columns
corr_cols = ['unit_price','quantity','discount_pct','revenue','profit','profit_margin']
corr = df[corr_cols].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', ax=axes[1],
            mask=mask, vmin=-1, vmax=1, center=0,
            annot_kws={'size':10}, linewidths=0.5,
            cbar_kws={'shrink':0.8})
axes[1].set_title('Correlation Matrix (Key Metrics)', fontsize=12, fontweight='bold', color='#1B4F72')
axes[1].tick_params(axis='x', rotation=30, labelsize=9)
axes[1].tick_params(axis='y', rotation=0, labelsize=9)

fig.suptitle('Statistical Correlation Analysis', fontsize=15, fontweight='bold', color='#1B4F72')
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz6_correlation_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 6 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 7: Top 10 Sales Reps Performance (horizontal bar + sparkline overlay)
# ═══════════════════════════════════════════════════════════════════════════════
rep_stats = df.groupby('sales_rep').agg(
    revenue=('revenue','sum'), profit=('profit','sum'),
    orders=('order_id','count'), margin=('profit_margin','mean')
).reset_index().sort_values('revenue', ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#FAFAFA')

gradient_colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(rep_stats)))
bars = ax.barh(rep_stats['sales_rep'][::-1], rep_stats['revenue'][::-1]/1e5,
               color=gradient_colors, edgecolor='white', linewidth=0.5)

# Annotations
for bar, (_, row) in zip(bars, rep_stats[::-1].iterrows()):
    ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
            f'₹{row.revenue/1e5:.1f}L | {row.orders} orders | {row.margin:.0f}% margin',
            va='center', fontsize=9)

ax.set_xlabel('Total Revenue (Lakhs ₹)', fontweight='bold')
ax.set_title('Top 10 Sales Representatives Performance (2023–2024)', fontsize=13, fontweight='bold', color='#1B4F72', pad=12)
ax.xaxis.set_major_formatter(FuncFormatter(lakh))
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz7_top_sales_reps.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 7 saved")

# ═══════════════════════════════════════════════════════════════════════════════
# VIZ 8: Weekday Sales Pattern + Return Rate Analysis
# ═══════════════════════════════════════════════════════════════════════════════
day_order  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
day_stats  = df.groupby('weekday').agg(revenue=('revenue','sum'), orders=('order_id','count')).reindex(day_order)
ret_stats  = df.groupby('category')['returned'].mean() * 100

fig, axes  = plt.subplots(1, 2, figsize=(13, 5))
fig.patch.set_facecolor('#FAFAFA')

# Weekday revenue bars
bar_colors = ['#85C1E9','#85C1E9','#85C1E9','#85C1E9','#85C1E9','#1B4F72','#1B4F72']
bars = axes[0].bar(day_order, day_stats['revenue']/1e7, color=bar_colors, edgecolor='white', linewidth=0.5)
axes[0].set_xlabel('Day of Week', fontweight='bold')
axes[0].yaxis.set_major_formatter(FuncFormatter(crore))
axes[0].set_ylabel('Total Revenue', fontweight='bold')
axes[0].set_title('Revenue by Day of Week', fontsize=12, fontweight='bold', color='#1B4F72')
axes[0].tick_params(axis='x', rotation=30, labelsize=9)
for bar in bars:
    axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                 f'₹{bar.get_height():.1f}Cr', ha='center', fontsize=8, fontweight='bold')
wknd_patch = mpatches.Patch(color='#1B4F72', label='Weekend')
wkdy_patch = mpatches.Patch(color='#85C1E9', label='Weekday')
axes[0].legend(handles=[wknd_patch, wkdy_patch], fontsize=9)

# Return rate by category
ret_colors = [CAT_COLORS[c] for c in ret_stats.index]
bars2 = axes[1].bar(ret_stats.index, ret_stats.values, color=ret_colors, edgecolor='white', linewidth=0.5)
axes[1].axhline(ret_stats.mean(), color='red', linestyle='--', linewidth=1.5, label=f'Avg: {ret_stats.mean():.1f}%')
axes[1].set_xlabel('Category', fontweight='bold')
axes[1].set_ylabel('Return Rate (%)', fontweight='bold')
axes[1].set_title('Product Return Rate by Category', fontsize=12, fontweight='bold', color='#1B4F72')
axes[1].tick_params(axis='x', rotation=20, labelsize=8)
for bar, val in zip(bars2, ret_stats.values):
    axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05, f'{val:.1f}%', ha='center', fontsize=9, fontweight='bold')
axes[1].legend(fontsize=9)

fig.suptitle('Operational Patterns: Weekday Sales & Product Returns', fontsize=14, fontweight='bold', color='#1B4F72')
plt.tight_layout()
plt.savefig(f'{OUTDIR}viz8_weekday_returns.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ VIZ 8 saved")

print("\n🎉 All 8 visualizations created successfully!")
print(f"   Saved to: {OUTDIR}")
