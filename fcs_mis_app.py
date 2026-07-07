"""
Full Circle Studio — MIS Dashboard
Streamlit app for monthly management reporting
Reads Tally Trial Balance + Master exports

Deploy: streamlit run fcs_mis_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io, re
from datetime import datetime

# ─── Page Config ───
st.set_page_config(
    page_title="Full Circle Studio — MIS",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme & Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #1B2A4A 0%, #2E86C1 100%);
        padding: 28px 32px; border-radius: 12px; margin-bottom: 24px; color: white;
    }
    .main-header h1 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.3px; }
    .main-header p { margin: 4px 0 0; font-size: 13px; opacity: 0.8; }
    
    .kpi-card {
        background: white; border-radius: 10px; padding: 18px 20px;
        border-left: 4px solid #2E86C1; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .kpi-label { font-size: 11px; color: #95A5A6; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #2C3E50; }
    .kpi-sub { font-size: 11px; margin-top: 4px; }
    
    .flag-high { color: #E74C3C; font-weight: 700; }
    .flag-medium { color: #F39C12; font-weight: 600; }
    .flag-low { color: #27AE60; }
    
    .section-header {
        display: flex; align-items: center; gap: 8px; margin: 20px 0 12px;
    }
    .section-bar { width: 4px; height: 20px; border-radius: 2px; display: inline-block; }
    
    div[data-testid="stMetric"] { background: white; padding: 16px; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
    
    .stca-footer { text-align: center; padding: 20px 0 8px; color: #95A5A6; font-size: 11px; border-top: 1px solid #E0E0E0; margin-top: 24px; }
</style>
""", unsafe_allow_html=True)

