"""
Full Circle Studio — MIS Dashboard v4
Fixed: BS sign convention (signed_closing), TDS mapping, client mode
Deploy: streamlit run fcs_mis_app_v4.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

IS_CLIENT_MODE = st.query_params.get("mode", "").lower() == "client"

st.set_page_config(
    page_title="Full Circle Studio — MIS",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed" if IS_CLIENT_MODE else "expanded"
)
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
IS_CLIENT = IS_CLIENT_MODE

# ─── Styling ───
client_css = """
    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    /* Hide hamburger menu */
    [data-testid="stMainMenu"] { display: none !important; }
    #MainMenu { display: none !important; }
    button[kind="header"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    /* Hide Streamlit footer */
    footer { display: none !important; }
    [data-testid="stFooter"] { display: none !important; }
    /* Hide deploy button */
    [data-testid="stToolbar"] { display: none !important; }
    .stDeployButton { display: none !important; }
""" if IS_CLIENT else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.main-header {{ background: linear-gradient(135deg, #1B2A4A 0%, #2E86C1 100%); padding: 28px 32px; border-radius: 12px; margin-bottom: 24px; color: white; }}
.main-header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
.main-header p {{ margin: 4px 0 0; font-size: 13px; opacity: 0.8; }}
.stca-footer {{ text-align: center; padding: 20px 0 8px; color: #95A5A6; font-size: 11px; border-top: 1px solid #E0E0E0; margin-top: 24px; }}
.month-tag {{ display: inline-block; background: #D6E4F0; color: #1B2A4A; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 2px; }}
{client_css}
</style>
""", unsafe_allow_html=True)

# ─── MIS Mapping ───
# Key fix: TDS Ledgers → CL (payable), not CA
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
    "TDS Ledgers": ("TDS Payable", "BS", "CL"),     # FIXED: was CA
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

