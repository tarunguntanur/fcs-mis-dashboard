"""
Full Circle Studio — MIS Dashboard v2
Multi-month support with persistence, trends, and YTD
Deploy: streamlit run fcs_mis_app_v2.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, os, io, calendar
from datetime import datetime
from pathlib import Path

# ─── Page Config ───
st.set_page_config(page_title="Full Circle Studio — MIS", page_icon="🏋️", layout="wide", initial_sidebar_state="expanded")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ─── Styling ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main-header { background: linear-gradient(135deg, #1B2A4A 0%, #2E86C1 100%); padding: 28px 32px; border-radius: 12px; margin-bottom: 24px; color: white; }
.main-header h1 { margin: 0; font-size: 24px; font-weight: 700; }
.main-header p { margin: 4px 0 0; font-size: 13px; opacity: 0.8; }
.stca-footer { text-align: center; padding: 20px 0 8px; color: #95A5A6; font-size: 11px; border-top: 1px solid #E0E0E0; margin-top: 24px; }
.month-tag { display: inline-block; background: #D6E4F0; color: #1B2A4A; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 2px; }
.month-tag-active { background: #2E86C1; color: white; }
</style>
""", unsafe_allow_html=True)

# ─── MIS Mapping ───
GROUP_MAP = {
    "Revenue from operations": ("Revenue", "P&L", "Revenue"),
    "Direct Incomes": ("Other Operating Income", "P&L", "Revenue"),
    "Other direct income": ("Other Operating Income", "P&L", "Revenue"),
    "Indirect Incomes": ("Other Income", "P&L", "Revenue"),
    "Direct Expenses": ("Direct Costs", "P&L", "COGS"),
    "Purchase Accounts": ("Purchases", "P&L", "COGS"),
    "Employee costs": ("Employee Costs", "P&L", "OpEx"),
    "Facility and rental cost": ("Rent & Facility", "P&L", "OpEx"),
    "Professional and consultancy fees": ("Professional Fees", "P&L", "OpEx"),
    "Selling and distribution expense": ("Selling & Distribution", "P&L", "OpEx"),
    "Travelling, boarding and lodging": ("Travel & Lodging", "P&L", "OpEx"),
    "Communication costs": ("Communication", "P&L", "OpEx"),
    "Power and fuel": ("Power & Fuel", "P&L", "OpEx"),
    "Insurance expense": ("Insurance", "P&L", "OpEx"),
    "Repairs and maintenance": ("Repairs & Maintenance", "P&L", "OpEx"),
    "Miscellaneous expenses": ("Miscellaneous", "P&L", "OpEx"),
    "Office Expenses": ("Office Expenses", "P&L", "OpEx"),
    "Indirect Expenses": ("Other Indirect Expenses", "P&L", "OpEx"),
    "Reimbursements": ("Reimbursements", "P&L", "OpEx"),
    "Finance costs": ("Finance Costs", "P&L", "Finance"),
    "Tax expense": ("Tax Expense", "P&L", "Tax"),
    "Share capital": ("Share Capital", "BS", "Equity"),
    "Reserves & Surplus": ("Reserves & Surplus", "BS", "Equity"),
    "Debentures": ("Debentures", "BS", "Borrowings"),
    "Loans (Liability)": ("Other Loans", "BS", "Borrowings"),
    "Secured Loans": ("Secured Loans", "BS", "Borrowings"),
    "Unsecured Loans": ("Unsecured Loans", "BS", "Borrowings"),
    "Loan From Directors": ("Director Loans", "BS", "Borrowings"),
    "Loan From Relatives": ("Related Party Loans", "BS", "Borrowings"),
    "Sundry Creditors": ("Trade Payables", "BS", "CL"),
    "Current Liabilities": ("Other Current Liabilities", "BS", "CL"),
    "Other current liabilities": ("Other Current Liabilities", "BS", "CL"),
    "Provisions": ("Provisions", "BS", "CL"),
    "Amounts payable to employees": ("Employee Payables", "BS", "CL"),
    "GST Ledgers": ("GST Payable", "BS", "CL"),
    "TDS Ledgers": ("TDS Receivable", "BS", "CA"),
    "ESI": ("ESI Payable", "BS", "CL"),
    "PF": ("PF Payable", "BS", "CL"),
    "Labour welfare fund": ("LWF Payable", "BS", "CL"),
    "Professional Tax": ("Prof Tax Payable", "BS", "CL"),
    "Property, plant and equipment": ("PPE", "BS", "FA"),
    "Intangible assets": ("Intangible Assets", "BS", "FA"),
    "Fixed Assets": ("Other Fixed Assets", "BS", "FA"),
    "Balance with banks": ("Bank Balances", "BS", "CA"),
    "Other deposit with banks": ("Bank Deposits", "BS", "CA"),
    "Cash-in-Hand": ("Cash", "BS", "CA"),
    "Sundry Debtors": ("Trade Receivables", "BS", "CA"),
    "Trade receivables": ("Trade Receivables", "BS", "CA"),
    "Deposits (Asset)": ("Security Deposits", "BS", "CA"),
    "Loans & Advances (Asset)": ("Loans & Advances", "BS", "CA"),
    "Capital Advances": ("Capital Advances", "BS", "CA"),
    "Current Assets": ("Other Current Assets", "BS", "CA"),
    "Prepaid expenses": ("Prepaid Expenses", "BS", "CA"),
    "Inventory": ("Inventory", "BS", "CA"),
    "Investments": ("Investments", "BS", "CA"),
    "Balances with government authorities": ("Statutory Receivables", "BS", "CA"),
    "Suspense A/c": ("Suspense", "BS", "CA"),
    "_x0004_ Primary": ("Unmapped", "BS", "CA"),
}