# ─── MIS Category Mapping ───
# Maps Tally groups to MIS reporting categories and statement type
GROUP_MAP = {
    # ── P&L: Revenue ──
    "Revenue from operations":     ("Revenue",            "P&L", "Revenue"),
    "Direct Incomes":              ("Other Operating Income", "P&L", "Revenue"),
    "Other direct income":         ("Other Operating Income", "P&L", "Revenue"),
    "Indirect Incomes":            ("Other Income",       "P&L", "Revenue"),
    
    # ── P&L: Cost of Revenue ──
    "Direct Expenses":             ("Direct Costs",       "P&L", "COGS"),
    "Purchase Accounts":           ("Purchases",          "P&L", "COGS"),
    
    # ── P&L: Operating Expenses ──
    "Employee costs":              ("Employee Costs",     "P&L", "OpEx"),
    "Facility and rental cost":    ("Rent & Facility",    "P&L", "OpEx"),
    "Professional and consultancy fees": ("Professional Fees", "P&L", "OpEx"),
    "Selling and distribution expense": ("Selling & Distribution", "P&L", "OpEx"),
    "Travelling, boarding and lodging": ("Travel & Lodging", "P&L", "OpEx"),
    "Communication costs":         ("Communication",      "P&L", "OpEx"),
    "Power and fuel":              ("Power & Fuel",       "P&L", "OpEx"),
    "Insurance expense":           ("Insurance",          "P&L", "OpEx"),
    "Repairs and maintenance":     ("Repairs & Maintenance", "P&L", "OpEx"),
    "Miscellaneous expenses":      ("Miscellaneous",      "P&L", "OpEx"),
    "Office Expenses":             ("Office Expenses",    "P&L", "OpEx"),
    "Indirect Expenses":           ("Other Indirect Expenses", "P&L", "OpEx"),
    "Reimbursements":              ("Reimbursements",     "P&L", "OpEx"),
    
    # ── P&L: Below EBITDA ──
    "Finance costs":               ("Finance Costs",      "P&L", "Finance"),
    "Tax expense":                 ("Tax Expense",        "P&L", "Tax"),
    
    # ── BS: Equity ──
    "Share capital":               ("Share Capital",      "BS", "Equity"),
    "Reserves & Surplus":          ("Reserves & Surplus", "BS", "Equity"),
    
    # ── BS: Borrowings ──
    "Debentures":                  ("Debentures",         "BS", "Borrowings"),
    "Loans (Liability)":           ("Other Loans",        "BS", "Borrowings"),
    "Secured Loans":               ("Secured Loans",      "BS", "Borrowings"),
    "Unsecured Loans":             ("Unsecured Loans",    "BS", "Borrowings"),
    "Loan From Directors":         ("Director Loans",     "BS", "Borrowings"),
    "Loan From Relatives":         ("Related Party Loans", "BS", "Borrowings"),
    
    # ── BS: Current Liabilities ──
    "Sundry Creditors":            ("Trade Payables",     "BS", "CL"),
    "Current Liabilities":         ("Other Current Liabilities", "BS", "CL"),
    "Other current liabilities":   ("Other Current Liabilities", "BS", "CL"),
    "Provisions":                  ("Provisions",         "BS", "CL"),
    "Amounts payable to employees":("Employee Payables",  "BS", "CL"),
    "GST Ledgers":                 ("GST Payable",        "BS", "CL"),
    "TDS Ledgers":                 ("TDS Receivable",     "BS", "CA"),  # TDS is an asset
    "ESI":                         ("ESI Payable",        "BS", "CL"),
    "PF":                          ("PF Payable",         "BS", "CL"),
    "Labour welfare fund":         ("LWF Payable",        "BS", "CL"),
    "Professional Tax":            ("Prof Tax Payable",   "BS", "CL"),
    
    # ── BS: Fixed Assets ──
    "Property, plant and equipment": ("PPE",              "BS", "FA"),
    "Intangible assets":           ("Intangible Assets",  "BS", "FA"),
    "Fixed Assets":                ("Other Fixed Assets", "BS", "FA"),
    
    # ── BS: Current Assets ──
    "Balance with banks":          ("Bank Balances",      "BS", "CA"),
    "Other deposit with banks":    ("Bank Deposits",      "BS", "CA"),
    "Cash-in-Hand":                ("Cash",               "BS", "CA"),
    "Sundry Debtors":              ("Trade Receivables",  "BS", "CA"),
    "Trade receivables":           ("Trade Receivables",  "BS", "CA"),
    "Deposits (Asset)":            ("Security Deposits",  "BS", "CA"),
    "Loans & Advances (Asset)":    ("Loans & Advances",   "BS", "CA"),
    "Capital Advances":            ("Capital Advances",   "BS", "CA"),
    "Current Assets":              ("Other Current Assets","BS", "CA"),
    "Prepaid expenses":            ("Prepaid Expenses",   "BS", "CA"),
    "Inventory":                   ("Inventory",          "BS", "CA"),
    "Investments":                 ("Investments",        "BS", "CA"),
    "Balances with government authorities": ("Statutory Receivables", "BS", "CA"),
    "Suspense A/c":                ("Suspense",           "BS", "CA"),
    
    # ── Catch-all ──
    "_x0004_ Primary":             ("Unmapped",           "BS", "CA"),
}


# ─── Helper Functions ───

def fmt_inr(val, show_sign=False):
    """Format number as INR with lakhs/crores."""
    if pd.isna(val) or val == 0:
        return "—"
    prefix = "" if not show_sign else ("+" if val > 0 else "")
    abs_val = abs(val)
    if abs_val >= 1e7:
        return f"{prefix}₹{val/1e7:,.2f} Cr"
    if abs_val >= 1e5:
        return f"{prefix}₹{val/1e5:,.2f} L"
    return f"{prefix}₹{val:,.0f}"

def fmt_inr_table(val):
    """Format for table display — parentheses for negatives."""
    if pd.isna(val) or val == 0:
        return "—"
    if val < 0:
        return f"(₹{abs(val):,.0f})"
    return f"₹{val:,.0f}"

