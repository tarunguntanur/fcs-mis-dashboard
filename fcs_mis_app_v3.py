"""
Full Circle Studio — MIS Dashboard v5
Professional design, STCA branding, signed_closing BS fix
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# ─── Client mode detection BEFORE set_page_config ───
IS_CLIENT = st.query_params.get("mode", "").lower() == "client"

st.set_page_config(
    page_title="Full Circle Studio — MIS | STCA Global",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed" if IS_CLIENT else "expanded"
)

DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)

# ─── Professional Design System ───
NAVY = "#0F1B2D"
DARK_BLUE = "#1A2B4A"
MID_BLUE = "#2563EB"
LIGHT_BLUE = "#E8F0FE"
ACCENT = "#D97706"  # Warm amber
GREEN = "#059669"
RED = "#DC2626"
MUTED = "#6B7280"
LIGHT_BG = "#F9FAFB"
CARD_BG = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#111827"
TEXT_SECONDARY = "#4B5563"

client_hide = """
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
[data-testid="stMainMenu"],[data-testid="stToolbar"],
[data-testid="stFooter"],header[data-testid="stHeader"],
footer,.stDeployButton,#MainMenu,button[kind="header"]
{ display: none !important; }
""" if IS_CLIENT else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', -apple-system, sans-serif; color: {TEXT}; }}
{client_hide}

.report-header {{
    background: linear-gradient(135deg, {NAVY} 0%, {DARK_BLUE} 60%, #1E3A5F 100%);
    padding: 32px 36px 28px; border-radius: 14px; margin-bottom: 28px; color: white;
    position: relative; overflow: hidden;
}}
.report-header::after {{
    content: ''; position: absolute; top: -50%; right: -10%; width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(37,99,235,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.report-header .company {{ font-size: 26px; font-weight: 700; letter-spacing: -0.5px; margin: 0; }}
.report-header .subtitle {{ font-size: 13px; opacity: 0.6; margin-top: 2px; letter-spacing: 0.5px; text-transform: uppercase; }}
.report-header .period-box {{
    margin-top: 16px; display: inline-flex; gap: 24px; background: rgba(255,255,255,0.08);
    padding: 10px 20px; border-radius: 8px; font-size: 13px;
}}
.report-header .period-label {{ opacity: 0.5; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
.report-header .period-value {{ font-weight: 600; margin-top: 2px; }}
.report-header .preparer {{
    position: absolute; bottom: 16px; right: 24px; font-size: 11px; opacity: 0.4;
    text-align: right; z-index: 1;
}}

.kpi-card {{
    background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px;
    padding: 20px 22px; height: 100%;
    transition: box-shadow 0.2s;
}}
.kpi-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
.kpi-label {{ font-size: 11px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }}
.kpi-value {{ font-size: 26px; font-weight: 700; color: {TEXT}; margin: 8px 0 4px; font-family: 'JetBrains Mono', monospace; }}
.kpi-sub {{ font-size: 12px; font-weight: 500; }}
.kpi-dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}

.section-title {{
    font-size: 14px; font-weight: 700; color: {DARK_BLUE}; text-transform: uppercase;
    letter-spacing: 1px; margin: 28px 0 16px; padding-bottom: 8px;
    border-bottom: 2px solid {MID_BLUE};
}}

.ratio-card {{
    background: {LIGHT_BG}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 16px 20px; text-align: center;
}}
.ratio-value {{ font-size: 24px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: {DARK_BLUE}; }}
.ratio-label {{ font-size: 11px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}

.stca-footer {{
    text-align: center; padding: 24px 0 12px; color: {MUTED}; font-size: 11px;
    border-top: 1px solid {BORDER}; margin-top: 32px;
}}
.stca-footer strong {{ color: {TEXT_SECONDARY}; }}

.month-tag {{ display: inline-block; background: {LIGHT_BLUE}; color: {DARK_BLUE}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 2px; }}

.confidential {{
    background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px;
    padding: 8px 16px; font-size: 11px; color: #92400E; text-align: center;
    margin-bottom: 20px; font-weight: 500;
}}
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
    "TDS Ledgers": ("TDS Payable", "BS", "CL"),
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

def fmt_inr(val, compact=True):
    if pd.isna(val) or val == 0: return "—"
    sign = "(-)" if val < 0 else ""
    a = abs(val)
    if compact:
        if a >= 1e7: return f"{sign}₹{a/1e7:,.2f} Cr"
        if a >= 1e5: return f"{sign}₹{a/1e5:,.2f} L"
        if a >= 1e3: return f"{sign}₹{a/1e3:,.1f}K"
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
    tb = df.iloc[data_start:].copy(); tb.columns = range(len(tb.columns))
    tb = tb[[0,1,2,3,4]]; tb.columns = ['ledger','opening','debit','credit','closing']
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
    ms = df.iloc[data_start:][[1,2]].copy(); ms.columns = ['ledger','group']
    ms = ms.dropna(subset=['ledger'])
    ms['ledger'] = ms['ledger'].astype(str).str.strip()
    ms['group'] = ms['group'].astype(str).str.strip()
    return ms

def apply_mapping(tb, master):
    m = tb.merge(master[['ledger','group']], on='ledger', how='left')
    m['mis_category'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[0])
    m['statement'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[1])
    m['section'] = m['group'].map(lambda g: GROUP_MAP.get(g, ("Unmapped","BS","CA"))[2])
    m['signed_closing'] = m['opening'] + m['debit'] - m['credit']
    m['pl_amount'] = 0.0
    rev = m['section'] == 'Revenue'; exp = (m['statement'] == 'P&L') & ~rev
    m.loc[rev, 'pl_amount'] = m.loc[rev, 'credit'] - m.loc[rev, 'debit']
    m.loc[exp, 'pl_amount'] = m.loc[exp, 'debit'] - m.loc[exp, 'credit']
    m['bs_amount'] = 0.0
    bs = m['statement'] == 'BS'; m.loc[bs, 'bs_amount'] = m.loc[bs, 'signed_closing']
    net_pl_signed = m.loc[m['statement'] == 'P&L', 'signed_closing'].sum()
    pl_plug = pd.DataFrame([{
        'ledger': 'Profit & Loss Account (Current Period)', 'opening': 0, 'debit': 0, 'credit': 0,
        'closing': 0, 'group': 'Reserves & Surplus', 'mis_category': 'Current Period P&L',
        'statement': 'BS', 'section': 'Equity', 'pl_amount': 0,
        'signed_closing': net_pl_signed, 'bs_amount': net_pl_signed,
    }])
    return pd.concat([m, pl_plug], ignore_index=True)

def save_master(m): m.to_csv(DATA_DIR / "master.csv", index=False)
def load_master():
    p = DATA_DIR / "master.csv"; return pd.read_csv(p) if p.exists() else None
def save_month(mk, tb): tb.to_csv(DATA_DIR / f"tb_{mk}.csv", index=False)
def load_all_months():
    return {f.stem.replace("tb_",""):pd.read_csv(f) for f in sorted(DATA_DIR.glob("tb_*.csv"))}
def delete_month(mk):
    p = DATA_DIR / f"tb_{mk}.csv"
    if p.exists(): p.unlink()
def msort(k):
    for i, m in enumerate(["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]):
        if k.lower().startswith(m): return i
    return 99
def mlabel(k): return k[:3].title() + "-" + k[3:]
def stot(mis, stmt, sec, col='pl_amount'):
    return mis[(mis['statement']==stmt)&(mis['section']==sec)][col].sum()

def kpi_card(label, value, sub_text="", sub_color=MUTED, dot_color=None):
    dot = f"<span class='kpi-dot' style='background:{dot_color};'></span>" if dot_color else ""
    return f"""<div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub' style='color:{sub_color};'>{dot}{sub_text}</div>
    </div>"""

# ─── Sidebar ───
if not IS_CLIENT:
    with st.sidebar:
        st.markdown("### Data Management")
        existing_master = load_master()
        if existing_master is not None:
            st.success(f"✓ Master — {len(existing_master)} ledgers")
            if st.checkbox("Re-upload Master"):
                mf = st.file_uploader("New Master", type=['xlsx','xls'], key="mn")
                if mf: save_master(parse_master(mf)); st.rerun()
        else:
            mf = st.file_uploader("Upload Master", type=['xlsx','xls'], key="mi")
            if mf: save_master(parse_master(mf)); st.rerun()
        st.markdown("---")
        st.markdown("**Monthly Trial Balance**")
        fy = st.selectbox("FY", ["2026-27","2025-26"], index=0)
        fys = int(fy[:4])
        mopts = [f"{m}-{str(fys)[2:]}" if i<9 else f"{m}-{str(fys+1)[2:]}" for i,m in enumerate(FY_MONTHS)]
        sml = st.selectbox("Month", mopts); mk = sml.replace("-","").lower()
        tf = st.file_uploader("Upload TB", type=['xlsx','xls'], key="tu")
        if tf and load_master() is not None:
            tp, per = parse_tb(tf)
            if tp is not None: save_month(mk, tp); st.success(f"✓ {sml} saved"); st.rerun()
        st.markdown("---")
        ams = load_all_months()
        if ams:
            st.markdown("**Loaded Months**")
            sk = sorted(ams.keys(), key=msort)
            st.markdown(" ".join([f"<span class='month-tag'>{mlabel(k)}</span>" for k in sk]), unsafe_allow_html=True)
            with st.expander("Remove a month"):
                dl = st.selectbox("Month", [mlabel(k) for k in sk], key="ds")
                if st.button("Remove"): delete_month(dl.replace("-","").lower()); st.rerun()
        st.markdown("---")
        st.markdown("**Client Link**")
        bu = st.text_input("App URL", value="https://fcs-mis-dashboard-6fnefgshckmu8qvx3ugn5j.streamlit.app", key="bu")
        st.code(f"{bu}/?mode=client", language=None)
        st.markdown("---")
        st.caption("⚠️ Upload standalone monthly TBs, not inception-to-date.")

master = load_master(); all_months = load_all_months()
if master is None or not all_months:
    st.markdown("""<div class='report-header'><p class='company'>Full Circle Studio Private Limited</p>
    <p class='subtitle'>Management Information System</p></div>""", unsafe_allow_html=True)
    if IS_CLIENT: st.info("The MIS report is being prepared. Please check back shortly.")
    elif master is None: st.info("Upload the **Master** (List of Ledgers) in the sidebar to begin.")
    else: st.info("Master loaded. Upload a **Trial Balance** for any month to generate the MIS.")
    st.stop()

sorted_months = sorted(all_months.keys(), key=msort)
month_data = {}
for mk in sorted_months:
    tb = all_months[mk]
    for c in ['opening','debit','credit','closing']:
        tb[c] = pd.to_numeric(tb[c], errors='coerce').fillna(0)
    month_data[mk] = apply_mapping(tb, master)

latest = sorted_months[-1]; lmis = month_data[latest]
prior = sorted_months[-2] if len(sorted_months) > 1 else None
pmis = month_data[prior] if prior else None

mm = {}
for mk in sorted_months:
    mis = month_data[mk]
    rev=stot(mis,'P&L','Revenue'); cogs=stot(mis,'P&L','COGS'); opex=stot(mis,'P&L','OpEx')
    fin=stot(mis,'P&L','Finance'); tax=stot(mis,'P&L','Tax')
    gross=rev-cogs; ebitda=gross-opex; net=ebitda-fin-tax; texp=cogs+opex+fin
    bank=mis[mis['mis_category'].isin(['Bank Balances','Bank Deposits'])]['bs_amount'].sum()
    borr=abs(mis[mis['section']=='Borrowings']['bs_amount'].sum())
    eq=mis[mis['section']=='Equity']['bs_amount'].sum()
    fa=mis[mis['section']=='FA']['bs_amount'].sum()
    ca=mis[mis['section']=='CA']['bs_amount'].sum()
    cl=abs(mis[mis['section']=='CL']['bs_amount'].sum())
    mm[mk] = dict(revenue=rev,cogs=cogs,gross_profit=gross,opex=opex,ebitda=ebitda,
        finance=fin,tax=tax,net_pl=net,total_expenses=texp,bank=bank,borrowings=borr,
        equity=-eq,fa=fa,ca=ca,cl=cl,burn_rate=texp,
        runway=bank/texp if texp>0 else 0,de_ratio=borr/abs(eq) if eq!=0 else 0,
        current_ratio=ca/cl if cl>0 else 0)

lm=mm[latest]; pm=mm[prior] if prior else None
ytd={k:sum(mm[mk][k] for mk in sorted_months) for k in ['revenue','cogs','opex','finance','tax','total_expenses']}
ytd['gross_profit']=ytd['revenue']-ytd['cogs']; ytd['ebitda']=ytd['gross_profit']-ytd['opex']
ytd['net_pl']=ytd['ebitda']-ytd['finance']-ytd['tax']

# ─── Header ───
pr = f"{mlabel(sorted_months[0])} to {mlabel(sorted_months[-1])}"
now = datetime.now().strftime("%d %B %Y, %I:%M %p")
st.markdown(f"""
<div class='report-header'>
    <p class='company'>Full Circle Studio Private Limited</p>
    <p class='subtitle'>Monthly Management Information System</p>
    <div class='period-box'>
        <div><div class='period-label'>Reporting Period</div><div class='period-value'>{pr}</div></div>
        <div><div class='period-label'>Months Loaded</div><div class='period-value'>{len(sorted_months)} of 12</div></div>
        <div><div class='period-label'>Latest Month</div><div class='period-value'>{mlabel(latest)}</div></div>
    </div>
    <div class='preparer'>Prepared on {now}<br>STCA Global, Chartered Accountants</div>