FY_MONTHS = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]

# ─── Helpers ───
def fmt_inr(val):
    if pd.isna(val) or val == 0: return "—"
    a = abs(val)
    if a >= 1e7: return f"₹{val/1e7:,.2f} Cr"
    if a >= 1e5: return f"₹{val/1e5:,.2f} L"
    return f"₹{val:,.0f}"

def fmt_tbl(val):
    if pd.isna(val) or val == 0: return "—"
    if val < 0: return f"({abs(val):,.0f})"
    return f"{val:,.0f}"

def parse_tb(file):
    df = pd.read_excel(file, header=None)
    header_row = None
    for i, row in df.iterrows():
        if any(str(v).strip() == 'Particulars' for v in row.values if pd.notna(v)):
            header_row = i; break
    period = ""
    for i in range(min(header_row or 5, 10)):
        val = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ""
        if "to" in val.lower() and any(c.isdigit() for c in val):
            period = val.strip(); break
    data_start = header_row + 2 if header_row is not None else 9
    tb = df.iloc[data_start:].copy()
    tb.columns = range(len(tb.columns))
    tb = tb[[0,1,2,3,4]]
    tb.columns = ['ledger','opening','debit','credit','closing']
    tb = tb.dropna(subset=['ledger'])
    tb = tb[~tb['ledger'].astype(str).str.contains('Grand Total|Total', case=False, na=False)]
    for c in ['opening','debit','credit','closing']:
        tb[c] = pd.to_numeric(tb[c], errors='coerce').fillna(0)
    tb['ledger'] = tb['ledger'].astype(str).str.strip()
    return tb, period

def parse_master(file):
    df = pd.read_excel(file, header=None)
    header_row = None
    for i, row in df.iterrows():
        if 'Name of Ledger' in ' '.join(str(v) for v in row.values if pd.notna(v)):
            header_row = i; break
    data_start = (header_row + 1) if header_row is not None else 6
    ms = df.iloc[data_start:][[1,2]].copy()
    ms.columns = ['ledger','group']
    ms = ms.dropna(subset=['ledger'])
    ms['ledger'] = ms['ledger'].astype(str).str.strip()
    ms['group'] = ms['group'].astype(str).str.strip()
    return ms

def apply_mapping(tb, master):
    m = tb.merge(master[['ledger','group']], on='ledger', how='left')
    m['mis_category'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[0])
    m['statement'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[1])
    m['section'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[2])
    # P&L amounts
    m['pl_amount'] = 0.0
    rev = m['section'] == 'Revenue'
    exp = (m['statement'] == 'P&L') & ~rev
    m.loc[rev, 'pl_amount'] = m.loc[rev, 'credit'] - m.loc[rev, 'debit']
    m.loc[exp, 'pl_amount'] = m.loc[exp, 'debit'] - m.loc[exp, 'credit']
    # BS amounts
    m['bs_amount'] = 0.0
    bs = m['statement'] == 'BS'
    m.loc[bs, 'bs_amount'] = m.loc[bs, 'closing']
    return m

def save_master(master):
    master.to_csv(DATA_DIR / "master.csv", index=False)

def load_master():
    p = DATA_DIR / "master.csv"
    if p.exists(): return pd.read_csv(p)
    return None

def save_month(month_key, tb_parsed):
    tb_parsed.to_csv(DATA_DIR / f"tb_{month_key}.csv", index=False)

def load_all_months():
    months = {}
    for f in sorted(DATA_DIR.glob("tb_*.csv")):
        key = f.stem.replace("tb_", "")
        months[key] = pd.read_csv(f)
    return months

def delete_month(month_key):
    p = DATA_DIR / f"tb_{month_key}.csv"
    if p.exists(): p.unlink()