def parse_tally_tb(file):
    """Parse Tally Trial Balance export into a clean DataFrame."""
    df = pd.read_excel(file, header=None)
    
    # Find the header row (contains 'Particulars')
    header_row = None
    for i, row in df.iterrows():
        if any(str(v).strip() == 'Particulars' for v in row.values if pd.notna(v)):
            header_row = i
            break
    
    # Find period from the rows above
    period = ""
    for i in range(min(header_row or 5, 10)):
        val = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ""
        if "to" in val.lower() and any(c.isdigit() for c in val):
            period = val.strip()
            break
    
    # Data starts 2 rows after Particulars (skip the Dr/Cr sub-header)
    data_start = header_row + 2 if header_row is not None else 9
    
    tb = df.iloc[data_start:].copy()
    tb.columns = range(len(tb.columns))
    
    # Handle 5-column format: Particulars | Opening | Debit | Credit | Closing
    if len(tb.columns) >= 5:
        tb = tb[[0, 1, 2, 3, 4]]
        tb.columns = ['ledger', 'opening', 'debit', 'credit', 'closing']
    else:
        st.error("Unexpected TB format. Expected 5 columns.")
        return None, period
    
    tb = tb.dropna(subset=['ledger'])
    tb = tb[~tb['ledger'].astype(str).str.contains('Grand Total|Total', case=False, na=False)]
    
    for col in ['opening', 'debit', 'credit', 'closing']:
        tb[col] = pd.to_numeric(tb[col], errors='coerce').fillna(0)
    
    tb['ledger'] = tb['ledger'].astype(str).str.strip()
    
    return tb, period

def parse_tally_master(file):
    """Parse Tally List of Ledgers export."""
    df = pd.read_excel(file, header=None)
    
    # Find header row (contains 'Name of Ledger')
    header_row = None
    for i, row in df.iterrows():
        row_str = ' '.join(str(v) for v in row.values if pd.notna(v))
        if 'Name of Ledger' in row_str or 'Ledger' in row_str:
            header_row = i
            break
    
    data_start = (header_row + 1) if header_row is not None else 6
    ms = df.iloc[data_start:].copy()
    ms.columns = range(len(ms.columns))
    
    if len(ms.columns) >= 3:
        ms = ms[[1, 2]]
        ms.columns = ['ledger', 'group']
    
    ms = ms.dropna(subset=['ledger'])
    ms['ledger'] = ms['ledger'].astype(str).str.strip()
    ms['group'] = ms['group'].astype(str).str.strip()
    
    return ms

