"""
Full Circle Studio — MIS Dashboard v3
Multi-month | BS fix (P&L plug) | Client view mode | No flags tab
Deploy: streamlit run fcs_mis_app_v3.py
Client URL: http://localhost:8501/?mode=client
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os, io
from pathlib import Path

st.set_page_config(page_title="Full Circle Studio — MIS", page_icon="🏋️", layout="wide", initial_sidebar_state="expanded")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ─── Client vs Internal mode ───
query_params = st.query_params
IS_CLIENT = query_params.get("mode", "").lower() == "client"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main-header { background: linear-gradient(135deg, #1B2A4A 0%, #2E86C1 100%); padding: 28px 32px; border-radius: 12px; margin-bottom: 24px; color: white; }
.main-header h1 { margin: 0; font-size: 24px; font-weight: 700; }
.main-header p { margin: 4px 0 0; font-size: 13px; opacity: 0.8; }
.stca-footer { text-align: center; padding: 20px 0 8px; color: #95A5A6; font-size: 11px; border-top: 1px solid #E0E0E0; margin-top: 24px; }
.month-tag { display: inline-block; background: #D6E4F0; color: #1B2A4A; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 2px; }
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

    m['pl_amount'] = 0.0
    rev = m['section'] == 'Revenue'
    exp = (m['statement'] == 'P&L') & ~rev
    m.loc[rev, 'pl_amount'] = m.loc[rev, 'credit'] - m.loc[rev, 'debit']
    m.loc[exp, 'pl_amount'] = m.loc[exp, 'debit'] - m.loc[exp, 'credit']

    m['bs_amount'] = 0.0
    bs = m['statement'] == 'BS'
    m.loc[bs, 'bs_amount'] = m.loc[bs, 'closing']

    # ── BS FIX: Inject P&L balance as a synthetic Equity line ──
    # The TB contains P&L ledgers whose net must appear on the BS
    # as "Current Period P&L" under Reserves & Surplus / Equity.
    # Revenue (credit nature) = Credit - Debit → positive = profit
    # Expenses (debit nature) = Debit - Credit → positive = expense
    # Net P&L = Revenue - Expenses. Positive = profit (credit balance on BS).
    # On BS liabilities side, credit balances are positive,
    # so profit adds to Equity, loss reduces it.
    total_revenue = m.loc[rev, 'pl_amount'].sum()
    total_expenses = m.loc[exp, 'pl_amount'].sum()
    net_pl = total_revenue - total_expenses  # positive = profit

    pl_plug = pd.DataFrame([{
        'ledger': 'Profit & Loss Account (Current Period)',
        'opening': 0, 'debit': 0, 'credit': 0,
        'closing': net_pl,  # positive = credit (profit), negative = debit (loss)
        'group': 'Reserves & Surplus',
        'mis_category': 'Current Period P&L',
        'statement': 'BS',
        'section': 'Equity',
        'pl_amount': 0,
        'bs_amount': net_pl,
    }])
    m = pd.concat([m, pl_plug], ignore_index=True)

    return m

def save_master(master): master.to_csv(DATA_DIR / "master.csv", index=False)
def load_master():
    p = DATA_DIR / "master.csv"
    return pd.read_csv(p) if p.exists() else None
def save_month(mk, tb): tb.to_csv(DATA_DIR / f"tb_{mk}.csv", index=False)
def load_all_months():
    months = {}
    for f in sorted(DATA_DIR.glob("tb_*.csv")):
        months[f.stem.replace("tb_","")] = pd.read_csv(f)
    return months
def delete_month(mk):
    p = DATA_DIR / f"tb_{mk}.csv"
    if p.exists(): p.unlink()
def month_sort_key(key):
    for i, m in enumerate(["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]):
        if key.lower().startswith(m): return i
    return 99
def get_month_label(key): return key[:3].title() + "-" + key[3:]
def sect_total(mis, stmt, sec, col='pl_amount'):
    return mis[(mis['statement']==stmt) & (mis['section']==sec)][col].sum()


# ─── Sidebar (hidden in client mode) ───
if not IS_CLIENT:
    with st.sidebar:
        st.markdown("### 📁 Data Management")
        existing_master = load_master()
        if existing_master is not None:
            st.success(f"✓ Master — {len(existing_master)} ledgers")
            if st.checkbox("Re-upload Master"):
                mf = st.file_uploader("Upload new Master", type=['xlsx','xls'], key="master_new")
                if mf:
                    save_master(parse_master(mf)); st.rerun()
        else:
            mf = st.file_uploader("Upload Master", type=['xlsx','xls'], key="master_init")
            if mf:
                save_master(parse_master(mf)); st.rerun()

        st.markdown("---")
        st.markdown("**Add Monthly Trial Balance**")
        fy_year = st.selectbox("Financial Year", ["2026-27","2025-26"], index=0)
        fy_start = int(fy_year[:4])
        month_options = [f"{m}-{str(fy_start)[2:]}" if i < 9 else f"{m}-{str(fy_start+1)[2:]}" for i, m in enumerate(FY_MONTHS)]
        selected_month_label = st.selectbox("Month", month_options)
        month_key = selected_month_label.replace("-","").lower()
        tb_file = st.file_uploader("Upload TB", type=['xlsx','xls'], key="tb_upload")
        if tb_file and load_master() is not None:
            tb_parsed, period = parse_tb(tb_file)
            if tb_parsed is not None:
                save_month(month_key, tb_parsed)
                st.success(f"✓ Saved {selected_month_label} — {len(tb_parsed)} ledgers")
                st.rerun()

        st.markdown("---")
        all_months_sidebar = load_all_months()
        if all_months_sidebar:
            st.markdown("**Loaded Months**")
            sk = sorted(all_months_sidebar.keys(), key=month_sort_key)
            st.markdown(" ".join([f"<span class='month-tag'>{get_month_label(k)}</span>" for k in sk]), unsafe_allow_html=True)
            with st.expander("🗑️ Remove a month"):
                dl = st.selectbox("Month", [get_month_label(k) for k in sk], key="del_sel")
                if st.button("Remove"): delete_month(dl.replace("-","").lower()); st.rerun()

        st.markdown("---")
        # Client link helper
        st.markdown("**🔗 Client Share Link**")
        base_url = st.text_input("Your app URL", value="http://localhost:8501", key="base_url")
        client_url = f"{base_url}/?mode=client"
        st.code(client_url, language=None)
        st.caption("Share this URL with the client. They see only Dashboard, P&L, and Balance Sheet — no sidebar, no ledger detail.")

        st.markdown("---")
        st.markdown("<div style='text-align:center; font-size:10px; color:#95A5A6;'>STCA Global • FRN 016465S</div>", unsafe_allow_html=True)

# ─── Load Data ───
master = load_master()
all_months = load_all_months()

if master is None or not all_months:
    st.markdown("""<div class='main-header'><h1>Full Circle Studio Private Limited</h1>
    <p>Management Information System</p></div>""", unsafe_allow_html=True)
    if IS_CLIENT:
        st.info("The MIS dashboard is being set up. Please check back shortly.")
    else:
        if master is None: st.info("👈 Upload the **Master** (List of Ledgers) in the sidebar.")
        elif not all_months: st.info("👈 Master loaded. Now upload a **Trial Balance** for any month.")
    st.stop()

# ─── Process ───
sorted_months = sorted(all_months.keys(), key=month_sort_key)
month_data = {}
for mk in sorted_months:
    tb = all_months[mk]
    for c in ['opening','debit','credit','closing']:
        tb[c] = pd.to_numeric(tb[c], errors='coerce').fillna(0)
    month_data[mk] = apply_mapping(tb, master)

latest_month = sorted_months[-1]
latest_mis = month_data[latest_month]
prior_month = sorted_months[-2] if len(sorted_months) > 1 else None
prior_mis = month_data[prior_month] if prior_month else None

# ─── Monthly metrics ───
monthly_metrics = {}
for mk in sorted_months:
    mis = month_data[mk]
    rev = sect_total(mis,'P&L','Revenue')
    cogs = sect_total(mis,'P&L','COGS')
    opex = sect_total(mis,'P&L','OpEx')
    fin = sect_total(mis,'P&L','Finance')
    tax = sect_total(mis,'P&L','Tax')
    gross = rev - cogs
    ebitda = gross - opex
    net = ebitda - fin - tax
    tot_exp = cogs + opex + fin
    bank = mis[mis['mis_category'].isin(['Bank Balances','Bank Deposits'])]['bs_amount'].sum()
    borr = abs(mis[mis['section']=='Borrowings']['bs_amount'].sum())
    eq = mis[mis['section']=='Equity']['bs_amount'].sum()  # includes P&L plug now
    fa = mis[mis['section']=='FA']['bs_amount'].sum()
    ca = mis[mis['section']=='CA']['bs_amount'].sum()
    cl_v = abs(mis[mis['section']=='CL']['bs_amount'].sum())

    monthly_metrics[mk] = {
        'revenue':rev, 'cogs':cogs, 'gross_profit':gross, 'opex':opex,
        'ebitda':ebitda, 'finance':fin, 'tax':tax, 'net_pl':net,
        'total_expenses':tot_exp, 'bank':bank, 'borrowings':borr,
        'equity':eq, 'fa':fa, 'ca':ca, 'cl':cl_v,
        'burn_rate':tot_exp,
        'runway': bank/tot_exp if tot_exp > 0 else 0,
        'de_ratio': borr/abs(eq) if eq != 0 else 0,
        'current_ratio': ca/cl_v if cl_v > 0 else 0,
    }

lm = monthly_metrics[latest_month]
pm = monthly_metrics[prior_month] if prior_month else None

ytd = {}
for key in ['revenue','cogs','opex','finance','tax','total_expenses']:
    ytd[key] = sum(monthly_metrics[mk][key] for mk in sorted_months)
ytd['gross_profit'] = ytd['revenue'] - ytd['cogs']
ytd['ebitda'] = ytd['gross_profit'] - ytd['opex']
ytd['net_pl'] = ytd['ebitda'] - ytd['finance'] - ytd['tax']

# ─── Header ───
period_range = f"{get_month_label(sorted_months[0])} to {get_month_label(sorted_months[-1])}"
client_badge = " &nbsp;•&nbsp; <span style='background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:10px; font-size:11px;'>Client View</span>" if IS_CLIENT else ""
st.markdown(f"""<div class='main-header'><h1>Full Circle Studio Private Limited</h1>
<p>Management Information System &nbsp;•&nbsp; {period_range}{client_badge}</p></div>""", unsafe_allow_html=True)

# ─── Tabs ───
if IS_CLIENT:
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet", "🔍 Ledger Detail"])


# ═══════ DASHBOARD ═══════
with tab1:
    if lm['revenue'] == 0:
        st.warning("🚧 **Pre-Launch Phase** — No revenue recorded in the latest month.")

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    def delta_s(curr_val, prev_dict, key):
        if prev_dict is None: return None
        d = curr_val - prev_dict[key]
        if d == 0: return None
        return f"{'↑' if d>0 else '↓'} {fmt_inr(abs(d))}"

    k1.metric("Revenue", fmt_inr(lm['revenue']) if lm['revenue']>0 else "NIL", delta_s(lm['revenue'],pm,'revenue'))
    k2.metric("Expenses", fmt_inr(lm['total_expenses']), delta_s(lm['total_expenses'],pm,'total_expenses'), delta_color="inverse")
    k3.metric("Net P/L", fmt_inr(lm['net_pl']), "Loss" if lm['net_pl']<0 else "Profit", delta_color="inverse" if lm['net_pl']<0 else "normal")
    k4.metric("Cash & Bank", fmt_inr(lm['bank']), delta_s(lm['bank'],pm,'bank'))
    k5.metric("Burn Rate", fmt_inr(lm['burn_rate']))
    k6.metric("Runway", f"{lm['runway']:.1f} mo" if lm['runway']<100 else "N/A")

    st.markdown("---")
    y1,y2,y3,y4 = st.columns(4)
    y1.metric("YTD Revenue", fmt_inr(ytd['revenue']) if ytd['revenue']>0 else "NIL")
    y2.metric("YTD Expenses", fmt_inr(ytd['total_expenses']))
    y3.metric("YTD Net P/L", fmt_inr(ytd['net_pl']))
    y4.metric("Months Loaded", f"{len(sorted_months)} of 12")

    st.markdown("---")

    if len(sorted_months) > 1:
        trend_df = pd.DataFrame([{'Month':get_month_label(mk), **monthly_metrics[mk]} for mk in sorted_months])
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df['Month'], y=trend_df['total_expenses'], name='Expenses', marker_color='#E74C3C', opacity=0.8))
            fig.add_trace(go.Bar(x=trend_df['Month'], y=trend_df['revenue'], name='Revenue', marker_color='#27AE60', opacity=0.8))
            fig.update_layout(title="Revenue vs Expenses", height=350, barmode='group',
                            font=dict(family="Inter"), margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.15))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['bank'], mode='lines+markers', name='Cash & Bank',
                                     line=dict(color='#2E86C1',width=3), marker=dict(size=8)))
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['borrowings'], mode='lines+markers', name='Borrowings',
                                     line=dict(color='#E8833A',width=2,dash='dash'), marker=dict(size=6)))
            fig2.update_layout(title="Cash & Borrowings", height=350, font=dict(family="Inter"),
                             margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.15))
            st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        exp_data = latest_mis[(latest_mis['statement']=='P&L') & (latest_mis['section']!='Revenue') & (latest_mis['pl_amount']>0)]
        exp_cat = exp_data.groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False).reset_index()
        exp_cat.columns = ['Category','Amount']
        if len(exp_cat) > 0:
            fig3 = px.pie(exp_cat, values='Amount', names='Category', title=f"Expense Mix — {get_month_label(latest_month)}",
                        color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig3.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"), legend=dict(orientation="h",y=-0.1))
            fig3.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
            st.plotly_chart(fig3, use_container_width=True)
    with c4:
        asset_data = latest_mis[(latest_mis['section'].isin(['FA','CA'])) & (latest_mis['bs_amount']>0)]
        asset_cat = asset_data.groupby('mis_category')['bs_amount'].sum().sort_values(ascending=False).reset_index()
        asset_cat.columns = ['Asset','Amount']
        if len(asset_cat) > 0:
            fig4 = px.bar(asset_cat, x='Asset', y='Amount', title="Asset Composition",
                        color_discrete_sequence=['#27AE60'])
            fig4.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"),
                             showlegend=False, xaxis_title="", yaxis_title="")
            fig4.update_traces(text=[fmt_inr(v) for v in asset_cat['Amount']], textposition='outside', textfont_size=11)
            st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Key Ratios")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Debt-Equity", f"{lm['de_ratio']:.1f}x")
    r2.metric("Current Ratio", f"{lm['current_ratio']:.1f}x")
    r3.metric("Total Borrowings", fmt_inr(lm['borrowings']))
    r4.metric("Net Worth", fmt_inr(lm['equity']))


# ═══════ PROFIT & LOSS ═══════
with tab2:
    st.markdown("#### Profit & Loss Statement — Monthly + YTD")

    all_categories = {}
    for mk in sorted_months:
        mis = month_data[mk]
        for section in ['Revenue','COGS','OpEx','Finance','Tax']:
            cats = mis[(mis['statement']=='P&L') & (mis['section']==section) & (mis['pl_amount']!=0)]['mis_category'].unique()
            if section not in all_categories: all_categories[section] = set()
            all_categories[section].update(cats)

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

    table_rows = []
    for label, row_type, section in pl_order:
        if row_type == "spacer": table_rows.append({"type":"spacer"}); continue
        if row_type == "header": table_rows.append({"type":"header","label":label}); continue
        if row_type == "items":
            for cat in sorted(all_categories.get(section, [])):
                row = {"type":"item","label":f"  {cat}"}
                ytd_v = 0
                for mk in sorted_months:
                    v = month_data[mk][(month_data[mk]['statement']=='P&L') & (month_data[mk]['section']==section) & (month_data[mk]['mis_category']==cat)]['pl_amount'].sum()
                    row[mk] = v; ytd_v += v
                row['ytd'] = ytd_v
                table_rows.append(row)
            continue
        if row_type == "total":
            row = {"type":"total","label":label}; ytd_v = 0
            metric = {'Revenue':'revenue','COGS':'cogs','OpEx':'opex','Finance':'finance','Tax':'tax'}.get(section,'')
            for mk in sorted_months:
                v = monthly_metrics[mk].get(metric, 0); row[mk] = v; ytd_v += v
            row['ytd'] = ytd_v; table_rows.append(row); continue
        if row_type == "grand":
            row = {"type":"grand","label":label}
            metric = {'gross':'gross_profit','ebitda':'ebitda','net':'net_pl'}.get(section, section)
            ytd_v = 0
            for mk in sorted_months:
                v = monthly_metrics[mk].get(metric, 0); row[mk] = v; ytd_v += v
            row['ytd'] = ytd_v; table_rows.append(row)

    th = "text-align:right; padding:10px 10px; font-weight:600; font-size:12px;"
    header_html = "<th style='text-align:left; padding:10px 14px; font-weight:600; min-width:200px;'>Particulars</th>"
    for mk in sorted_months: header_html += f"<th style='{th}'>{get_month_label(mk)}</th>"
    header_html += f"<th style='{th} background:#D6E4F0;'>YTD</th>"

    rows_html = ""
    ncols = len(sorted_months) + 2
    for row in table_rows:
        if row['type'] == 'spacer': rows_html += f"<tr><td colspan='{ncols}' style='padding:4px;'></td></tr>"; continue
        if row['type'] == 'header': rows_html += f"<tr><td colspan='{ncols}' style='padding:8px 14px; font-weight:700; color:#E8833A; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;'>{row['label']}</td></tr>"; continue
        bg = "#F8F9FA" if row['type']=='total' else ("#D6E4F0" if row['type']=='grand' else "transparent")
        fw = "700" if row['type'] in ('total','grand') else "400"
        bdr = "border-bottom:2px solid #1B2A4A;" if row['type'] in ('total','grand') else "border-bottom:1px solid #ECF0F1;"
        td = f"<td style='padding:7px 14px; font-weight:{fw}; {bdr}'>{row['label']}</td>"
        for mk in sorted_months:
            v = row.get(mk, 0)
            clr = "#E74C3C" if v < 0 else "#2C3E50"
            td += f"<td style='text-align:right; padding:7px 10px; font-weight:{fw}; color:{clr}; {bdr}; font-size:12px;'>{fmt_tbl(v)}</td>"
        yv = row.get('ytd', 0)
        yclr = "#E74C3C" if yv < 0 else "#2C3E50"
        td += f"<td style='text-align:right; padding:7px 10px; font-weight:700; color:{yclr}; {bdr}; background:#F0F4F8; font-size:12px;'>{fmt_tbl(yv)}</td>"
        rows_html += f"<tr style='background:{bg};'>{td}</tr>"

    st.markdown(f"<div style='overflow-x:auto;'><table style='width:100%; border-collapse:collapse; font-family:Inter,sans-serif; font-size:13px;'><thead><tr style='background:#1B2A4A; color:white;'>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>", unsafe_allow_html=True)

    if len(sorted_months) > 1:
        st.markdown("---")
        st.markdown("#### Expense Composition — Month on Month")
        exp_trend = []
        for mk in sorted_months:
            cats = month_data[mk][(month_data[mk]['statement']=='P&L') & (month_data[mk]['section'].isin(['COGS','OpEx'])) & (month_data[mk]['pl_amount']>0)]
            for cat_name, cat_val in cats.groupby('mis_category')['pl_amount'].sum().items():
                exp_trend.append({'Month': get_month_label(mk), 'Category': cat_name, 'Amount': cat_val})
        if exp_trend:
            edf = pd.DataFrame(exp_trend)
            fig_s = px.bar(edf, x='Month', y='Amount', color='Category', color_discrete_sequence=px.colors.qualitative.Set2)
            fig_s.update_layout(height=350, barmode='stack', font=dict(family="Inter"), margin=dict(t=20,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.2))
            st.plotly_chart(fig_s, use_container_width=True)


# ═══════ BALANCE SHEET ═══════
with tab3:
    st.markdown(f"#### Balance Sheet as at {get_month_label(latest_month)}")
    if prior_month: st.caption(f"Comparison with {get_month_label(prior_month)}")

    def build_bs_rows(mis_c, mis_p, sections):
        rows = []
        for sk, sl in sections:
            cd = mis_c[(mis_c['section']==sk) & (mis_c['bs_amount']!=0)]
            pd_data = mis_p[(mis_p['section']==sk)] if mis_p is not None else pd.DataFrame()
            if len(cd)==0 and len(pd_data)==0: continue

            rows.append({"type":"section","label":sl})
            cc = cd.groupby('mis_category')['bs_amount'].sum()
            pc = pd_data.groupby('mis_category')['bs_amount'].sum() if len(pd_data)>0 else pd.Series(dtype=float)
            is_liab = sk in ['Equity','Borrowings','CL']

            for cat in sorted(set(cc.index) | set(pc.index)):
                cv = cc.get(cat, 0); pv = pc.get(cat, 0)
                dcv = abs(cv) if is_liab else cv
                dpv = abs(pv) if is_liab else pv
                rows.append({"type":"item","label":cat,"current":dcv,"prior":dpv,"movement":dcv-dpv})

            sc = abs(cc.sum()) if is_liab else cc.sum()
            sp = abs(pc.sum()) if is_liab else pc.sum()
            rows.append({"type":"subtotal","label":sl,"current":sc,"prior":sp,"movement":sc-sp})

        gt_c = sum(r['current'] for r in rows if r['type']=='subtotal')
        gt_p = sum(r['prior'] for r in rows if r['type']=='subtotal')
        rows.append({"type":"grand","label":"TOTAL","current":gt_c,"prior":gt_p,"movement":gt_c-gt_p})
        return rows

    def render_bs_html(rows, show_prior):
        cols_h = f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{get_month_label(latest_month)}</th>"
        if show_prior:
            cols_h += f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{get_month_label(prior_month)}</th>"
            cols_h += "<th style='text-align:right; padding:6px 10px; font-size:11px;'>Movement</th>"
        span = '4' if show_prior else '2'
        html = f"<table style='width:100%; border-collapse:collapse; font-size:13px;'><thead><tr style='background:#D6E4F0;'><th style='text-align:left; padding:6px 10px;'>Particulars</th>{cols_h}</tr></thead><tbody>"
        for r in rows:
            if r['type']=='section':
                html += f"<tr><td colspan='{span}' style='padding:8px 10px; font-weight:700; color:#E8833A; font-size:11px;'>{r['label'].upper()}</td></tr>"
            else:
                bg = "#F2F2F2" if r['type']=='subtotal' else ("#1B2A4A" if r['type']=='grand' else "transparent")
                fc = "white" if r['type']=='grand' else "#2C3E50"
                fw = "700" if r['type'] in ('subtotal','grand') else "400"
                mc = "#27AE60" if r.get('movement',0)>0 else ("#E74C3C" if r.get('movement',0)<0 else "#95A5A6")
                rh = f"<td style='padding:5px 10px; font-weight:{fw}; color:{fc};'>{r['label']}</td>"
                rh += f"<td style='text-align:right; padding:5px 10px; font-weight:{fw}; color:{fc};'>{fmt_tbl(r['current'])}</td>"
                if show_prior:
                    rh += f"<td style='text-align:right; padding:5px 10px; color:{fc};'>{fmt_tbl(r['prior'])}</td>"
                    rh += f"<td style='text-align:right; padding:5px 10px; color:{mc}; font-size:12px;'>{fmt_tbl(r['movement'])}</td>"
                html += f"<tr style='background:{bg}; border-bottom:1px solid #ECF0F1;'>{rh}</tr>"
        html += "</tbody></table>"
        return html

    show_p = prior_month is not None
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Sources of Funds**")
        liab_rows = build_bs_rows(latest_mis, prior_mis, [("Equity","Equity"),("Borrowings","Borrowings"),("CL","Current Liabilities")])
        st.markdown(render_bs_html(liab_rows, show_p), unsafe_allow_html=True)
    with col_r:
        st.markdown("**Application of Funds**")
        asset_rows = build_bs_rows(latest_mis, prior_mis, [("FA","Fixed Assets"),("CA","Current Assets")])
        st.markdown(render_bs_html(asset_rows, show_p), unsafe_allow_html=True)

    lt = sum(r['current'] for r in liab_rows if r['type']=='grand')
    at = sum(r['current'] for r in asset_rows if r['type']=='grand')
    diff = abs(at - lt)
    if diff < 2:
        st.success(f"✅ Balance Sheet tallies — Assets ₹{at:,.0f} = Liabilities ₹{lt:,.0f}")
    else:
        st.error(f"⚠️ Difference of ₹{diff:,.0f} — Assets ₹{at:,.0f} vs Liabilities ₹{lt:,.0f}")


# ═══════ LEDGER DETAIL (internal only) ═══════
if not IS_CLIENT:
    with tab4:
        st.markdown("#### Ledger-Level Detail")
        sel_mk_label = st.selectbox("Month", [get_month_label(mk) for mk in sorted_months], index=len(sorted_months)-1, key="det_m")
        det_mk = sel_mk_label.replace("-","").lower()
        det_mis = month_data[det_mk]

        view_opt = st.radio("View", ["P&L Ledgers","BS Ledgers","All"], horizontal=True)
        if view_opt == "P&L Ledgers":
            detail = det_mis[det_mis['statement']=='P&L'][['ledger','group','mis_category','section','debit','credit','pl_amount']].copy()
            detail = detail[detail['pl_amount']!=0].sort_values('pl_amount', ascending=False)
            detail.columns = ['Ledger','Tally Group','MIS Category','Section','Debit','Credit','Net Amount']
        elif view_opt == "BS Ledgers":
            detail = det_mis[(det_mis['statement']=='BS') & (det_mis['ledger']!='Profit & Loss Account (Current Period)')][['ledger','group','mis_category','section','opening','closing','bs_amount']].copy()
            detail = detail[detail['closing']!=0].sort_values('bs_amount', ascending=False)
            detail.columns = ['Ledger','Tally Group','MIS Category','Section','Opening','Closing','BS Amount']
        else:
            detail = det_mis[det_mis['ledger']!='Profit & Loss Account (Current Period)'][['ledger','group','mis_category','statement','section','opening','debit','credit','closing']].copy()
            detail = detail[(detail['closing']!=0)|(detail['debit']!=0)].sort_values('closing', ascending=False)
            detail.columns = ['Ledger','Tally Group','MIS Category','Statement','Section','Opening','Debit','Credit','Closing']

        search = st.text_input("🔍 Search", "", key="det_s")
        if search: detail = detail[detail['Ledger'].str.contains(search, case=False, na=False)]
        st.dataframe(detail, use_container_width=True, hide_index=True)
        st.download_button("📥 Download CSV", detail.to_csv(index=False), f"ledger_{det_mk}.csv", "text/csv")

st.markdown("<div class='stca-footer'>Prepared by STCA Global, Chartered Accountants (FRN 016465S) • Confidential</div>", unsafe_allow_html=True)