def month_sort_key(key):
    """Sort month keys in FY order: apr26=0, may26=1, ..., mar27=11"""
    parts = key.lower()
    for i, m in enumerate(["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]):
        if parts.startswith(m): return i
    return 99

def get_month_label(key):
    """Convert 'jun26' to 'Jun-26'"""
    return key[:3].title() + "-" + key[3:]

def compute_section_total(mis, statement, section, amount_col='pl_amount'):
    return mis[(mis['statement']==statement) & (mis['section']==section)][amount_col].sum()


# ─── Sidebar ───
with st.sidebar:
    st.markdown("### 📁 Data Management")
    
    # Master upload
    st.markdown("**Master (List of Ledgers)**")
    existing_master = load_master()
    if existing_master is not None:
        st.success(f"✓ Loaded — {len(existing_master)} ledgers")
        if st.checkbox("Re-upload Master"):
            mf = st.file_uploader("Upload new Master", type=['xlsx','xls'], key="master_new")
            if mf:
                master = parse_master(mf)
                save_master(master)
                st.success(f"Updated — {len(master)} ledgers")
                st.rerun()
    else:
        mf = st.file_uploader("Upload Master", type=['xlsx','xls'], key="master_init")
        if mf:
            master = parse_master(mf)
            save_master(master)
            st.success(f"Saved — {len(master)} ledgers")
            st.rerun()
    
    st.markdown("---")
    
    # Monthly TB upload
    st.markdown("**Add Monthly Trial Balance**")
    
    fy_year = st.selectbox("Financial Year", ["2026-27", "2025-26"], index=0)
    fy_start = int(fy_year[:4])
    
    month_options = [f"{m}-{str(fy_start)[2:]}" if i < 9 else f"{m}-{str(fy_start+1)[2:]}" for i, m in enumerate(FY_MONTHS)]
    selected_month_label = st.selectbox("Month", month_options)
    month_key = selected_month_label.replace("-","").lower()
    
    tb_file = st.file_uploader("Upload TB for this month", type=['xlsx','xls'], key="tb_upload")
    if tb_file and existing_master is not None:
        tb_parsed, period = parse_tb(tb_file)
        if tb_parsed is not None:
            save_month(month_key, tb_parsed)
            st.success(f"✓ Saved {selected_month_label} — {len(tb_parsed)} ledgers, period: {period}")
            st.rerun()
    
    st.markdown("---")
    
    # Show loaded months
    all_months = load_all_months()
    if all_months:
        st.markdown("**Loaded Months**")
        sorted_keys = sorted(all_months.keys(), key=month_sort_key)
        tags = " ".join([f"<span class='month-tag'>{get_month_label(k)}</span>" for k in sorted_keys])
        st.markdown(tags, unsafe_allow_html=True)
        
        with st.expander("🗑️ Remove a month"):
            del_month = st.selectbox("Select month to remove", [get_month_label(k) for k in sorted_keys])
            if st.button("Remove", type="secondary"):
                dk = del_month.replace("-","").lower()
                delete_month(dk)
                st.rerun()
    
    st.markdown("---")
    st.markdown("<div style='text-align:center; font-size:10px; color:#95A5A6;'>STCA Global • FRN 016465S</div>", unsafe_allow_html=True)


# ─── Main ───
master = load_master()
all_months = load_all_months()

if master is None or not all_months:
    st.markdown("""<div class='main-header'><h1>Full Circle Studio Private Limited</h1>
    <p>Management Information System — Monthly Reporting Dashboard</p></div>""", unsafe_allow_html=True)
    
    if master is None:
        st.info("👈 Upload the **Master** (List of Ledgers) in the sidebar.")
    elif not all_months:
        st.info("👈 Master loaded. Now upload a **Trial Balance** for any month.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Tally Export Steps")
        st.markdown("""
        1. **Master** → Gateway → Display → List of Accounts → Export as Excel
        2. **Trial Balance** → Gateway → Display → Trial Balance → Set period (standalone month) → Export as Excel
        """)
    with c2:
        st.markdown("#### Monthly Workflow")
        st.markdown("""
        1. Close the month in Tally
        2. Export standalone monthly TB
        3. Select month in sidebar → Upload
        4. Review MIS → Share with client
        """)
    st.stop()

# ─── Process all months ───
sorted_months = sorted(all_months.keys(), key=month_sort_key)
month_data = {}

for mk in sorted_months:
    tb = all_months[mk]
    # Ensure numeric columns
    for c in ['opening','debit','credit','closing']:
        tb[c] = pd.to_numeric(tb[c], errors='coerce').fillna(0)
    mis = apply_mapping(tb, master)
    month_data[mk] = mis

latest_month = sorted_months[-1]
latest_mis = month_data[latest_month]
prior_month = sorted_months[-2] if len(sorted_months) > 1 else None
prior_mis = month_data[prior_month] if prior_month else None

# ─── Compute metrics for each month ───
monthly_metrics = {}
for mk in sorted_months:
    mis = month_data[mk]
    revenue = compute_section_total(mis, 'P&L', 'Revenue')
    cogs = compute_section_total(mis, 'P&L', 'COGS')
    opex = compute_section_total(mis, 'P&L', 'OpEx')
    finance = compute_section_total(mis, 'P&L', 'Finance')
    tax = compute_section_total(mis, 'P&L', 'Tax')
    gross = revenue - cogs
    ebitda = gross - opex
    net = ebitda - finance - tax
    total_exp = cogs + opex + finance
    bank = mis[mis['mis_category'].isin(['Bank Balances','Bank Deposits'])]['bs_amount'].sum()
    borrowings = abs(mis[mis['section']=='Borrowings']['bs_amount'].sum())
    equity_val = abs(mis[mis['section']=='Equity']['bs_amount'].sum())
    fa = mis[mis['section']=='FA']['bs_amount'].sum()
    ca = mis[mis['section']=='CA']['bs_amount'].sum()
    cl_val = abs(mis[mis['section']=='CL']['bs_amount'].sum())
    
    monthly_metrics[mk] = {
        'revenue': revenue, 'cogs': cogs, 'gross_profit': gross, 'opex': opex,
        'ebitda': ebitda, 'finance': finance, 'tax': tax, 'net_pl': net,
        'total_expenses': total_exp, 'bank': bank, 'borrowings': borrowings,
        'equity': equity_val, 'fa': fa, 'ca': ca, 'cl': cl_val,
        'burn_rate': total_exp, 'runway': bank / total_exp if total_exp > 0 else 0,
        'de_ratio': borrowings / equity_val if equity_val > 0 else 0,
        'current_ratio': ca / cl_val if cl_val > 0 else 0,
    }

lm = monthly_metrics[latest_month]
pm = monthly_metrics[prior_month] if prior_month else None

# ─── YTD aggregation ───
ytd = {}
for key in ['revenue','cogs','opex','finance','tax','total_expenses']:
    ytd[key] = sum(monthly_metrics[mk][key] for mk in sorted_months)
ytd['gross_profit'] = ytd['revenue'] - ytd['cogs']
ytd['ebitda'] = ytd['gross_profit'] - ytd['opex']
ytd['net_pl'] = ytd['ebitda'] - ytd['finance'] - ytd['tax']

# ─── Header ───
period_range = f"{get_month_label(sorted_months[0])} to {get_month_label(sorted_months[-1])}"
st.markdown(f"""<div class='main-header'><h1>Full Circle Studio Private Limited</h1>
<p>Management Information System &nbsp;•&nbsp; FY {fy_year} &nbsp;•&nbsp; {len(sorted_months)} month(s) loaded: {period_range}</p></div>""", unsafe_allow_html=True)

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet", "🔍 Ledger Detail", "🚩 Flags"])

# ═══════ DASHBOARD ═══════
with tab1:
    if lm['revenue'] == 0:
        st.warning("🚧 **Pre-Launch Phase** — No revenue recorded in the latest month.")
    
    # KPIs — latest month with MoM delta
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    def delta_str(curr, prev, key, invert=False):
        if prev is None: return None
        d = curr - prev[key]
        if d == 0: return None
        return f"{'↑' if d>0 else '↓'} {fmt_inr(abs(d))}"
    
    k1.metric("Revenue", fmt_inr(lm['revenue']) if lm['revenue']>0 else "NIL", delta_str(lm['revenue'], pm, 'revenue'))
    k2.metric("Expenses", fmt_inr(lm['total_expenses']), delta_str(lm['total_expenses'], pm, 'total_expenses'), delta_color="inverse")
    k3.metric("Net P/L", fmt_inr(lm['net_pl']), "Loss" if lm['net_pl']<0 else "Profit", delta_color="inverse" if lm['net_pl']<0 else "normal")
    k4.metric("Cash & Bank", fmt_inr(lm['bank']), delta_str(lm['bank'], pm, 'bank'))
    k5.metric("Burn Rate", fmt_inr(lm['burn_rate']))
    k6.metric("Runway", f"{lm['runway']:.1f} mo" if lm['runway']<100 else "N/A")
    
    # YTD summary
    st.markdown("---")
    y1,y2,y3,y4 = st.columns(4)
    y1.metric("YTD Revenue", fmt_inr(ytd['revenue']) if ytd['revenue']>0 else "NIL")
    y2.metric("YTD Expenses", fmt_inr(ytd['total_expenses']))
    y3.metric("YTD Net P/L", fmt_inr(ytd['net_pl']))
    y4.metric("Months Loaded", f"{len(sorted_months)} of 12")
    
    st.markdown("---")
    
    # ── Trend Charts ──
    if len(sorted_months) > 1:
        trend_df = pd.DataFrame([
            {'Month': get_month_label(mk), **monthly_metrics[mk]} for mk in sorted_months
        ])
        
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df['Month'], y=trend_df['total_expenses'], name='Expenses', marker_color='#E74C3C', opacity=0.8))
            fig.add_trace(go.Bar(x=trend_df['Month'], y=trend_df['revenue'], name='Revenue', marker_color='#27AE60', opacity=0.8))
            fig.update_layout(title="Revenue vs Expenses — Monthly Trend", height=350, barmode='group',
                            font=dict(family="Inter"), margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['bank'], mode='lines+markers', name='Cash & Bank',
                                     line=dict(color='#2E86C1', width=3), marker=dict(size=8)))
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['borrowings'], mode='lines+markers', name='Borrowings',
                                     line=dict(color='#E8833A', width=2, dash='dash'), marker=dict(size=6)))
            fig2.update_layout(title="Cash & Borrowings Trajectory", height=350,
                             font=dict(family="Inter"), margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig2, use_container_width=True)
    
    # Expense breakdown — latest month
    c3, c4 = st.columns(2)
    with c3:
        exp_data = latest_mis[(latest_mis['statement']=='P&L') & (latest_mis['section']!='Revenue') & (latest_mis['pl_amount']>0)]
        exp_cat = exp_data.groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False).reset_index()
        exp_cat.columns = ['Category','Amount']
        if len(exp_cat) > 0:
            fig3 = px.pie(exp_cat, values='Amount', names='Category', title=f"Expense Mix — {get_month_label(latest_month)}",
                        color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig3.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"),
                             legend=dict(orientation="h", y=-0.1))
            fig3.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
            st.plotly_chart(fig3, use_container_width=True)
    
    with c4:
        asset_data = latest_mis[(latest_mis['section'].isin(['FA','CA'])) & (latest_mis['bs_amount']>0)]
        asset_cat = asset_data.groupby('mis_category')['bs_amount'].sum().sort_values(ascending=False).reset_index()
        asset_cat.columns = ['Asset','Amount']
        if len(asset_cat) > 0:
            fig4 = px.bar(asset_cat, x='Asset', y='Amount', title="Asset Composition — Latest",
                        color_discrete_sequence=['#27AE60'])
            fig4.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"),
                             showlegend=False, xaxis_title="", yaxis_title="")
            fig4.update_traces(text=[fmt_inr(v) for v in asset_cat['Amount']], textposition='outside', textfont_size=11)
            st.plotly_chart(fig4, use_container_width=True)
    
    # Ratios
    st.markdown("#### Key Ratios")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Debt-Equity", f"{lm['de_ratio']:.1f}x", delta_str(lm['de_ratio'], pm, 'de_ratio') if pm else None, delta_color="inverse")
    r2.metric("Current Ratio", f"{lm['current_ratio']:.1f}x")
    r3.metric("Total Borrowings", fmt_inr(lm['borrowings']))
    r4.metric("Net Worth", fmt_inr(lm['equity']))