def build_mis(tb, master):
    """Merge TB with Master and apply MIS mapping."""
    merged = tb.merge(master[['ledger', 'group']], on='ledger', how='left')
    
    # Apply MIS mapping
    merged['mis_category'] = merged['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped", "BS", "CA"))[0])
    merged['statement'] = merged['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped", "BS", "CA"))[1])
    merged['section'] = merged['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped", "BS", "CA"))[2])
    
    # P&L: net transaction = Debit - Credit for expenses, Credit - Debit for income
    # In Tally TB: expenses have debit closing, income has credit closing
    # For P&L items, the "amount" is the net transaction activity
    merged['pl_amount'] = 0.0
    merged['bs_amount'] = 0.0
    
    pl_mask = merged['statement'] == 'P&L'
    bs_mask = merged['statement'] == 'BS'
    
    # P&L: Revenue items = Credit - Debit (positive = income)
    # P&L: Expense items = Debit - Credit (positive = expense)
    rev_mask = pl_mask & merged['section'].isin(['Revenue'])
    exp_mask = pl_mask & ~merged['section'].isin(['Revenue'])
    
    merged.loc[rev_mask, 'pl_amount'] = merged.loc[rev_mask, 'credit'] - merged.loc[rev_mask, 'debit']
    merged.loc[exp_mask, 'pl_amount'] = merged.loc[exp_mask, 'debit'] - merged.loc[exp_mask, 'credit']
    
    # BS: Use closing balance
    # Liabilities & Equity: Credit closing is positive
    # Assets: Debit closing is positive
    # Tally convention: closing is shown as absolute with implied sign from group nature
    # In our export: closing column is positive for debit balances, we need to handle sign
    asset_sections = ['FA', 'CA']
    liab_sections = ['Equity', 'Borrowings', 'CL']
    
    merged.loc[bs_mask & merged['section'].isin(asset_sections), 'bs_amount'] = merged.loc[bs_mask & merged['section'].isin(asset_sections), 'closing']
    merged.loc[bs_mask & merged['section'].isin(liab_sections), 'bs_amount'] = merged.loc[bs_mask & merged['section'].isin(liab_sections), 'closing']
    
    return merged


def generate_flags(mis):
    """Auto-generate flag-off items based on data patterns."""
    flags = []
    
    # Large unverified balances
    large = mis[(mis['bs_amount'].abs() > 100000) & (mis['section'].isin(['CA']))].sort_values('bs_amount', ascending=False)
    for _, r in large.head(5).iterrows():
        flags.append({
            'item': f"{r['ledger']} — {fmt_inr(r['bs_amount'])}",
            'priority': 'HIGH' if abs(r['bs_amount']) > 500000 else 'MEDIUM',
            'category': r['mis_category'],
            'action': 'Obtain supporting documents / breakup'
        })
    
    # Negative creditors (advances)
    neg_cred = mis[(mis['mis_category'] == 'Trade Payables') & (mis['closing'] > 0)]
    for _, r in neg_cred.iterrows():
        flags.append({
            'item': f"{r['ledger']} — Debit balance {fmt_inr(r['closing'])}",
            'priority': 'HIGH',
            'category': 'Trade Payables',
            'action': 'Confirm if advance; reclassify to advances'
        })
    
    # Suspense balances
    susp = mis[mis['mis_category'] == 'Suspense']
    for _, r in susp.iterrows():
        if r['closing'] != 0:
            flags.append({
                'item': f"Suspense balance — {fmt_inr(r['closing'])}",
                'priority': 'HIGH',
                'category': 'Suspense',
                'action': 'Clear before month-end close'
            })
    
    # Unmapped ledgers
    unmapped = mis[mis['mis_category'] == 'Unmapped']
    if len(unmapped) > 0:
        flags.append({
            'item': f"{len(unmapped)} unmapped ledger(s) in TB",
            'priority': 'MEDIUM',
            'category': 'Mapping',
            'action': 'Update group mapping in Master'
        })
    
    return flags


# ─── Sidebar ───
with st.sidebar:
    st.markdown("### 📁 Data Upload")
    
    master_file = st.file_uploader("**Master** (List of Ledgers)", type=['xlsx', 'xls'], key="master")
    tb_file = st.file_uploader("**Trial Balance**", type=['xlsx', 'xls'], key="tb")
    
    st.markdown("---")
    st.markdown("### 📋 Export Format")
    st.markdown("""
    **From Tally → Export:**
    - Gateway → Display → Trial Balance
    - Period: Monthly (standalone)
    - Format: Excel / Spreadsheet
    
    **Master:**
    - Gateway → Display → List of Accounts
    - Export as Excel
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; font-size: 10px; color: #95A5A6;'>
    Prepared by STCA Global<br>
    Chartered Accountants (FRN 016465S)
    </div>
    """, unsafe_allow_html=True)


# ─── Main Content ───
if not master_file or not tb_file:
    st.markdown("""
    <div class='main-header'>
        <h1>Full Circle Studio Private Limited</h1>
        <p>Management Information System — Monthly Reporting Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("👈 Upload the **Master** (List of Ledgers) and **Trial Balance** from the sidebar to generate the MIS.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### What to export from Tally")
        st.markdown("""
        1. **Master** — Gateway → Display → List of Accounts → Export as Excel
        2. **Trial Balance** — Gateway → Display → Trial Balance → Set period → Export as Excel
        """)
    with col2:
        st.markdown("#### Monthly workflow")
        st.markdown("""
        1. Close the month in Tally (pass all entries)
        2. Export standalone monthly TB (e.g., 1-Jul-26 to 31-Jul-26)
        3. Upload here → MIS auto-generates
        4. Review flags → Share with client
        """)
    st.stop()

# ─── Parse uploaded data ───
master = parse_tally_master(master_file)
tb, period = parse_tally_tb(tb_file)

if tb is None:
    st.stop()

mis = build_mis(tb, master)

# ─── Compute key numbers ───
# P&L
revenue = mis[mis['section'] == 'Revenue']['pl_amount'].sum()
cogs = mis[mis['section'] == 'COGS']['pl_amount'].sum()
gross_profit = revenue - cogs
opex = mis[mis['section'] == 'OpEx']['pl_amount'].sum()
ebitda = gross_profit - opex
finance = mis[mis['section'] == 'Finance']['pl_amount'].sum()
tax = mis[mis['section'] == 'Tax']['pl_amount'].sum()
net_pl = ebitda - finance - tax

# BS
equity = mis[mis['section'] == 'Equity']['bs_amount'].sum()
borrowings = mis[mis['section'] == 'Borrowings']['bs_amount'].sum()
cl = mis[mis['section'] == 'CL']['bs_amount'].sum()
fa = mis[mis['section'] == 'FA']['bs_amount'].sum()
ca = mis[mis['section'] == 'CA']['bs_amount'].sum()
net_worth = equity - abs(net_pl) if net_pl < 0 else equity + net_pl  # Simplified
total_liab = abs(equity) + abs(borrowings) + abs(cl)
total_assets = fa + ca

bank = mis[mis['mis_category'] == 'Bank Balances']['bs_amount'].sum()
total_expenses = cogs + opex + finance
burn_rate = total_expenses if total_expenses > 0 else 0
runway = bank / burn_rate if burn_rate > 0 else float('inf')

# ─── Header ───
st.markdown(f"""
<div class='main-header'>
    <h1>Full Circle Studio Private Limited</h1>
    <p>Management Information System &nbsp;•&nbsp; Period: {period}</p>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet", "🔍 Ledger Detail", "🚩 Flag-Off Items"])

# ═══════════════════════════════════════
#  TAB 1: DASHBOARD
# ═══════════════════════════════════════
with tab1:
    if revenue == 0:
        st.warning("🚧 **Pre-Launch Phase** — No revenue recorded. All expenses are pre-operative.")
    
    # KPI Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Revenue", fmt_inr(revenue) if revenue > 0 else "NIL")
    k2.metric("Total Expenses", fmt_inr(total_expenses))
    k3.metric("Net P/L", fmt_inr(-net_pl) if net_pl < 0 else fmt_inr(net_pl), delta=f"{'Loss' if net_pl < 0 else 'Profit'}", delta_color="inverse" if net_pl < 0 else "normal")
    k4.metric("Cash & Bank", fmt_inr(bank))
    k5.metric("Burn Rate / mo", fmt_inr(burn_rate))
    k6.metric("Runway", f"{runway:.1f} months" if runway < 100 else "N/A")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Expense Breakdown
        exp_data = mis[(mis['statement'] == 'P&L') & (mis['section'] != 'Revenue') & (mis['pl_amount'] > 0)]
        exp_by_cat = exp_data.groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False).reset_index()
        exp_by_cat.columns = ['Category', 'Amount']
        
        if len(exp_by_cat) > 0:
            fig_exp = px.pie(exp_by_cat, values='Amount', names='Category',
                           title="Expense Breakdown",
                           color_discrete_sequence=px.colors.qualitative.Set2,
                           hole=0.4)
            fig_exp.update_layout(height=380, margin=dict(t=40, b=20, l=20, r=20),
                                font=dict(family="Inter"), showlegend=True,
                                legend=dict(orientation="h", y=-0.1))
            fig_exp.update_traces(textposition='inside', textinfo='percent+label',
                                textfont_size=11)
            st.plotly_chart(fig_exp, use_container_width=True)
    
    with col2:
        # Funding Structure
        fund_data = mis[mis['section'].isin(['Equity', 'Borrowings'])].copy()
        fund_by_cat = fund_data.groupby('mis_category')['bs_amount'].sum().abs().sort_values(ascending=True).reset_index()
        fund_by_cat.columns = ['Source', 'Amount']
        fund_by_cat = fund_by_cat[fund_by_cat['Amount'] > 0]
        
        if len(fund_by_cat) > 0:
            fig_fund = px.bar(fund_by_cat, x='Amount', y='Source', orientation='h',
                            title="Funding Structure",
                            color_discrete_sequence=['#2E86C1'])
            fig_fund.update_layout(height=380, margin=dict(t=40, b=20, l=20, r=20),
                                 font=dict(family="Inter"), showlegend=False,
                                 xaxis_title="", yaxis_title="")
            fig_fund.update_traces(text=[fmt_inr(v) for v in fund_by_cat['Amount']],
                                 textposition='outside', textfont_size=11)
            st.plotly_chart(fig_fund, use_container_width=True)
    
    # Asset Composition
    asset_data = mis[mis['section'].isin(['FA', 'CA']) & (mis['bs_amount'] > 0)]
    asset_by_cat = asset_data.groupby('mis_category')['bs_amount'].sum().sort_values(ascending=False).reset_index()
    asset_by_cat.columns = ['Asset', 'Amount']
    
    if len(asset_by_cat) > 0:
        fig_asset = px.bar(asset_by_cat, x='Asset', y='Amount',
                          title="Asset Composition",
                          color_discrete_sequence=['#27AE60'])
        fig_asset.update_layout(height=320, margin=dict(t=40, b=20, l=20, r=20),
                              font=dict(family="Inter"), showlegend=False,
                              xaxis_title="", yaxis_title="")
        fig_asset.update_traces(text=[fmt_inr(v) for v in asset_by_cat['Amount']],
                              textposition='outside', textfont_size=11)
        st.plotly_chart(fig_asset, use_container_width=True)
    
    # Key Ratios
    st.markdown("#### Key Ratios")
    r1, r2, r3, r4 = st.columns(4)
    de_ratio = abs(borrowings) / abs(net_worth) if net_worth != 0 else 0
    current_ratio = ca / abs(cl) if cl != 0 else 0
    r1.metric("Debt-Equity Ratio", f"{de_ratio:.1f}x")
    r2.metric("Current Ratio", f"{current_ratio:.1f}x")
    r3.metric("Total Borrowings", fmt_inr(abs(borrowings)))
    r4.metric("Net Worth", fmt_inr(net_worth))


# ═══════════════════════════════════════
#  TAB 2: PROFIT & LOSS
# ═══════════════════════════════════════
with tab2:
    st.markdown("#### Profit & Loss Statement")
    st.caption(f"Period: {period}")
    
    # Build P&L structure
    pl_sections = [
        ("REVENUE", "header", None),
    ]
    
    rev_items = mis[(mis['section'] == 'Revenue') & (mis['pl_amount'] != 0)].groupby('mis_category')['pl_amount'].sum()
    for cat, val in rev_items.items():
        pl_sections.append((f"  {cat}", "item", val))
    pl_sections.append(("Total Revenue", "total", revenue))
    pl_sections.append(("", "spacer", None))
    
    pl_sections.append(("COST OF REVENUE", "header", None))
    cogs_items = mis[(mis['section'] == 'COGS') & (mis['pl_amount'] != 0)].groupby('mis_category')['pl_amount'].sum()
    for cat, val in cogs_items.items():
        pl_sections.append((f"  {cat}", "item", val))
    pl_sections.append(("Total Cost of Revenue", "total", cogs))
    pl_sections.append(("", "spacer", None))
    
    pl_sections.append(("GROSS PROFIT", "grand", gross_profit))
    if revenue > 0:
        pl_sections.append(("  Gross Margin", "pct", gross_profit / revenue))
    pl_sections.append(("", "spacer", None))
    
    pl_sections.append(("OPERATING EXPENSES", "header", None))
    opex_items = mis[(mis['section'] == 'OpEx') & (mis['pl_amount'] != 0)].groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False)
    for cat, val in opex_items.items():
        pct = val / total_expenses * 100 if total_expenses > 0 else 0
        pl_sections.append((f"  {cat}", "item", val, pct))
    pl_sections.append(("Total Operating Expenses", "total", opex))
    pl_sections.append(("", "spacer", None))
    
    pl_sections.append(("EBITDA", "grand", ebitda))
    pl_sections.append(("", "spacer", None))
    
    if finance > 0:
        pl_sections.append(("Finance Costs", "item", finance))
    if tax > 0:
        pl_sections.append(("Tax Expense", "item", tax))
    
    pl_sections.append(("NET PROFIT / (LOSS)", "grand", net_pl if net_pl >= 0 else -abs(net_pl)))
    
    # Render as table
    rows_html = ""
    for entry in pl_sections:
        label = entry[0]
        style = entry[1]
        val = entry[2] if len(entry) > 2 else None
        pct = entry[3] if len(entry) > 3 else None
        
        if style == "spacer":
            rows_html += "<tr><td colspan='3' style='padding:4px;'></td></tr>"
            continue
        
        bg = "#F8F9FA" if style == "total" else ("#D6E4F0" if style == "grand" else "transparent")
        fw = "700" if style in ("total", "grand", "header") else "400"
        color = "#E8833A" if style == "header" else ("#E74C3C" if val is not None and val < 0 else "#2C3E50")
        fs = "11px" if style == "header" else "13px"
        
        val_str = fmt_inr_table(val) if val is not None else ""
        pct_str = f"{pct:.1f}%" if pct else ""
        
        border = "border-bottom: 2px solid #1B2A4A;" if style in ("total", "grand") else "border-bottom: 1px solid #ECF0F1;"
        
        rows_html += f"""
        <tr style='background:{bg};'>
            <td style='padding:8px 14px; font-weight:{fw}; color:{color}; font-size:{fs}; {border}'>{label}</td>
            <td style='text-align:right; padding:8px 14px; font-weight:{fw}; color:{color}; {border}'>{val_str}</td>
            <td style='text-align:right; padding:8px 14px; color:#95A5A6; font-size:12px; {border}'>{pct_str}</td>
        </tr>"""
    
    st.markdown(f"""
    <table style='width:100%; border-collapse:collapse; font-family:Inter,sans-serif;'>
        <thead>
            <tr style='background:#1B2A4A; color:white;'>
                <th style='text-align:left; padding:10px 14px; font-weight:600;'>Particulars</th>
                <th style='text-align:right; padding:10px 14px; font-weight:600;'>Amount (₹)</th>
                <th style='text-align:right; padding:10px 14px; font-weight:600;'>% of Expenses</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════
#  TAB 3: BALANCE SHEET
# ═══════════════════════════════════════
with tab3:
    st.markdown("#### Balance Sheet")
    st.caption(f"As at end of period: {period}")
    
    col_l, col_r = st.columns(2)
    
    def render_bs_section(container, title, sections_list, section_keys):
        with container:
            st.markdown(f"**{title}**")
            grand_total = 0
            
            for sec_key, sec_label in section_keys:
                sec_data = mis[(mis['section'] == sec_key) & (mis['bs_amount'] != 0)]
                if len(sec_data) == 0:
                    continue
                
                sec_by_cat = sec_data.groupby('mis_category')['bs_amount'].sum()
                sec_total = sec_by_cat.sum()
                grand_total += abs(sec_total)
                
                rows = ""
                for cat, val in sec_by_cat.items():
                    display_val = abs(val) if sec_key in ['Equity', 'Borrowings', 'CL'] else val
                    color = "#E74C3C" if val < 0 and sec_key not in ['Equity'] else "#2C3E50"
                    rows += f"<tr><td style='padding:5px 10px;'>{cat}</td><td style='text-align:right; padding:5px 10px; color:{color};'>{fmt_inr_table(display_val)}</td></tr>"
                
                display_total = abs(sec_total) if sec_key in ['Equity', 'Borrowings', 'CL'] else sec_total
                rows += f"<tr style='background:#F2F2F2; font-weight:700;'><td style='padding:6px 10px;'>{sec_label}</td><td style='text-align:right; padding:6px 10px;'>{fmt_inr_table(display_total)}</td></tr>"
                
                st.markdown(f"""
                <table style='width:100%; border-collapse:collapse; font-size:13px; margin-bottom:12px;'>
                    <thead><tr style='background:#D6E4F0;'>
                        <th style='text-align:left; padding:6px 10px; font-size:11px; color:#E8833A; letter-spacing:0.5px;'>{sec_label.upper()}</th>
                        <th style='text-align:right; padding:6px 10px;'></th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background:#1B2A4A; color:white; padding:10px 14px; border-radius:6px; display:flex; justify-content:space-between; font-weight:700; font-size:14px;'>
                <span>TOTAL</span><span>{fmt_inr_table(grand_total)}</span>
            </div>
            """, unsafe_allow_html=True)
            
            return grand_total
    
    total_l = render_bs_section(col_l, "Sources of Funds", mis,
        [("Equity", "Equity"), ("Borrowings", "Borrowings"), ("CL", "Current Liabilities")])
    
    total_r = render_bs_section(col_r, "Application of Funds", mis,
        [("FA", "Fixed Assets"), ("CA", "Current Assets")])
    
    # Tally check
    diff = abs(total_r - total_l)
    if diff < 1:
        st.success(f"✅ Balance Sheet tallies — Assets {fmt_inr_table(total_r)} = Liabilities {fmt_inr_table(total_l)}")
    else:
        st.error(f"⚠️ Difference of {fmt_inr_table(diff)} — Assets {fmt_inr_table(total_r)} vs Liabilities {fmt_inr_table(total_l)}")


# ═══════════════════════════════════════
#  TAB 4: LEDGER DETAIL
# ═══════════════════════════════════════
with tab4:
    st.markdown("#### Ledger-Level Detail")
    
    view_option = st.radio("View", ["P&L Ledgers", "BS Ledgers", "All Ledgers"], horizontal=True)
    
    if view_option == "P&L Ledgers":
        detail = mis[mis['statement'] == 'P&L'][['ledger', 'group', 'mis_category', 'section', 'debit', 'credit', 'pl_amount']].copy()
        detail = detail[detail['pl_amount'] != 0].sort_values('pl_amount', ascending=False)
        detail.columns = ['Ledger', 'Tally Group', 'MIS Category', 'Section', 'Debit', 'Credit', 'Net Amount']
    elif view_option == "BS Ledgers":
        detail = mis[mis['statement'] == 'BS'][['ledger', 'group', 'mis_category', 'section', 'opening', 'closing', 'bs_amount']].copy()
        detail = detail[detail['closing'] != 0].sort_values('bs_amount', ascending=False)
        detail.columns = ['Ledger', 'Tally Group', 'MIS Category', 'Section', 'Opening', 'Closing', 'BS Amount']
    else:
        detail = mis[['ledger', 'group', 'mis_category', 'statement', 'section', 'opening', 'debit', 'credit', 'closing']].copy()
        detail = detail[(detail['closing'] != 0) | (detail['debit'] != 0)].sort_values('closing', ascending=False)
        detail.columns = ['Ledger', 'Tally Group', 'MIS Category', 'Statement', 'Section', 'Opening', 'Debit', 'Credit', 'Closing']
    
    # Search filter
    search = st.text_input("🔍 Search ledger", "")
    if search:
        detail = detail[detail['Ledger'].str.contains(search, case=False, na=False)]
    
    st.dataframe(detail, use_container_width=True, hide_index=True)
    
    # Download
    csv = detail.to_csv(index=False)
    st.download_button("📥 Download as CSV", csv, "ledger_detail.csv", "text/csv")


# ═══════════════════════════════════════
#  TAB 5: FLAG-OFF ITEMS
# ═══════════════════════════════════════
with tab5:
    st.markdown("#### Flag-Off Items & Open Queries")
    
    flags = generate_flags(mis)
    
    # Static compliance flags
    compliance_flags = [
        {"item": "TDS Return Filing (24Q/26Q)", "priority": "HIGH", "category": "Compliance", "action": "File if any TDS deducted during the period"},
        {"item": "GST Registration Status", "priority": "HIGH", "category": "Compliance", "action": "Confirm if registered; if not, plan pre-launch registration"},
        {"item": "Director KYC (DIR-3 KYC)", "priority": "MEDIUM", "category": "Compliance", "action": "Annual filing — due 30 September"},
        {"item": "ROC Annual Filing (AOC-4/MGT-7)", "priority": "MEDIUM", "category": "Compliance", "action": "FY 2025-26 — due November 2026"},
        {"item": "Bank Reconciliation", "priority": "HIGH", "category": "Reconciliation", "action": "Obtain bank statement and reconcile"},
        {"item": "Related Party Transactions — Director/Shareholder Loans", "priority": "HIGH", "category": "Compliance", "action": "Board resolution, interest computation, Section 185/186 compliance"},
    ]
    
    all_flags = flags + compliance_flags
    
    # Summary
    high = sum(1 for f in all_flags if f['priority'] == 'HIGH')
    med = sum(1 for f in all_flags if f['priority'] == 'MEDIUM')
    low = sum(1 for f in all_flags if f['priority'] == 'LOW')
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 High Priority", high)
    c2.metric("🟡 Medium Priority", med)
    c3.metric("🟢 Low Priority", low)
    
    st.markdown("---")
    
    for f in sorted(all_flags, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x['priority'], 3)):
        p = f['priority']
        icon = "🔴" if p == "HIGH" else ("🟡" if p == "MEDIUM" else "🟢")
        with st.expander(f"{icon} {f['item']}", expanded=(p == "HIGH")):
            st.markdown(f"**Category:** {f['category']}")
            st.markdown(f"**Priority:** {p}")
            st.markdown(f"**Action Required:** {f['action']}")


# ─── Footer ───
st.markdown("""
<div class='stca-footer'>
    Prepared by STCA Global, Chartered Accountants (FRN 016465S) • Confidential — For management use only
</div>
""", unsafe_allow_html=True)