def fmt_inr(val):
    if pd.isna(val) or val == 0: return "—"
    sign = "" if val > 0 else "(-)"
    a = abs(val)
    if a >= 1e7: return f"{sign}₹{a/1e7:,.2f} Cr"
    if a >= 1e5: return f"{sign}₹{a/1e5:,.2f} L"
    return f"{sign}₹{a:,.0f}"

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

    # ── KEY FIX: Compute true signed closing ──
    # Tally TB shows all closings as positive. The true algebraic sign is:
    #   signed_closing = opening + debit - credit
    #   Positive = debit balance (assets, expenses)
    #   Negative = credit balance (liabilities, income)
    m['signed_closing'] = m['opening'] + m['debit'] - m['credit']

    # P&L amounts (unchanged — these use debit/credit directly)
    m['pl_amount'] = 0.0
    rev = m['section'] == 'Revenue'
    exp = (m['statement'] == 'P&L') & ~rev
    m.loc[rev, 'pl_amount'] = m.loc[rev, 'credit'] - m.loc[rev, 'debit']
    m.loc[exp, 'pl_amount'] = m.loc[exp, 'debit'] - m.loc[exp, 'credit']

    # BS amounts: use signed_closing instead of raw closing
    m['bs_amount'] = 0.0
    bs = m['statement'] == 'BS'
    m.loc[bs, 'bs_amount'] = m.loc[bs, 'signed_closing']

    # ── P&L PLUG ──
    # Net of all P&L signed_closings = net debit if loss, net credit if profit
    # This goes to Equity as "Current Period P&L"
    net_pl_signed = m.loc[m['statement'] == 'P&L', 'signed_closing'].sum()
    # net_pl_signed: positive = loss (net debit), negative = profit (net credit)

    pl_plug = pd.DataFrame([{
        'ledger': 'Profit & Loss Account (Current Period)',
        'opening': 0, 'debit': 0, 'credit': 0, 'closing': 0,
        'group': 'Reserves & Surplus',
        'mis_category': 'Current Period P&L',
        'statement': 'BS', 'section': 'Equity',
        'pl_amount': 0,
        'signed_closing': net_pl_signed,
        'bs_amount': net_pl_signed,
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

# ─── Sidebar ───
if not IS_CLIENT:
    with st.sidebar:
        st.markdown("### 📁 Data Management")
        existing_master = load_master()
        if existing_master is not None:
            st.success(f"✓ Master — {len(existing_master)} ledgers")
            if st.checkbox("Re-upload Master"):
                mf = st.file_uploader("Upload new Master", type=['xlsx','xls'], key="master_new")
                if mf: save_master(parse_master(mf)); st.rerun()
        else:
            mf = st.file_uploader("Upload Master", type=['xlsx','xls'], key="master_init")
            if mf: save_master(parse_master(mf)); st.rerun()
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
                save_month(month_key, tb_parsed); st.success(f"✓ {selected_month_label} saved"); st.rerun()
        st.markdown("---")
        all_months_sb = load_all_months()
        if all_months_sb:
            st.markdown("**Loaded Months**")
            sk = sorted(all_months_sb.keys(), key=month_sort_key)
            st.markdown(" ".join([f"<span class='month-tag'>{get_month_label(k)}</span>" for k in sk]), unsafe_allow_html=True)
            with st.expander("🗑️ Remove a month"):
                dl = st.selectbox("Month", [get_month_label(k) for k in sk], key="del_sel")
                if st.button("Remove"): delete_month(dl.replace("-","").lower()); st.rerun()
        st.markdown("---")
        st.markdown("**🔗 Client Share Link**")
        base_url = st.text_input("App URL", value="http://localhost:8501", key="base_url")
        st.code(f"{base_url}/?mode=client", language=None)
        st.caption("Client sees Dashboard, P&L, BS only.")
        st.markdown("---")
        st.markdown("⚠️ **Important:** Upload **standalone monthly** TBs (e.g. 1-Jun-26 to 30-Jun-26), not inception-to-date. Inception TBs will overstate the P&L.")
        st.markdown("---")
        st.markdown("<div style='text-align:center; font-size:10px; color:#95A5A6;'>STCA Global • FRN 016465S</div>", unsafe_allow_html=True)

master = load_master()
all_months = load_all_months()
if master is None or not all_months:
    st.markdown("""<div class='main-header'><h1>Full Circle Studio Private Limited</h1><p>Management Information System</p></div>""", unsafe_allow_html=True)
    if IS_CLIENT: st.info("Dashboard is being set up. Please check back shortly.")
    elif master is None: st.info("👈 Upload the **Master** in the sidebar.")
    else: st.info("👈 Upload a **Trial Balance** for any month.")
    st.stop()

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
    gross = rev - cogs; ebitda = gross - opex; net = ebitda - fin - tax
    tot_exp = cogs + opex + fin
    bank = mis[mis['mis_category'].isin(['Bank Balances','Bank Deposits'])]['bs_amount'].sum()
    # For BS metrics, use signed_closing convention:
    # Assets (FA, CA): positive signed = debit balance
    # Liabilities: negative signed = credit balance → take abs for display
    borr_signed = mis[mis['section']=='Borrowings']['bs_amount'].sum()  # negative (credit)
    eq_signed = mis[mis['section']=='Equity']['bs_amount'].sum()  # negative if net credit (profit), mixed if loss
    fa = mis[mis['section']=='FA']['bs_amount'].sum()  # positive (debit)
    ca = mis[mis['section']=='CA']['bs_amount'].sum()  # positive (debit)
    cl_signed = mis[mis['section']=='CL']['bs_amount'].sum()  # negative (credit)

    monthly_metrics[mk] = {
        'revenue': rev, 'cogs': cogs, 'gross_profit': gross, 'opex': opex,
        'ebitda': ebitda, 'finance': fin, 'tax': tax, 'net_pl': net,
        'total_expenses': tot_exp, 'bank': bank,
        'borrowings': abs(borr_signed),  # display as positive
        'equity': -eq_signed,  # flip: credit equity shows as positive
        'fa': fa, 'ca': ca, 'cl': abs(cl_signed),
        'burn_rate': tot_exp,
        'runway': bank / tot_exp if tot_exp > 0 else 0,
        'de_ratio': abs(borr_signed) / abs(eq_signed) if eq_signed != 0 else 0,
        'current_ratio': ca / abs(cl_signed) if cl_signed != 0 else 0,
    }

lm = monthly_metrics[latest_month]
pm = monthly_metrics[prior_month] if prior_month else None
ytd = {}
for key in ['revenue','cogs','opex','finance','tax','total_expenses']:
    ytd[key] = sum(monthly_metrics[mk][key] for mk in sorted_months)
ytd['gross_profit'] = ytd['revenue'] - ytd['cogs']
ytd['ebitda'] = ytd['gross_profit'] - ytd['opex']
ytd['net_pl'] = ytd['ebitda'] - ytd['finance'] - ytd['tax']

period_range = f"{get_month_label(sorted_months[0])} to {get_month_label(sorted_months[-1])}"
client_badge = " &nbsp;•&nbsp; <span style='background:rgba(255,255,255,0.2); padding:2px 10px; border-radius:10px; font-size:11px;'>Client View</span>" if IS_CLIENT else ""
st.markdown(f"""<div class='main-header'><h1>Full Circle Studio Private Limited</h1>
<p>Management Information System &nbsp;•&nbsp; {period_range}{client_badge}</p></div>""", unsafe_allow_html=True)

if IS_CLIENT:
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Profit & Loss", "🏦 Balance Sheet", "🔍 Ledger Detail"])

# ═══════ DASHBOARD ═══════
with tab1:
    if lm['revenue'] == 0:
        st.warning("🚧 **Pre-Launch Phase** — No revenue recorded in the latest month.")
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    def ds(cv, pv, key):
        if pv is None: return None
        d = cv - pv[key]
        return f"{'↑' if d>0 else '↓'} {fmt_inr(abs(d))}" if d != 0 else None
    k1.metric("Revenue", fmt_inr(lm['revenue']) if lm['revenue']>0 else "NIL", ds(lm['revenue'],pm,'revenue'))
    k2.metric("Expenses", fmt_inr(lm['total_expenses']), ds(lm['total_expenses'],pm,'total_expenses'), delta_color="inverse")
    k3.metric("Net P/L", fmt_inr(lm['net_pl']), "Loss" if lm['net_pl']<0 else "Profit", delta_color="inverse" if lm['net_pl']<0 else "normal")
    k4.metric("Cash & Bank", fmt_inr(lm['bank']), ds(lm['bank'],pm,'bank'))
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
            fig.update_layout(title="Revenue vs Expenses", height=350, barmode='group', font=dict(family="Inter"), margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.15))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['bank'], mode='lines+markers', name='Cash & Bank', line=dict(color='#2E86C1',width=3), marker=dict(size=8)))
            fig2.add_trace(go.Scatter(x=trend_df['Month'], y=trend_df['borrowings'], mode='lines+markers', name='Borrowings', line=dict(color='#E8833A',width=2,dash='dash'), marker=dict(size=6)))
            fig2.update_layout(title="Cash & Borrowings", height=350, font=dict(family="Inter"), margin=dict(t=40,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.15))
            st.plotly_chart(fig2, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        ed = latest_mis[(latest_mis['statement']=='P&L') & (latest_mis['section']!='Revenue') & (latest_mis['pl_amount']>0)]
        ec = ed.groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False).reset_index()
        ec.columns = ['Category','Amount']
        if len(ec) > 0:
            fig3 = px.pie(ec, values='Amount', names='Category', title=f"Expense Mix — {get_month_label(latest_month)}", color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig3.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"), legend=dict(orientation="h",y=-0.1))
            fig3.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
            st.plotly_chart(fig3, use_container_width=True)
    with c4:
        # Assets: positive signed_closing
        ad = latest_mis[(latest_mis['section'].isin(['FA','CA'])) & (latest_mis['bs_amount']>0)]
        ac = ad.groupby('mis_category')['bs_amount'].sum().sort_values(ascending=False).reset_index()
        ac.columns = ['Asset','Amount']
        if len(ac) > 0:
            fig4 = px.bar(ac, x='Asset', y='Amount', title="Asset Composition", color_discrete_sequence=['#27AE60'])
            fig4.update_layout(height=350, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"), showlegend=False, xaxis_title="", yaxis_title="")
            fig4.update_traces(text=[fmt_inr(v) for v in ac['Amount']], textposition='outside', textfont_size=11)
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
        ("REVENUE","header","Revenue"), ("_","items","Revenue"), ("Total Revenue","total","Revenue"), ("","spacer",None),
        ("COST OF REVENUE","header","COGS"), ("_","items","COGS"), ("Total Cost of Revenue","total","COGS"), ("","spacer",None),
        ("GROSS PROFIT","grand","gross"), ("","spacer",None),
        ("OPERATING EXPENSES","header","OpEx"), ("_","items","OpEx"), ("Total Operating Expenses","total","OpEx"), ("","spacer",None),
        ("EBITDA","grand","ebitda"), ("","spacer",None),
        ("FINANCE COSTS","header","Finance"), ("_","items","Finance"), ("","spacer",None),
        ("NET PROFIT / (LOSS)","grand","net"),
    ]
    table_rows = []
    for label, rt, section in pl_order:
        if rt == "spacer": table_rows.append({"type":"spacer"}); continue
        if rt == "header": table_rows.append({"type":"header","label":label}); continue
        if rt == "items":
            for cat in sorted(all_categories.get(section, [])):
                row = {"type":"item","label":f"  {cat}"}; yv = 0
                for mk in sorted_months:
                    v = month_data[mk][(month_data[mk]['statement']=='P&L')&(month_data[mk]['section']==section)&(month_data[mk]['mis_category']==cat)]['pl_amount'].sum()
                    row[mk] = v; yv += v
                row['ytd'] = yv; table_rows.append(row); continue
        if rt == "total":
            row = {"type":"total","label":label}; yv = 0
            metric = {'Revenue':'revenue','COGS':'cogs','OpEx':'opex','Finance':'finance','Tax':'tax'}.get(section,'')
            for mk in sorted_months: v = monthly_metrics[mk].get(metric,0); row[mk] = v; yv += v
            row['ytd'] = yv; table_rows.append(row); continue
        if rt == "grand":
            row = {"type":"grand","label":label}; yv = 0
            metric = {'gross':'gross_profit','ebitda':'ebitda','net':'net_pl'}.get(section, section)
            for mk in sorted_months: v = monthly_metrics[mk].get(metric,0); row[mk] = v; yv += v
            row['ytd'] = yv; table_rows.append(row)

    th = "text-align:right; padding:10px 10px; font-weight:600; font-size:12px;"
    hh = "<th style='text-align:left; padding:10px 14px; font-weight:600; min-width:200px;'>Particulars</th>"
    for mk in sorted_months: hh += f"<th style='{th}'>{get_month_label(mk)}</th>"
    hh += f"<th style='{th} background:#D6E4F0;'>YTD</th>"
    rh = ""; nc = len(sorted_months) + 2
    for row in table_rows:
        if row['type']=='spacer': rh += f"<tr><td colspan='{nc}' style='padding:4px;'></td></tr>"; continue
        if row['type']=='header': rh += f"<tr><td colspan='{nc}' style='padding:8px 14px; font-weight:700; color:#E8833A; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;'>{row['label']}</td></tr>"; continue
        bg = "#F8F9FA" if row['type']=='total' else ("#D6E4F0" if row['type']=='grand' else "transparent")
        fw = "700" if row['type'] in ('total','grand') else "400"
        bdr = "border-bottom:2px solid #1B2A4A;" if row['type'] in ('total','grand') else "border-bottom:1px solid #ECF0F1;"
        td = f"<td style='padding:7px 14px; font-weight:{fw}; {bdr}'>{row['label']}</td>"
        for mk in sorted_months:
            v = row.get(mk,0); clr = "#E74C3C" if v < 0 else "#2C3E50"
            td += f"<td style='text-align:right; padding:7px 10px; font-weight:{fw}; color:{clr}; {bdr}; font-size:12px;'>{fmt_tbl(v)}</td>"
        yv = row.get('ytd',0); yc = "#E74C3C" if yv < 0 else "#2C3E50"
        td += f"<td style='text-align:right; padding:7px 10px; font-weight:700; color:{yc}; {bdr}; background:#F0F4F8; font-size:12px;'>{fmt_tbl(yv)}</td>"
        rh += f"<tr style='background:{bg};'>{td}</tr>"
    st.markdown(f"<div style='overflow-x:auto;'><table style='width:100%; border-collapse:collapse; font-family:Inter,sans-serif; font-size:13px;'><thead><tr style='background:#1B2A4A; color:white;'>{hh}</tr></thead><tbody>{rh}</tbody></table></div>", unsafe_allow_html=True)
    if len(sorted_months) > 1:
        st.markdown("---"); st.markdown("#### Expense Composition — Month on Month")
        et = []
        for mk in sorted_months:
            cats = month_data[mk][(month_data[mk]['statement']=='P&L')&(month_data[mk]['section'].isin(['COGS','OpEx']))&(month_data[mk]['pl_amount']>0)]
            for cn, cv in cats.groupby('mis_category')['pl_amount'].sum().items():
                et.append({'Month':get_month_label(mk),'Category':cn,'Amount':cv})
        if et:
            edf = pd.DataFrame(et)
            fs = px.bar(edf, x='Month', y='Amount', color='Category', color_discrete_sequence=px.colors.qualitative.Set2)
            fs.update_layout(height=350, barmode='stack', font=dict(family="Inter"), margin=dict(t=20,b=20,l=20,r=20), legend=dict(orientation="h",y=-0.2))
            st.plotly_chart(fs, use_container_width=True)

# ═══════ BALANCE SHEET (FIXED) ═══════
with tab3:
    st.markdown(f"#### Balance Sheet as at {get_month_label(latest_month)}")
    if prior_month: st.caption(f"Comparison with {get_month_label(prior_month)}")

    def build_bs_rows(mis_c, mis_p, sections):
        """
        Build BS rows using signed_closing convention:
        - bs_amount = signed_closing (positive=debit, negative=credit)
        - For LIABILITIES display: flip sign → credit becomes positive, debit becomes negative
        - For ASSETS display: use as-is → debit is positive
        """
        rows = []
        is_liab_side = sections[0][0] in ['Equity','Borrowings','CL']

        for sk, sl in sections:
            cd = mis_c[mis_c['section']==sk]
            pd_df = mis_p[mis_p['section']==sk] if mis_p is not None else pd.DataFrame()

            cc = cd.groupby('mis_category')['bs_amount'].sum()
            pc = pd_df.groupby('mis_category')['bs_amount'].sum() if len(pd_df) > 0 else pd.Series(dtype=float)

            active_cats = set()
            for cat in set(cc.index) | set(pc.index):
                cv = cc.get(cat, 0); pv = pc.get(cat, 0)
                if cv != 0 or pv != 0: active_cats.add(cat)

            if not active_cats: continue
            rows.append({"type": "section", "label": sl})

            sec_curr = 0; sec_prev = 0
            for cat in sorted(active_cats):
                cv_raw = cc.get(cat, 0); pv_raw = pc.get(cat, 0)
                # For liabilities: flip sign (credit balance → positive display)
                # For assets: keep as-is (debit balance → positive display)
                if is_liab_side:
                    cv_display = -cv_raw  # credit (neg) → positive; debit (pos) → negative
                    pv_display = -pv_raw
                else:
                    cv_display = cv_raw
                    pv_display = pv_raw
                sec_curr += cv_display; sec_prev += pv_display
                rows.append({"type":"item","label":cat,"current":cv_display,"prior":pv_display,"movement":cv_display - pv_display})

            rows.append({"type":"subtotal","label":sl,"current":sec_curr,"prior":sec_prev,"movement":sec_curr - sec_prev})

        gt_c = sum(r['current'] for r in rows if r['type']=='subtotal')
        gt_p = sum(r['prior'] for r in rows if r['type']=='subtotal')
        rows.append({"type":"grand","label":"TOTAL","current":gt_c,"prior":gt_p,"movement":gt_c - gt_p})
        return rows

    def render_bs_html(rows, show_prior, latest_lbl, prior_lbl):
        ch = f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{latest_lbl}</th>"
        if show_prior:
            ch += f"<th style='text-align:right; padding:6px 10px; font-size:11px;'>{prior_lbl}</th>"
            ch += "<th style='text-align:right; padding:6px 10px; font-size:11px;'>Movement</th>"
        span = '4' if show_prior else '2'
        html = f"<table style='width:100%; border-collapse:collapse; font-size:13px;'><thead><tr style='background:#D6E4F0;'><th style='text-align:left; padding:6px 10px;'>Particulars</th>{ch}</tr></thead><tbody>"
        for r in rows:
            if r['type']=='section':
                html += f"<tr><td colspan='{span}' style='padding:8px 10px; font-weight:700; color:#E8833A; font-size:11px;'>{r['label'].upper()}</td></tr>"
            else:
                bg = "#F2F2F2" if r['type']=='subtotal' else ("#1B2A4A" if r['type']=='grand' else "transparent")
                fc = "white" if r['type']=='grand' else "#2C3E50"
                fw = "700" if r['type'] in ('subtotal','grand') else "400"
                mc = "#27AE60" if r.get('movement',0) > 0 else ("#E74C3C" if r.get('movement',0) < 0 else "#95A5A6")
                cv_color = "#E74C3C" if r['current'] < 0 else fc
                rr = f"<td style='padding:5px 10px; font-weight:{fw}; color:{fc};'>{r['label']}</td>"
                rr += f"<td style='text-align:right; padding:5px 10px; font-weight:{fw}; color:{cv_color};'>{fmt_tbl(r['current'])}</td>"
                if show_prior:
                    pv_color = "#E74C3C" if r['prior'] < 0 else fc
                    rr += f"<td style='text-align:right; padding:5px 10px; color:{pv_color};'>{fmt_tbl(r['prior'])}</td>"
                    rr += f"<td style='text-align:right; padding:5px 10px; color:{mc}; font-size:12px;'>{fmt_tbl(r['movement'])}</td>"
                html += f"<tr style='background:{bg}; border-bottom:1px solid #ECF0F1;'>{rr}</tr>"
        html += "</tbody></table>"; return html

    show_p = prior_month is not None
    ll = get_month_label(latest_month); pl = get_month_label(prior_month) if prior_month else ""
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Sources of Funds**")
        liab_rows = build_bs_rows(latest_mis, prior_mis, [("Equity","Equity"),("Borrowings","Borrowings"),("CL","Current Liabilities")])
        st.markdown(render_bs_html(liab_rows, show_p, ll, pl), unsafe_allow_html=True)
    with col_r:
        st.markdown("**Application of Funds**")
        asset_rows = build_bs_rows(latest_mis, prior_mis, [("FA","Fixed Assets"),("CA","Current Assets")])
        st.markdown(render_bs_html(asset_rows, show_p, ll, pl), unsafe_allow_html=True)
    lt = sum(r['current'] for r in liab_rows if r['type']=='grand')
    at = sum(r['current'] for r in asset_rows if r['type']=='grand')
    diff = abs(at - lt)
    if diff < 2:
        st.success(f"✅ Balance Sheet tallies — Assets ₹{at:,.0f} = Liabilities ₹{lt:,.0f}")
    else:
        st.error(f"⚠️ Difference: ₹{diff:,.0f} — Assets ₹{at:,.0f} vs Liabilities ₹{lt:,.0f}")

# ═══════ LEDGER DETAIL ═══════
if not IS_CLIENT:
    with tab4:
        st.markdown("#### Ledger-Level Detail")
        sl = st.selectbox("Month", [get_month_label(mk) for mk in sorted_months], index=len(sorted_months)-1, key="dm")
        dmk = sl.replace("-","").lower(); dm = month_data[dmk]
        vo = st.radio("View", ["P&L","BS","All"], horizontal=True)
        if vo == "P&L":
            d = dm[dm['statement']=='P&L'][['ledger','group','mis_category','section','debit','credit','pl_amount']].copy()
            d = d[d['pl_amount']!=0].sort_values('pl_amount', ascending=False)
            d.columns = ['Ledger','Tally Group','MIS Category','Section','Debit','Credit','Net Amount']
        elif vo == "BS":
            d = dm[(dm['statement']=='BS')&(dm['ledger']!='Profit & Loss Account (Current Period)')][['ledger','group','mis_category','section','opening','closing','bs_amount','signed_closing']].copy()
            d = d[d['closing']!=0].sort_values('bs_amount', ascending=False)
            d.columns = ['Ledger','Tally Group','MIS Category','Section','Opening','Closing','BS Amount','Signed Closing']
        else:
            d = dm[dm['ledger']!='Profit & Loss Account (Current Period)'][['ledger','group','mis_category','statement','section','debit','credit','closing','signed_closing']].copy()
            d = d[(d['closing']!=0)|(d['debit']!=0)].sort_values('signed_closing', ascending=False)
            d.columns = ['Ledger','Tally Group','MIS Category','Statement','Section','Debit','Credit','Closing','Signed']
        s = st.text_input("🔍 Search", "", key="ds")
        if s: d = d[d['Ledger'].str.contains(s, case=False, na=False)]
        st.dataframe(d, use_container_width=True, hide_index=True)
        st.download_button("📥 CSV", d.to_csv(index=False), f"ledger_{dmk}.csv", "text/csv")

st.markdown("<div class='stca-footer'>Prepared by STCA Global, Chartered Accountants (FRN 016465S) • Confidential</div>", unsafe_allow_html=True)