</div>
""", unsafe_allow_html=True)

if IS_CLIENT:
    st.markdown("<div class='confidential'>CONFIDENTIAL — Prepared for management use only. Not for external distribution.</div>", unsafe_allow_html=True)

if IS_CLIENT:
    tab1,tab2,tab3 = st.tabs(["📊 Executive Summary", "📈 Income Statement", "🏦 Balance Sheet"])
else:
    tab1,tab2,tab3,tab4 = st.tabs(["📊 Executive Summary", "📈 Income Statement", "🏦 Balance Sheet", "🔍 Ledger Detail"])

# ═══════ EXECUTIVE SUMMARY ═══════
with tab1:
    if lm['revenue'] == 0:
        st.markdown(f"""<div style='background:#FEF3C7; border-left:4px solid {ACCENT}; padding:12px 20px; border-radius:0 8px 8px 0; margin-bottom:20px;'>
        <strong style='color:#92400E;'>Pre-Launch Phase</strong><span style='color:#92400E; margin-left:8px;'>No revenue recorded. All expenses are pre-operative.</span></div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Key Performance Indicators</div>", unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.markdown(kpi_card("Revenue", fmt_inr(lm['revenue']) if lm['revenue']>0 else "NIL", "Pre-launch" if lm['revenue']==0 else "Current month", MUTED), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Monthly Burn", fmt_inr(lm['total_expenses']), "Total expenses", RED, RED), unsafe_allow_html=True)
    with c3:
        pl_color = RED if lm['net_pl']<0 else GREEN
        st.markdown(kpi_card("Net P/L", fmt_inr(lm['net_pl']), "Loss" if lm['net_pl']<0 else "Profit", pl_color, pl_color), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Cash Position", fmt_inr(lm['bank']), f"{lm['runway']:.1f} months runway" if lm['runway']<100 else "", MID_BLUE, MID_BLUE), unsafe_allow_html=True)
    with c5: st.markdown(kpi_card("Borrowings", fmt_inr(lm['borrowings']), "Promoter funded", ACCENT, ACCENT), unsafe_allow_html=True)
    with c6: st.markdown(kpi_card("Net Worth", fmt_inr(lm['equity']), "Equity + Retained", TEXT_SECONDARY), unsafe_allow_html=True)

    # YTD
    st.markdown("<div class='section-title'>Year to Date Summary</div>", unsafe_allow_html=True)
    y1,y2,y3,y4 = st.columns(4)
    with y1: st.markdown(kpi_card("YTD Revenue", fmt_inr(ytd['revenue']) if ytd['revenue']>0 else "NIL", "", MUTED), unsafe_allow_html=True)
    with y2: st.markdown(kpi_card("YTD Expenses", fmt_inr(ytd['total_expenses']), "", RED), unsafe_allow_html=True)
    with y3: st.markdown(kpi_card("YTD Net P/L", fmt_inr(ytd['net_pl']), "Loss" if ytd['net_pl']<0 else "Profit", RED if ytd['net_pl']<0 else GREEN), unsafe_allow_html=True)
    with y4: st.markdown(kpi_card("Coverage", f"{len(sorted_months)}/12", "Months reported", MUTED), unsafe_allow_html=True)

    # Trend Charts
    if len(sorted_months) > 1:
        st.markdown("<div class='section-title'>Monthly Trends</div>", unsafe_allow_html=True)
        tdf = pd.DataFrame([{'Month':mlabel(mk), **mm[mk]} for mk in sorted_months])
        tc1, tc2 = st.columns(2)
        with tc1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=tdf['Month'],y=tdf['total_expenses'],name='Expenses',marker_color=RED,opacity=0.85))
            fig.add_trace(go.Bar(x=tdf['Month'],y=tdf['revenue'],name='Revenue',marker_color=GREEN,opacity=0.85))
            fig.update_layout(title=dict(text="Revenue vs Expenses",font=dict(size=14,family="DM Sans")),
                height=340,barmode='group',font=dict(family="DM Sans",size=11),
                margin=dict(t=45,b=20,l=20,r=20),legend=dict(orientation="h",y=-0.12),
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True,gridcolor="#F3F4F6")
            st.plotly_chart(fig, use_container_width=True)
        with tc2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=tdf['Month'],y=tdf['bank'],mode='lines+markers',name='Cash & Bank',
                line=dict(color=MID_BLUE,width=3),marker=dict(size=8,color=MID_BLUE)))
            fig2.add_trace(go.Scatter(x=tdf['Month'],y=tdf['borrowings'],mode='lines+markers',name='Borrowings',
                line=dict(color=ACCENT,width=2,dash='dot'),marker=dict(size=6,color=ACCENT)))
            fig2.update_layout(title=dict(text="Cash & Borrowings Trajectory",font=dict(size=14,family="DM Sans")),
                height=340,font=dict(family="DM Sans",size=11),margin=dict(t=45,b=20,l=20,r=20),
                legend=dict(orientation="h",y=-0.12),plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig2.update_xaxes(showgrid=False); fig2.update_yaxes(showgrid=True,gridcolor="#F3F4F6")
            st.plotly_chart(fig2, use_container_width=True)

    # Composition
    cc1, cc2 = st.columns(2)
    with cc1:
        ed = lmis[(lmis['statement']=='P&L')&(lmis['section']!='Revenue')&(lmis['pl_amount']>0)]
        ec = ed.groupby('mis_category')['pl_amount'].sum().sort_values(ascending=False).reset_index()
        ec.columns = ['Category','Amount']
        if len(ec)>0:
            fig3=px.pie(ec,values='Amount',names='Category',title="Expense Composition",
                color_discrete_sequence=[MID_BLUE,ACCENT,GREEN,"#8B5CF6","#EC4899","#06B6D4","#F97316"],hole=0.45)
            fig3.update_layout(height=340,margin=dict(t=45,b=20,l=20,r=20),font=dict(family="DM Sans",size=11),
                legend=dict(orientation="h",y=-0.1),plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig3.update_traces(textposition='inside',textinfo='percent+label',textfont_size=10)
            st.plotly_chart(fig3, use_container_width=True)
    with cc2:
        ad = lmis[(lmis['section'].isin(['FA','CA']))&(lmis['bs_amount']>0)]
        ac = ad.groupby('mis_category')['bs_amount'].sum().sort_values(ascending=False).reset_index()
        ac.columns = ['Asset','Amount']
        if len(ac)>0:
            fig4=px.bar(ac,x='Asset',y='Amount',title="Asset Composition",
                color_discrete_sequence=[GREEN])
            fig4.update_layout(height=340,margin=dict(t=45,b=20,l=20,r=20),font=dict(family="DM Sans",size=11),
                showlegend=False,xaxis_title="",yaxis_title="",plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig4.update_traces(text=[fmt_inr(v) for v in ac['Amount']],textposition='outside',textfont_size=10)
            fig4.update_xaxes(showgrid=False); fig4.update_yaxes(showgrid=True,gridcolor="#F3F4F6")
            st.plotly_chart(fig4, use_container_width=True)

    # Ratios
    st.markdown("<div class='section-title'>Financial Ratios</div>", unsafe_allow_html=True)
    rr1,rr2,rr3,rr4 = st.columns(4)
    with rr1: st.markdown(f"<div class='ratio-card'><div class='ratio-value'>{lm['de_ratio']:.1f}x</div><div class='ratio-label'>Debt-Equity Ratio</div></div>", unsafe_allow_html=True)
    with rr2: st.markdown(f"<div class='ratio-card'><div class='ratio-value'>{lm['current_ratio']:.1f}x</div><div class='ratio-label'>Current Ratio</div></div>", unsafe_allow_html=True)
    with rr3: st.markdown(f"<div class='ratio-card'><div class='ratio-value'>{lm['runway']:.1f}</div><div class='ratio-label'>Months Runway</div></div>", unsafe_allow_html=True)
    with rr4:
        gm = (lm['gross_profit']/lm['revenue']*100) if lm['revenue']>0 else 0
        st.markdown(f"<div class='ratio-card'><div class='ratio-value'>{gm:.1f}%</div><div class='ratio-label'>Gross Margin</div></div>", unsafe_allow_html=True)

# ═══════ INCOME STATEMENT ═══════
with tab2:
    st.markdown(f"<div class='section-title'>Statement of Profit & Loss</div>", unsafe_allow_html=True)
    all_categories = {}
    for mk in sorted_months:
        mis = month_data[mk]
        for sec in ['Revenue','COGS','OpEx','Finance','Tax']:
            cats = mis[(mis['statement']=='P&L')&(mis['section']==sec)&(mis['pl_amount']!=0)]['mis_category'].unique()
            if sec not in all_categories: all_categories[sec] = set()
            all_categories[sec].update(cats)
    plo = [("REVENUE","h","Revenue"),("_","i","Revenue"),("Total Revenue","t","Revenue"),("","s",None),
        ("COST OF REVENUE","h","COGS"),("_","i","COGS"),("Total Cost of Revenue","t","COGS"),("","s",None),
        ("GROSS PROFIT","g","gross"),("","s",None),
        ("OPERATING EXPENSES","h","OpEx"),("_","i","OpEx"),("Total Operating Expenses","t","OpEx"),("","s",None),
        ("EBITDA","g","ebitda"),("","s",None),
        ("FINANCE COSTS","h","Finance"),("_","i","Finance"),("","s",None),
        ("NET PROFIT / (LOSS)","g","net")]
    trows = []
    for lb, rt, sec in plo:
        if rt=="s": trows.append({"t":"s"}); continue
        if rt=="h": trows.append({"t":"h","l":lb}); continue
        if rt=="i":
            for cat in sorted(all_categories.get(sec,[])):
                row={"t":"i","l":f"&nbsp;&nbsp;{cat}"}; yv=0
                for mk in sorted_months:
                    v=month_data[mk][(month_data[mk]['statement']=='P&L')&(month_data[mk]['section']==sec)&(month_data[mk]['mis_category']==cat)]['pl_amount'].sum()
                    row[mk]=v; yv+=v
                row['ytd']=yv; trows.append(row); continue
        if rt=="t":
            row={"t":"t","l":lb}; yv=0
            mkey={'Revenue':'revenue','COGS':'cogs','OpEx':'opex','Finance':'finance','Tax':'tax'}.get(sec,'')
            for mk in sorted_months: v=mm[mk].get(mkey,0); row[mk]=v; yv+=v
            row['ytd']=yv; trows.append(row); continue
        if rt=="g":
            row={"t":"g","l":lb}; yv=0
            mkey={'gross':'gross_profit','ebitda':'ebitda','net':'net_pl'}.get(sec,sec)
            for mk in sorted_months: v=mm[mk].get(mkey,0); row[mk]=v; yv+=v
            row['ytd']=yv; trows.append(row)

    # Render professional table
    ths = f"<th style='text-align:left; padding:12px 16px; font-weight:600; font-size:12px; letter-spacing:0.3px;'>Particulars</th>"
    for mk in sorted_months: ths += f"<th style='text-align:right; padding:12px 12px; font-weight:600; font-size:11px;'>{mlabel(mk)}</th>"
    ths += f"<th style='text-align:right; padding:12px 14px; font-weight:700; font-size:11px; background:{LIGHT_BLUE};'>YTD</th>"

    rhtml = ""; nc = len(sorted_months)+2
    for row in trows:
        if row['t']=='s': rhtml += f"<tr><td colspan='{nc}' style='padding:3px;'></td></tr>"; continue
        if row['t']=='h': rhtml += f"<tr><td colspan='{nc}' style='padding:10px 16px 4px; font-weight:700; color:{ACCENT}; font-size:11px; text-transform:uppercase; letter-spacing:1px;'>{row['l']}</td></tr>"; continue
        bg = LIGHT_BG if row['t']=='t' else (LIGHT_BLUE if row['t']=='g' else 'transparent')
        fw = "700" if row['t'] in ('t','g') else "400"
        bdr = f"border-bottom:2px solid {DARK_BLUE};" if row['t'] in ('t','g') else f"border-bottom:1px solid {BORDER};"
        ff = "'JetBrains Mono',monospace" if row['t'] in ('t','g') else "'DM Sans',sans-serif"
        td = f"<td style='padding:8px 16px; font-weight:{fw}; {bdr}; font-size:13px;'>{row['l']}</td>"
        for mk in sorted_months:
            v=row.get(mk,0); clr=RED if v<0 else TEXT
            td += f"<td style='text-align:right; padding:8px 12px; font-weight:{fw}; color:{clr}; {bdr}; font-size:12px; font-family:{ff};'>{fmt_tbl(v)}</td>"
        yv=row.get('ytd',0); yc=RED if yv<0 else TEXT
        td += f"<td style='text-align:right; padding:8px 14px; font-weight:700; color:{yc}; {bdr}; background:{LIGHT_BG}; font-size:12px; font-family:\"JetBrains Mono\",monospace;'>{fmt_tbl(yv)}</td>"
        rhtml += f"<tr style='background:{bg};'>{td}</tr>"

    st.markdown(f"""<div style='overflow-x:auto; border:1px solid {BORDER}; border-radius:10px;'>
    <table style='width:100%; border-collapse:collapse; font-family:"DM Sans",sans-serif;'>
    <thead><tr style='background:{NAVY}; color:white;'>{ths}</tr></thead>
    <tbody>{rhtml}</tbody></table></div>""", unsafe_allow_html=True)

    if len(sorted_months)>1:
        st.markdown("<div class='section-title'>Expense Trend Analysis</div>", unsafe_allow_html=True)
        et=[]
        for mk in sorted_months:
            cats=month_data[mk][(month_data[mk]['statement']=='P&L')&(month_data[mk]['section'].isin(['COGS','OpEx']))&(month_data[mk]['pl_amount']>0)]
            for cn,cv in cats.groupby('mis_category')['pl_amount'].sum().items():
                et.append({'Month':mlabel(mk),'Category':cn,'Amount':cv})
        if et:
            edf=pd.DataFrame(et)
            fs=px.bar(edf,x='Month',y='Amount',color='Category',color_discrete_sequence=[MID_BLUE,ACCENT,GREEN,"#8B5CF6","#EC4899","#06B6D4"])
            fs.update_layout(height=340,barmode='stack',font=dict(family="DM Sans",size=11),
                margin=dict(t=20,b=20,l=20,r=20),legend=dict(orientation="h",y=-0.15),
                plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fs.update_xaxes(showgrid=False); fs.update_yaxes(showgrid=True,gridcolor="#F3F4F6")
            st.plotly_chart(fs, use_container_width=True)

# ═══════ BALANCE SHEET ═══════
with tab3:
    st.markdown(f"<div class='section-title'>Statement of Financial Position &nbsp;—&nbsp; as at {mlabel(latest)}</div>", unsafe_allow_html=True)
    if prior: st.caption(f"With comparative figures for {mlabel(prior)}")

    def build_bs(mc, mp, secs):
        rows=[]; is_l=secs[0][0] in ['Equity','Borrowings','CL']
        for sk,sl in secs:
            cd=mc[mc['section']==sk]; pd_=mp[mp['section']==sk] if mp is not None else pd.DataFrame()
            cc=cd.groupby('mis_category')['bs_amount'].sum()
            pc=pd_.groupby('mis_category')['bs_amount'].sum() if len(pd_)>0 else pd.Series(dtype=float)
            cats={c for c in set(cc.index)|set(pc.index) if cc.get(c,0)!=0 or pc.get(c,0)!=0}
            if not cats: continue
            rows.append({"t":"sec","l":sl}); sc=sp=0
            for cat in sorted(cats):
                cv=cc.get(cat,0); pv=pc.get(cat,0)
                dcv=-cv if is_l else cv; dpv=-pv if is_l else pv
                sc+=dcv; sp+=dpv
                rows.append({"t":"item","l":cat,"c":dcv,"p":dpv,"m":dcv-dpv})
            rows.append({"t":"sub","l":sl,"c":sc,"p":sp,"m":sc-sp})
        gc=sum(r['c'] for r in rows if r['t']=='sub')
        gp=sum(r['p'] for r in rows if r['t']=='sub')
        rows.append({"t":"grand","l":"TOTAL","c":gc,"p":gp,"m":gc-gp})
        return rows

    def render_bs(rows, sp, ll, pl):
        ch=f"<th style='text-align:right; padding:8px 12px; font-size:11px; font-weight:600;'>{ll}</th>"
        if sp: ch+=f"<th style='text-align:right; padding:8px 12px; font-size:11px;'>{pl}</th><th style='text-align:right; padding:8px 12px; font-size:11px;'>Movement</th>"
        span='4' if sp else '2'
        h=f"<div style='border:1px solid {BORDER}; border-radius:10px; overflow:hidden;'><table style='width:100%; border-collapse:collapse; font-size:13px;'><thead><tr style='background:{NAVY}; color:white;'><th style='text-align:left; padding:8px 12px; font-weight:600;'>Particulars</th>{ch}</tr></thead><tbody>"
        for r in rows:
            if r['t']=='sec':
                h+=f"<tr><td colspan='{span}' style='padding:10px 12px 4px; font-weight:700; color:{ACCENT}; font-size:11px; text-transform:uppercase; letter-spacing:1px;'>{r['l']}</td></tr>"
            else:
                bg=LIGHT_BG if r['t']=='sub' else (NAVY if r['t']=='grand' else 'transparent')
                fc='white' if r['t']=='grand' else TEXT; fw='700' if r['t'] in ('sub','grand') else '400'
                ff="'JetBrains Mono',monospace" if r['t'] in ('sub','grand') else "'DM Sans',sans-serif"
                vc=RED if r['c']<0 and r['t']!='grand' else fc
                rr=f"<td style='padding:6px 12px; font-weight:{fw}; color:{fc};'>{r['l']}</td>"
                rr+=f"<td style='text-align:right; padding:6px 12px; font-weight:{fw}; color:{vc}; font-family:{ff};'>{fmt_tbl(r['c'])}</td>"
                if sp:
                    pvc=RED if r['p']<0 and r['t']!='grand' else fc
                    mc=GREEN if r.get('m',0)>0 else (RED if r.get('m',0)<0 else MUTED)
                    rr+=f"<td style='text-align:right; padding:6px 12px; color:{pvc}; font-family:{ff};'>{fmt_tbl(r['p'])}</td>"
                    rr+=f"<td style='text-align:right; padding:6px 12px; color:{mc}; font-size:12px; font-family:{ff};'>{fmt_tbl(r['m'])}</td>"
                h+=f"<tr style='background:{bg}; border-bottom:1px solid {BORDER};'>{rr}</tr>"
        h+="</tbody></table></div>"; return h

    sp_=prior is not None; ll_=mlabel(latest); pl_=mlabel(prior) if prior else ""
    cl,cr = st.columns(2)
    with cl:
        st.markdown(f"**Sources of Funds**")
        lr=build_bs(lmis,pmis,[("Equity","Equity"),("Borrowings","Borrowings"),("CL","Current Liabilities")])
        st.markdown(render_bs(lr,sp_,ll_,pl_), unsafe_allow_html=True)
    with cr:
        st.markdown(f"**Application of Funds**")
        ar=build_bs(lmis,pmis,[("FA","Fixed Assets"),("CA","Current Assets")])
        st.markdown(render_bs(ar,sp_,ll_,pl_), unsafe_allow_html=True)
    lt=sum(r['c'] for r in lr if r['t']=='grand'); at_=sum(r['c'] for r in ar if r['t']=='grand')
    diff=abs(at_-lt)
    if diff<2:
        st.markdown(f"<div style='background:#D1FAE5; border:1px solid {GREEN}; border-radius:8px; padding:10px 16px; text-align:center; margin-top:16px; font-size:13px; color:#065F46;'><strong>✓ Balance Sheet Tallies</strong> &nbsp;—&nbsp; Assets ₹{at_:,.0f} = Liabilities ₹{lt:,.0f}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#FEE2E2; border:1px solid {RED}; border-radius:8px; padding:10px 16px; text-align:center; margin-top:16px; font-size:13px; color:#991B1B;'><strong>⚠ Difference:</strong> ₹{diff:,.0f} — Assets ₹{at_:,.0f} vs Liabilities ₹{lt:,.0f}</div>", unsafe_allow_html=True)

# ═══════ LEDGER DETAIL ═══════
if not IS_CLIENT:
    with tab4:
        st.markdown("<div class='section-title'>Ledger-Level Detail</div>", unsafe_allow_html=True)
        sl=st.selectbox("Month",[mlabel(mk) for mk in sorted_months],index=len(sorted_months)-1,key="dm")
        dmk=sl.replace("-","").lower(); dm=month_data[dmk]
        vo=st.radio("View",["P&L","BS","All"],horizontal=True)
        if vo=="P&L":
            d=dm[dm['statement']=='P&L'][['ledger','group','mis_category','section','debit','credit','pl_amount']].copy()
            d=d[d['pl_amount']!=0].sort_values('pl_amount',ascending=False)
            d.columns=['Ledger','Tally Group','MIS Category','Section','Debit','Credit','Net Amount']
        elif vo=="BS":
            d=dm[(dm['statement']=='BS')&(dm['ledger']!='Profit & Loss Account (Current Period)')][['ledger','group','mis_category','section','opening','closing','bs_amount','signed_closing']].copy()
            d=d[d['closing']!=0].sort_values('bs_amount',ascending=False)
            d.columns=['Ledger','Tally Group','MIS Category','Section','Opening','Closing','BS Amount','Signed']
        else:
            d=dm[dm['ledger']!='Profit & Loss Account (Current Period)'][['ledger','group','mis_category','statement','section','debit','credit','closing','signed_closing']].copy()
            d=d[(d['closing']!=0)|(d['debit']!=0)].sort_values('signed_closing',ascending=False)
            d.columns=['Ledger','Tally Group','MIS Category','Statement','Section','Debit','Credit','Closing','Signed']
        s=st.text_input("Search","",key="ds")
        if s: d=d[d['Ledger'].str.contains(s,case=False,na=False)]
        st.dataframe(d,use_container_width=True,hide_index=True)
        st.download_button("Download CSV",d.to_csv(index=False),f"ledger_{dmk}.csv","text/csv")

st.markdown(f"""<div class='stca-footer'>
    <strong>STCA Global</strong> &nbsp;·&nbsp; Suraj & Tarun, Chartered Accountants &nbsp;·&nbsp; FRN 016465S<br>
    This report has been prepared for the exclusive use of the management of Full Circle Studio Private Limited.<br>
    Generated on {now}
</div>""", unsafe_allow_html=True)