# ═══════ PROFIT & LOSS — MULTI-MONTH ═══════
with tab2:
    st.markdown("#### Profit & Loss Statement — Monthly + YTD")
    
    # Build P&L line items
    pl_order = [
        ("REVENUE", "header", "Revenue"),
        ("_items_", "items", "Revenue"),
        ("Total Revenue", "total", "Revenue"),
        ("", "spacer", None),
        ("COST OF REVENUE", "header", "COGS"),
        ("_items_", "items", "COGS"),
        ("Total Cost of Revenue", "total", "COGS"),
        ("", "spacer", None),
        ("GROSS PROFIT", "grand", "gross"),
        ("", "spacer", None),
        ("OPERATING EXPENSES", "header", "OpEx"),
        ("_items_", "items", "OpEx"),
        ("Total Operating Expenses", "total", "OpEx"),
        ("", "spacer", None),
        ("EBITDA", "grand", "ebitda"),
        ("", "spacer", None),
        ("FINANCE COSTS", "header", "Finance"),
        ("_items_", "items", "Finance"),
        ("", "spacer", None),
        ("NET PROFIT / (LOSS)", "grand", "net"),
    ]
    
    # Get all unique MIS categories per section across all months
    all_categories = {}
    for mk in sorted_months:
        mis = month_data[mk]
        for section in ['Revenue','COGS','OpEx','Finance','Tax']:
            cats = mis[(mis['statement']=='P&L') & (mis['section']==section) & (mis['pl_amount']!=0)]['mis_category'].unique()
            if section not in all_categories:
                all_categories[section] = set()
            all_categories[section].update(cats)
    
    # Build table header
    month_labels = [get_month_label(mk) for mk in sorted_months]
    header_cols = ["Particulars"] + month_labels + ["YTD"]
    
    # Build rows
    table_rows = []
    
    for label, row_type, section in pl_order:
        if row_type == "spacer":
            table_rows.append({"type": "spacer"})
            continue
        if row_type == "header":
            table_rows.append({"type": "header", "label": label})
            continue
        if row_type == "items":
            cats = sorted(all_categories.get(section, []))
            for cat in cats:
                row = {"type": "item", "label": f"  {cat}"}
                ytd_val = 0
                for mk in sorted_months:
                    mis = month_data[mk]
                    val = mis[(mis['statement']=='P&L') & (mis['section']==section) & (mis['mis_category']==cat)]['pl_amount'].sum()
                    row[mk] = val
                    ytd_val += val
                row['ytd'] = ytd_val
                table_rows.append(row)
            continue
        if row_type == "total":
            row = {"type": "total", "label": label}
            ytd_val = 0
            for mk in sorted_months:
                val = monthly_metrics[mk].get({
                    'Revenue': 'revenue', 'COGS': 'cogs', 'OpEx': 'opex', 'Finance': 'finance', 'Tax': 'tax'
                }.get(section, ''), 0)
                row[mk] = val
                ytd_val += val
            row['ytd'] = ytd_val
            table_rows.append(row)
            continue
        if row_type == "grand":
            row = {"type": "grand", "label": label}
            metric_key = {'gross': 'gross_profit', 'ebitda': 'ebitda', 'net': 'net_pl'}.get(section, section)
            ytd_val = 0
            for mk in sorted_months:
                val = monthly_metrics[mk].get(metric_key, 0)
                row[mk] = val
                ytd_val += val
            row['ytd'] = ytd_val
            table_rows.append(row)
    
    # Render HTML table
    # Column headers
    th_style = "text-align:right; padding:10px 12px; font-weight:600; font-size:12px;"
    header_html = f"<th style='text-align:left; padding:10px 14px; font-weight:600; min-width:200px;'>Particulars</th>"
    for ml in month_labels:
        header_html += f"<th style='{th_style}'>{ml}</th>"
    header_html += f"<th style='{th_style} background:#D6E4F0;'>YTD</th>"
    
    rows_html = ""
    for row in table_rows:
        if row['type'] == 'spacer':
            rows_html += f"<tr><td colspan='{len(header_cols)}' style='padding:4px;'></td></tr>"
            continue
        if row['type'] == 'header':
            rows_html += f"<tr><td colspan='{len(header_cols)}' style='padding:8px 14px; font-weight:700; color:#E8833A; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;'>{row['label']}</td></tr>"
            continue
        
        bg = "#F8F9FA" if row['type']=='total' else ("#D6E4F0" if row['type']=='grand' else "transparent")
        fw = "700" if row['type'] in ('total','grand') else "400"
        border = "border-bottom:2px solid #1B2A4A;" if row['type'] in ('total','grand') else "border-bottom:1px solid #ECF0F1;"
        
        td_label = f"<td style='padding:7px 14px; font-weight:{fw}; {border}'>{row['label']}</td>"
        td_vals = ""
        for mk in sorted_months:
            v = row.get(mk, 0)
            color = "#E74C3C" if v < 0 else "#2C3E50"
            td_vals += f"<td style='text-align:right; padding:7px 10px; font-weight:{fw}; color:{color}; {border}; font-size:12px;'>{fmt_tbl(v)}</td>"
        
        ytd_v = row.get('ytd', 0)
        ytd_color = "#E74C3C" if ytd_v < 0 else "#2C3E50"
        td_vals += f"<td style='text-align:right; padding:7px 10px; font-weight:700; color:{ytd_color}; {border}; background:#F0F4F8; font-size:12px;'>{fmt_tbl(ytd_v)}</td>"
        
        rows_html += f"<tr style='background:{bg};'>{td_label}{td_vals}</tr>"
    
    st.markdown(f"""
    <div style='overflow-x:auto;'>
    <table style='width:100%; border-collapse:collapse; font-family:Inter,sans-serif; font-size:13px;'>
        <thead><tr style='background:#1B2A4A; color:white;'>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table></div>
    """, unsafe_allow_html=True)
    
    # Expense trend stacked bar
    if len(sorted_months) > 1:
        st.markdown("---")
        st.markdown("#### Expense Composition — Month on Month")
        exp_trend = []
        for mk in sorted_months:
            mis = month_data[mk]
            cats = mis[(mis['statement']=='P&L') & (mis['section'].isin(['COGS','OpEx'])) & (mis['pl_amount']>0)]
            for _, r in cats.groupby('mis_category')['pl_amount'].sum().items():
                exp_trend.append({'Month': get_month_label(mk), 'Category': _, 'Amount': r})
        if exp_trend:
            edf = pd.DataFrame(exp_trend)
            fig_stack = px.bar(edf, x='Month', y='Amount', color='Category', title="",
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_stack.update_layout(height=350, barmode='stack', font=dict(family="Inter"),
                                  margin=dict(t=20,b=20,l=20,r=20), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_stack, use_container_width=True)


# ═══════ BALANCE SHEET ═══════
with tab3:
    st.markdown(f"#### Balance Sheet as at {get_month_label(latest_month)}")
    if prior_month:
        st.caption(f"With comparison to {get_month_label(prior_month)}")
    
    def render_bs_v2(mis_curr, mis_prev, sections):
        rows = []
        for sec_key, sec_label in sections:
            curr_data = mis_curr[(mis_curr['section']==sec_key) & (mis_curr['bs_amount']!=0)]
            if len(curr_data) == 0:
                prev_data = mis_prev[(mis_prev['section']==sec_key) & (mis_prev['bs_amount']!=0)] if mis_prev is not None else pd.DataFrame()
                if len(prev_data) == 0:
                    continue
            
            rows.append({"type": "section", "label": sec_label})
            
            curr_by_cat = curr_data.groupby('mis_category')['bs_amount'].sum()
            prev_by_cat = mis_prev[(mis_prev['section']==sec_key)].groupby('mis_category')['bs_amount'].sum() if mis_prev is not None else pd.Series(dtype=float)
            
            all_cats = set(curr_by_cat.index) | set(prev_by_cat.index)
            for cat in sorted(all_cats):
                cv = curr_by_cat.get(cat, 0)
                pv = prev_by_cat.get(cat, 0)
                is_liab = sec_key in ['Equity','Borrowings','CL']
                rows.append({"type": "item", "label": cat, "current": abs(cv) if is_liab else cv,
                            "prior": abs(pv) if is_liab else pv, "movement": abs(cv)-abs(pv) if is_liab else cv-pv})
            
            sec_curr = abs(curr_by_cat.sum()) if sec_key in ['Equity','Borrowings','CL'] else curr_by_cat.sum()
            sec_prev = abs(prev_by_cat.sum()) if sec_key in ['Equity','Borrowings','CL'] else prev_by_cat.sum()
            rows.append({"type": "subtotal", "label": sec_label, "current": sec_curr, "prior": sec_prev, "movement": sec_curr - sec_prev})
        
        # Grand total
        gt_curr = sum(r['current'] for r in rows if r['type']=='subtotal')
        gt_prev = sum(r['prior'] for r in rows if r['type']=='subtotal')
        rows.append({"type": "grand", "label": "TOTAL", "current": gt_curr, "prior": gt_prev, "movement": gt_curr - gt_prev})
        
        return rows
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("**Sources of Funds**")
        liab_rows = render_bs_v2(latest_mis, prior_mis, [("Equity","Equity"), ("Borrowings","Borrowings"), ("CL","Current Liabilities")])
        
        show_prior = prior_month is not None
        cols_header = f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{get_month_label(latest_month)}</th>"
        if show_prior:
            cols_header += f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{get_month_label(prior_month)}</th>"
            cols_header += f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>Movement</th>"
        
        bs_html = f"<table style='width:100%; border-collapse:collapse; font-size:13px;'><thead><tr style='background:#D6E4F0;'><th style='text-align:left; padding:6px 10px;'>Particulars</th>{cols_header}</tr></thead><tbody>"
        for r in liab_rows:
            if r['type'] == 'section':
                bs_html += f"<tr><td colspan='{'4' if show_prior else '2'}' style='padding:8px 10px; font-weight:700; color:#E8833A; font-size:11px;'>{r['label'].upper()}</td></tr>"
            elif r['type'] in ('item','subtotal','grand'):
                bg = "#F2F2F2" if r['type']=='subtotal' else ("#1B2A4A" if r['type']=='grand' else "transparent")
                fc = "white" if r['type']=='grand' else "#2C3E50"
                fw = "700" if r['type'] in ('subtotal','grand') else "400"
                mv_color = "#27AE60" if r.get('movement',0) > 0 else ("#E74C3C" if r.get('movement',0) < 0 else "#95A5A6")
                
                row_html = f"<td style='padding:5px 10px; font-weight:{fw}; color:{fc};'>{r['label']}</td>"
                row_html += f"<td style='text-align:right; padding:5px 10px; font-weight:{fw}; color:{fc};'>{fmt_tbl(r['current'])}</td>"
                if show_prior:
                    row_html += f"<td style='text-align:right; padding:5px 10px; color:{fc};'>{fmt_tbl(r['prior'])}</td>"
                    row_html += f"<td style='text-align:right; padding:5px 10px; color:{mv_color}; font-size:12px;'>{fmt_tbl(r['movement'])}</td>"
                bs_html += f"<tr style='background:{bg}; border-bottom:1px solid #ECF0F1;'>{row_html}</tr>"
        bs_html += "</tbody></table>"
        st.markdown(bs_html, unsafe_allow_html=True)
    
    with col_r:
        st.markdown("**Application of Funds**")
        asset_rows = render_bs_v2(latest_mis, prior_mis, [("FA","Fixed Assets"), ("CA","Current Assets")])
        
        bs_html2 = f"<table style='width:100%; border-collapse:collapse; font-size:13px;'><thead><tr style='background:#D6E4F0;'><th style='text-align:left; padding:6px 10px;'>Particulars</th>{cols_header}</tr></thead><tbody>"
        for r in asset_rows:
            if r['type'] == 'section':
                bs_html2 += f"<tr><td colspan='{'4' if show_prior else '2'}' style='padding:8px 10px; font-weight:700; color:#E8833A; font-size:11px;'>{r['label'].upper()}</td></tr>"
            elif r['type'] in ('item','subtotal','grand'):
                bg = "#F2F2F2" if r['type']=='subtotal' else ("#1B2A4A" if r['type']=='grand' else "transparent")
                fc = "white" if r['type']=='grand' else "#2C3E50"
                fw = "700" if r['type'] in ('subtotal','grand') else "400"
                mv_color = "#27AE60" if r.get('movement',0) > 0 else ("#E74C3C" if r.get('movement',0) < 0 else "#95A5A6")
                
                row_html = f"<td style='padding:5px 10px; font-weight:{fw}; color:{fc};'>{r['label']}</td>"
                row_html += f"<td style='text-align:right; padding:5px 10px; font-weight:{fw}; color:{fc};'>{fmt_tbl(r['current'])}</td>"
                if show_prior:
                    row_html += f"<td style='text-align:right; padding:5px 10px; color:{fc};'>{fmt_tbl(r['prior'])}</td>"
                    row_html += f"<td style='text-align:right; padding:5px 10px; color:{mv_color}; font-size:12px;'>{fmt_tbl(r['movement'])}</td>"
                bs_html2 += f"<tr style='background:{bg}; border-bottom:1px solid #ECF0F1;'>{row_html}</tr>"
        bs_html2 += "</tbody></table>"
        st.markdown(bs_html2, unsafe_allow_html=True)
    
    # Tally check
    liab_total = sum(r['current'] for r in liab_rows if r['type']=='grand')
    asset_total = sum(r['current'] for r in asset_rows if r['type']=='grand')
    diff = abs(asset_total - liab_total)
    if diff < 1:
        st.success(f"✅ Balance Sheet tallies — Assets {fmt_tbl(asset_total)} = Liabilities {fmt_tbl(liab_total)}")
    else:
        st.error(f"⚠️ Difference: {fmt_tbl(diff)} — Assets {fmt_tbl(asset_total)} vs Liabilities {fmt_tbl(liab_total)}")


# ═══════ LEDGER DETAIL ═══════
with tab4:
    st.markdown("#### Ledger-Level Detail")
    
    sel_month_det = st.selectbox("Month", [get_month_label(mk) for mk in sorted_months], index=len(sorted_months)-1, key="det_month")
    det_mk = sel_month_det.replace("-","").lower()
    det_mis = month_data[det_mk]
    
    view_opt = st.radio("View", ["P&L Ledgers", "BS Ledgers", "All"], horizontal=True)
    
    if view_opt == "P&L Ledgers":
        detail = det_mis[det_mis['statement']=='P&L'][['ledger','group','mis_category','section','debit','credit','pl_amount']].copy()
        detail = detail[detail['pl_amount']!=0].sort_values('pl_amount', ascending=False)
        detail.columns = ['Ledger','Tally Group','MIS Category','Section','Debit','Credit','Net Amount']
    elif view_opt == "BS Ledgers":
        detail = det_mis[det_mis['statement']=='BS'][['ledger','group','mis_category','section','opening','closing','bs_amount']].copy()
        detail = detail[detail['closing']!=0].sort_values('bs_amount', ascending=False)
        detail.columns = ['Ledger','Tally Group','MIS Category','Section','Opening','Closing','BS Amount']
    else:
        detail = det_mis[['ledger','group','mis_category','statement','section','opening','debit','credit','closing']].copy()
        detail = detail[(detail['closing']!=0)|(detail['debit']!=0)].sort_values('closing', ascending=False)
        detail.columns = ['Ledger','Tally Group','MIS Category','Statement','Section','Opening','Debit','Credit','Closing']
    
    search = st.text_input("🔍 Search", "", key="det_search")
    if search:
        detail = detail[detail['Ledger'].str.contains(search, case=False, na=False)]
    
    st.dataframe(detail, use_container_width=True, hide_index=True)
    st.download_button("📥 Download CSV", detail.to_csv(index=False), f"ledger_{det_mk}.csv", "text/csv")


# ═══════ FLAGS ═══════
with tab5:
    st.markdown("#### Flag-Off Items")
    
    flags = []
    lmis = latest_mis
    
    # Auto-detect large CA balances
    large_ca = lmis[(lmis['bs_amount'].abs()>100000) & (lmis['section']=='CA')].sort_values('bs_amount', ascending=False)
    for _, r in large_ca.head(5).iterrows():
        flags.append({"item": f"{r['ledger']} — {fmt_inr(r['bs_amount'])}", "priority": "HIGH" if abs(r['bs_amount'])>500000 else "MEDIUM",
                      "category": r['mis_category'], "action": "Obtain supporting documents"})
    
    # Negative creditors
    neg = lmis[(lmis['mis_category']=='Trade Payables') & (lmis['closing']>0)]
    for _, r in neg.iterrows():
        flags.append({"item": f"{r['ledger']} — Dr balance {fmt_inr(r['closing'])}", "priority": "HIGH",
                      "category": "Trade Payables", "action": "Reclassify to advances"})
    
    # Suspense
    susp = lmis[(lmis['mis_category']=='Suspense') & (lmis['closing']!=0)]
    for _, r in susp.iterrows():
        flags.append({"item": f"Suspense — {fmt_inr(r['closing'])}", "priority": "HIGH",
                      "category": "Suspense", "action": "Clear before close"})
    
    # MoM material movements
    if prior_mis is not None:
        for cat in lmis['mis_category'].unique():
            curr_val = lmis[lmis['mis_category']==cat]['bs_amount'].sum()
            prev_val = prior_mis[prior_mis['mis_category']==cat]['bs_amount'].sum()
            mvmt = curr_val - prev_val
            if abs(mvmt) > 200000 and prev_val != 0:
                pct = abs(mvmt/prev_val)*100
                if pct > 25:
                    flags.append({"item": f"{cat} — moved {fmt_inr(mvmt)} ({pct:.0f}% MoM)", "priority": "MEDIUM",
                                  "category": "MoM Movement", "action": "Investigate material movement"})
    
    # Compliance
    compliance = [
        {"item": "TDS Return Filing", "priority": "HIGH", "category": "Compliance", "action": "File 24Q/26Q if TDS deducted"},
        {"item": "GST Registration / Returns", "priority": "HIGH", "category": "Compliance", "action": "Confirm registration status"},
        {"item": "Bank Reconciliation", "priority": "HIGH", "category": "Reconciliation", "action": "Obtain bank statement and reconcile"},
        {"item": "Related Party Loan Documentation", "priority": "HIGH", "category": "Compliance", "action": "Board resolution, Sec 185/186, interest"},
        {"item": "Director KYC (DIR-3 KYC)", "priority": "MEDIUM", "category": "Compliance", "action": "Due 30-Sep annually"},
        {"item": "ROC Filings (AOC-4/MGT-7)", "priority": "MEDIUM", "category": "Compliance", "action": "Due November for prev FY"},
    ]
    
    all_flags = flags + compliance
    
    hi = sum(1 for f in all_flags if f['priority']=='HIGH')
    me = sum(1 for f in all_flags if f['priority']=='MEDIUM')
    lo = sum(1 for f in all_flags if f['priority']=='LOW')
    
    f1,f2,f3 = st.columns(3)
    f1.metric("🔴 High", hi)
    f2.metric("🟡 Medium", me)
    f3.metric("🟢 Low", lo)
    
    st.markdown("---")
    for f in sorted(all_flags, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x['priority'],3)):
        icon = "🔴" if f['priority']=="HIGH" else ("🟡" if f['priority']=="MEDIUM" else "🟢")
        with st.expander(f"{icon} {f['item']}", expanded=(f['priority']=="HIGH")):
            st.markdown(f"**Category:** {f['category']}")
            st.markdown(f"**Action:** {f['action']}")

st.markdown("<div class='stca-footer'>Prepared by STCA Global, Chartered Accountants (FRN 016465S) • Confidential</div>", unsafe_allow_html=True)
