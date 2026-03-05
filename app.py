import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="MPDR Issue Tracker", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
.stApp { background: linear-gradient(135deg,#0a0e1a 0%,#0d1117 50%,#0a0e1a 100%); color:#e6edf3; }
.main .block-container { padding:1.5rem 2rem 2rem 2rem; max-width:1400px; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d1117 0%,#161b22 100%); border-right: 1px solid #21262d; }
section[data-testid="stSidebar"] * { color:#e6edf3 !important; }
section[data-testid="stSidebar"] .stButton button { background:transparent !important; color:#8b949e !important; border:1px solid transparent !important; border-radius:8px !important; text-align:left !important; padding:0.6rem 1rem !important; font-size:0.88rem !important; font-weight:500 !important; transition:all 0.2s !important; width:100% !important; }
section[data-testid="stSidebar"] .stButton button:hover { background:#21262d !important; color:#58a6ff !important; border-color:#30363d !important; }
.stat-card { background:linear-gradient(135deg,#161b22,#1c2128); border:1px solid #21262d; border-radius:12px; padding:1.4rem 1.6rem; text-align:center; }
.stat-number { font-size:2.4rem; font-weight:700; line-height:1; }
.stat-label { font-size:0.82rem; color:#8b949e; margin-top:0.4rem; text-transform:uppercase; letter-spacing:0.05em; }
.info-card { background:#161b22; border:1px solid #21262d; border-radius:12px; padding:1.2rem 1.4rem; margin-bottom:0.8rem; }
.ticket-card { background:linear-gradient(135deg,#161b22,#1c2128); border:1px solid #21262d; border-left:4px solid #58a6ff; border-radius:10px; padding:1.2rem 1.4rem; margin-bottom:0.8rem; }
.ticket-card.critical { border-left-color:#ff4444; }
.ticket-card.high { border-left-color:#ff7b72; }
.ticket-card.medium { border-left-color:#f0a500; }
.ticket-card.low { border-left-color:#3fb950; }
.ticket-id { font-size:0.75rem; color:#8b949e; font-family:monospace !important; }
.ticket-title { font-size:1.05rem; font-weight:600; color:#e6edf3; margin:0.2rem 0; }
.ticket-desc { font-size:0.88rem; color:#8b949e; margin-top:0.3rem; line-height:1.5; }
.ticket-meta { font-size:0.8rem; color:#6e7681; margin-top:0.6rem; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; letter-spacing:0.03em; text-transform:uppercase; }
.b-open { background:#1f3a5f; color:#58a6ff; border:1px solid #1f6feb; }
.b-assigned { background:#3d2b00; color:#f0a500; border:1px solid #9e6a03; }
.b-inprog { background:#1a3a1a; color:#3fb950; border:1px solid #238636; }
.b-resolved { background:#1b3a2d; color:#56d364; border:1px solid #2ea043; }
.b-closed { background:#21262d; color:#8b949e; border:1px solid #30363d; }
.b-low { background:#1a3a1a; color:#3fb950; }
.b-medium { background:#3d2b00; color:#f0a500; }
.b-high { background:#4d1a00; color:#ff7b72; }
.b-critical { background:#5a0000; color:#ff4444; }
.page-header { background:linear-gradient(135deg,#161b22,#1c2128); border:1px solid #21262d; border-radius:12px; padding:1.4rem 1.8rem; margin-bottom:1.5rem; }
.page-title { font-size:1.6rem; font-weight:700; color:#e6edf3; margin:0; }
.page-sub { font-size:0.88rem; color:#8b949e; margin-top:0.3rem; }
.stTextInput input, .stTextArea textarea { background:#21262d !important; color:#e6edf3 !important; border:1px solid #30363d !important; border-radius:8px !important; }
.stButton > button { background:linear-gradient(135deg,#238636,#2ea043) !important; color:white !important; border:none !important; border-radius:8px !important; padding:0.55rem 1.4rem !important; font-weight:600 !important; }
.stTabs [data-baseweb="tab-list"] { background:#161b22; border-radius:8px; padding:4px; gap:4px; border:1px solid #21262d; }
.stTabs [data-baseweb="tab"] { background:transparent !important; color:#8b949e !important; border-radius:6px !important; padding:0.5rem 1.2rem !important; font-weight:500 !important; }
.stTabs [aria-selected="true"] { background:#21262d !important; color:#58a6ff !important; }
hr { border-color:#21262d; }
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#0d1117; }
::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]

@st.cache_resource(show_spinner=False)
def get_client():
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    return gspread.authorize(creds)

def sheet(tab):
    return get_client().open("MPDR Issue Tracker").worksheet(tab)

NOTIFY_EMAILS = ["admin@morepenpdr.com","mpdr.services@gmail.com"]

def send_email(to_list, subject, html_body):
    try:
        user = st.secrets["gmail"]["user"]
        pwd  = st.secrets["gmail"]["app_password"]
        targets = to_list if isinstance(to_list,list) else [to_list]
        for to_email in targets:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"MPDR Issue Tracker <{user}>"
            msg["To"]      = to_email
            msg.attach(MIMEText(html_body,"html"))
            with smtplib.SMTP_SSL("smtp.gmail.com",465) as srv:
                srv.login(user,pwd)
                srv.sendmail(user,to_email,msg.as_string())
        return True
    except Exception as e:
        st.toast(f"Email error: {e}",icon="⚠️")
        return False

def email_new_ticket(t):
    subj = f"[MPDR] New Ticket #{t['ticket_id'][:8].upper()} — {t['priority']} Priority"
    html = f"""<div style="font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:30px;border-radius:12px;max-width:600px;margin:0 auto;">
<div style="text-align:center;margin-bottom:24px;"><div style="font-size:2rem;">🔬</div>
<h2 style="color:#58a6ff;margin:8px 0 4px 0;">MPDR Issue Tracker</h2>
<p style="color:#8b949e;font-size:0.85rem;margin:0;">Morepen Laboratories — New Issue Reported</p></div>
<div style="background:#161b22;border:1px solid #21262d;border-left:4px solid #58a6ff;border-radius:10px;padding:20px;margin-bottom:16px;">
<table style="width:100%;border-collapse:collapse;">
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;width:140px;">TICKET ID</td><td style="color:#58a6ff;font-family:monospace;font-weight:600;">#{t['ticket_id'][:8].upper()}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">TITLE</td><td style="color:#e6edf3;font-weight:600;">{t['title']}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">DEPARTMENT</td><td style="color:#e6edf3;">{t['assigned_to']}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">PRIORITY</td><td><span style="background:#4d1a00;color:#ff7b72;padding:2px 8px;border-radius:10px;font-size:0.78rem;font-weight:600;">{t['priority']}</span></td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">CATEGORY</td><td style="color:#e6edf3;">{t['category']}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">REPORTED BY</td><td style="color:#e6edf3;">{t['created_by']}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">CREATED AT</td><td style="color:#e6edf3;">{t['created_at']}</td></tr>
</table></div>
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px;margin-bottom:16px;">
<p style="color:#8b949e;font-size:0.82rem;margin:0 0 6px 0;">DESCRIPTION</p>
<p style="color:#e6edf3;margin:0;line-height:1.6;">{t['description']}</p></div>
<p style="color:#8b949e;font-size:0.8rem;text-align:center;">Login to MPDR Issue Tracker to manage this ticket.</p></div>"""
    send_email(NOTIFY_EMAILS, subj, html)

def email_resolved(t):
    subj = f"[MPDR] ✅ Your ticket #{t['ticket_id'][:8].upper()} has been resolved"
    notes_block = f"""<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px;margin-bottom:16px;">
<p style="color:#8b949e;font-size:0.82rem;margin:0 0 6px 0;">RESOLUTION NOTES</p>
<p style="color:#e6edf3;margin:0;line-height:1.6;">{t.get('resolution_notes','')}</p></div>""" if t.get('resolution_notes') else ""
    html = f"""<div style="font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:30px;border-radius:12px;max-width:600px;margin:0 auto;">
<div style="text-align:center;margin-bottom:24px;"><div style="font-size:2.5rem;">✅</div>
<h2 style="color:#3fb950;margin:8px 0 4px 0;">Issue Resolved!</h2>
<p style="color:#8b949e;font-size:0.85rem;margin:0;">Your issue has been resolved by the {t['assigned_to']} team</p></div>
<div style="background:#1b3a2d;border:1px solid #238636;border-radius:10px;padding:20px;margin-bottom:16px;">
<table style="width:100%;border-collapse:collapse;">
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;width:140px;">TICKET ID</td><td style="color:#58a6ff;font-family:monospace;font-weight:600;">#{t['ticket_id'][:8].upper()}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">TITLE</td><td style="color:#e6edf3;font-weight:600;">{t['title']}</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">RESOLVED BY</td><td style="color:#e6edf3;">{t['assigned_to']} Team</td></tr>
<tr><td style="color:#8b949e;font-size:0.82rem;padding:6px 0;">RESOLVED AT</td><td style="color:#e6edf3;">{t['updated_at']}</td></tr>
</table></div>
{notes_block}
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:20px;text-align:center;margin-bottom:16px;">
<p style="color:#e6edf3;font-weight:600;margin:0 0 8px 0;">How was our support?</p>
<p style="color:#8b949e;font-size:0.85rem;margin:0;">Please login to <strong style="color:#58a6ff;">MPDR Issue Tracker</strong> and submit your star rating feedback to close the ticket.</p></div>
<p style="color:#8b949e;font-size:0.8rem;text-align:center;">MPDR Issue Tracker · Morepen Laboratories</p></div>"""
    send_email(t['created_by'], subj, html)

def all_users():    return sheet("users").get_all_records()
def get_user(e):    return next((u for u in all_users() if u["email"]==e), None)
def register_user(email,password,role,dept=""):
    h = bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
    sheet("users").append_row([email,h,role,dept,datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
def check_pw(pw,h): return bcrypt.checkpw(pw.encode(),h.encode())

def all_tickets():  return sheet("tickets").get_all_records()
def find_row(tid):
    ws=sheet("tickets"); recs=ws.get_all_records()
    for i,r in enumerate(recs,start=2):
        if r["ticket_id"]==tid: return ws,i,r
    return None,None,None

def create_ticket(title,desc,cat,prio,dept,creator):
    tid=str(uuid.uuid4()); now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet("tickets").append_row([tid,title,desc,cat,prio,"OPEN",creator,dept,now,now,""])
    t=dict(ticket_id=tid,title=title,description=desc,category=cat,priority=prio,
           status="OPEN",created_by=creator,assigned_to=dept,created_at=now,updated_at=now,resolution_notes="")
    email_new_ticket(t); return tid

def update_ticket(tid,status,notes=""):
    ws,row,t=find_row(tid)
    if not row: return
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.update_cell(row,6,status); ws.update_cell(row,10,now)
    if notes: ws.update_cell(row,11,notes)
    if status=="RESOLVED":
        t["resolution_notes"]=notes; t["updated_at"]=now; email_resolved(t)

def all_feedback():   return sheet("feedback").get_all_records()
def has_fb(tid):      return any(f["ticket_id"]==tid for f in all_feedback())
def submit_fb(tid,by,rating,comments):
    sheet("feedback").append_row([tid,by,rating,comments,datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    update_ticket(tid,"CLOSED")

SC={"OPEN":"b-open","ASSIGNED":"b-assigned","IN_PROGRESS":"b-inprog","RESOLVED":"b-resolved","CLOSED":"b-closed"}
PC={"Low":"b-low","Medium":"b-medium","High":"b-high","Critical":"b-critical"}
PB={"Low":"low","Medium":"medium","High":"high","Critical":"critical"}
def sb(s): return f'<span class="badge {SC.get(s,"b-open")}">{s}</span>'
def pb(p): return f'<span class="badge {PC.get(p,"b-low")}">{p}</span>'
def st_stars(n): return "⭐"*int(n)+"☆"*(5-int(n))

for k,v in [("logged_in",False),("email",""),("role",""),("dept",""),("page","login")]:
    if k not in st.session_state: st.session_state[k]=v

def login_page():
    c1,c2,c3=st.columns([1,1.1,1])
    with c2:
        st.markdown("""<div style="text-align:center;padding:2rem 0 1.5rem 0;">
<div style="font-size:3rem;">🔬</div>
<h1 style="color:#58a6ff;font-size:2rem;font-weight:700;margin:0.5rem 0 0.2rem 0;">MPDR Issue Tracker</h1>
<p style="color:#8b949e;font-size:0.9rem;margin:0;">Morepen Laboratories · Pharmaceutical Research Division</p></div>""",unsafe_allow_html=True)

        t1,t2=st.tabs(["🔐  Sign In","📝  Register"])
        with t1:
            st.markdown("<br>",unsafe_allow_html=True)
            email=st.text_input("Company Email",placeholder="yourname@morepenpdr.com",key="li_e")
            pwd  =st.text_input("Password",type="password",key="li_p")
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("Sign In →",use_container_width=True,key="btn_li"):
                if not email.endswith("@morepenpdr.com"):
                    st.error("⛔ Only @morepenpdr.com emails are allowed.")
                else:
                    u=get_user(email)
                    if u and check_pw(pwd,str(u["password"])):
                        st.session_state.logged_in=True; st.session_state.email=email
                        st.session_state.role=u["role"]; st.session_state.dept=u["department"]
                        st.session_state.page="home"; st.rerun()
                    else: st.error("Invalid email or password.")

        with t2:
            st.markdown("<br>",unsafe_allow_html=True)
            re=st.text_input("Company Email",placeholder="yourname@morepenpdr.com",key="re_e")
            rp=st.text_input("Password (min 6 chars)",type="password",key="re_p")
            rp2=st.text_input("Confirm Password",type="password",key="re_p2")
            rr=st.selectbox("Role",["scientist","admin","management"],key="re_r")
            rd=""
            if rr=="admin": rd=st.selectbox("Department",["IT","Lab Maintenance","Safety"],key="re_d")
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("Create Account →",use_container_width=True,key="btn_re"):
                if not re.endswith("@morepenpdr.com"): st.error("⛔ Only @morepenpdr.com emails allowed.")
                elif get_user(re): st.error("Email already registered.")
                elif len(rp)<6: st.error("Password must be at least 6 characters.")
                elif rp!=rp2: st.error("Passwords do not match.")
                else: register_user(re,rp,rr,rd); st.success("✅ Account created! Please sign in.")

        st.markdown('<p style="text-align:center;color:#6e7681;font-size:0.78rem;margin-top:2rem;">🔒 Secure · Only @morepenpdr.com accounts permitted</p>',unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        RC={"scientist":"#58a6ff","admin":"#f0a500","management":"#3fb950"}
        RI={"scientist":"🧪","admin":"🛠️","management":"📊"}
        color=RC.get(st.session_state.role,"#58a6ff"); icon=RI.get(st.session_state.role,"👤")
        st.markdown(f"""<div style="padding:1.5rem 1rem 1rem 1rem;border-bottom:1px solid #21262d;">
<div style="font-size:1.3rem;font-weight:700;color:#58a6ff;">🔬 MPDR Tracker</div>
<div style="margin-top:1rem;display:flex;align-items:center;gap:10px;">
<div style="width:38px;height:38px;background:{color}22;border:2px solid {color};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">{icon}</div>
<div><div style="font-size:0.82rem;color:#e6edf3;font-weight:600;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{st.session_state.email.split('@')[0]}</div>
<div style="font-size:0.72rem;color:{color};text-transform:uppercase;font-weight:600;">{st.session_state.role}{' · '+st.session_state.dept if st.session_state.dept else ''}</div>
</div></div></div>
<div style="padding:1rem 0.5rem 0.5rem 0.5rem;"><p style="color:#6e7681;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;padding:0 0.5rem;margin-bottom:0.5rem;">Navigation</p></div>""",unsafe_allow_html=True)

        role=st.session_state.role
        if role=="scientist":
            if st.button("➕   New Ticket",use_container_width=True): st.session_state.page="create"
            if st.button("📋   My Tickets",use_container_width=True): st.session_state.page="my_tickets"
        elif role=="admin":
            if st.button("🛠️   Open Tickets",use_container_width=True): st.session_state.page="dept_tickets"
            if st.button("✅   Resolved",use_container_width=True): st.session_state.page="resolved"
        elif role=="management":
            if st.button("📊   Dashboard",use_container_width=True): st.session_state.page="dashboard"
            if st.button("📋   All Tickets",use_container_width=True): st.session_state.page="all_tickets"

        st.markdown("<hr style='border-color:#21262d;margin:1rem 0;'>",unsafe_allow_html=True)
        if st.button("🚪   Logout",use_container_width=True):
            for k in ["logged_in","email","role","dept","page"]: del st.session_state[k]
            st.rerun()
        st.markdown('<div style="position:fixed;bottom:1rem;left:0;width:260px;text-align:center;"><p style="color:#6e7681;font-size:0.72rem;">MPDR Issue Tracker v1.0<br>Morepen Laboratories</p></div>',unsafe_allow_html=True)

def page_create():
    st.markdown('<div class="page-header"><div class="page-title">➕ Report New Issue</div><div class="page-sub">Submit a ticket to the appropriate department for resolution</div></div>',unsafe_allow_html=True)
    c1,c2=st.columns([2,1])
    with c1:
        with st.form("new_t",clear_on_submit=True):
            title=st.text_input("Issue Title *",placeholder="e.g. HPLC system not responding in Lab 3")
            desc =st.text_area("Detailed Description *",placeholder="Describe the issue clearly...",height=140)
            a,b,c=st.columns(3)
            with a: cat =st.selectbox("Category *",["Equipment Failure","Software Issue","Safety Concern","Chemical Handling","Facility Problem","Network / IT","Documentation","Other"])
            with b: prio=st.selectbox("Priority *",["Low","Medium","High","Critical"])
            with c: dept=st.selectbox("Assign To *",["IT","Lab Maintenance","Safety"])
            st.markdown("<br>",unsafe_allow_html=True)
            sub=st.form_submit_button("🚀  Submit Ticket",use_container_width=True)
        if sub:
            if not title.strip() or not desc.strip(): st.error("⛔ Title and description are required.")
            else:
                with st.spinner("Submitting and notifying..."):
                    tid=create_ticket(title.strip(),desc.strip(),cat,prio,dept,st.session_state.email)
                st.success(f"✅ **Ticket submitted!** ID: `#{tid[:8].upper()}` · Notification sent to admin@morepenpdr.com")
    with c2:
        st.markdown("""<div class="info-card"><p style="color:#58a6ff;font-weight:600;margin:0 0 12px 0;">📌 Priority Guide</p>
<div style="margin-bottom:8px;"><span class="badge b-critical">Critical</span><span style="color:#8b949e;font-size:0.82rem;margin-left:8px;">Safety risk / production stopped</span></div>
<div style="margin-bottom:8px;"><span class="badge b-high">High</span><span style="color:#8b949e;font-size:0.82rem;margin-left:8px;">Major impact on work</span></div>
<div style="margin-bottom:8px;"><span class="badge b-medium">Medium</span><span style="color:#8b949e;font-size:0.82rem;margin-left:8px;">Moderate disruption</span></div>
<div><span class="badge b-low">Low</span><span style="color:#8b949e;font-size:0.82rem;margin-left:8px;">Minor / non-urgent</span></div></div>
<div class="info-card" style="margin-top:1rem;"><p style="color:#58a6ff;font-weight:600;margin:0 0 12px 0;">🏢 Departments</p>
<div style="color:#8b949e;font-size:0.85rem;line-height:2;">🖥️ <b style="color:#e6edf3;">IT</b> — Software, network<br>🧪 <b style="color:#e6edf3;">Lab Maintenance</b> — Equipment<br>⚠️ <b style="color:#e6edf3;">Safety</b> — Hazards, compliance</div></div>""",unsafe_allow_html=True)

def page_my_tickets():
    st.markdown('<div class="page-header"><div class="page-title">📋 My Tickets</div><div class="page-sub">Track all issues you have reported</div></div>',unsafe_allow_html=True)
    tickets=[t for t in all_tickets() if t["created_by"]==st.session_state.email]
    if not tickets: st.info("No tickets yet. Click New Ticket to report an issue."); return

    on=sum(1 for t in tickets if t["status"]=="OPEN")
    rn=sum(1 for t in tickets if t["status"] in ["RESOLVED","CLOSED"])
    pf=sum(1 for t in tickets if t["status"]=="RESOLVED" and not has_fb(t["ticket_id"]))
    a,b,c,d=st.columns(4)
    with a: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#58a6ff;">{len(tickets)}</div><div class="stat-label">Total</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff7b72;">{on}</div><div class="stat-label">Open</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#3fb950;">{rn}</div><div class="stat-label">Resolved</div></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#f0a500;">{pf}</div><div class="stat-label">Pending Feedback</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: sf=st.selectbox("Status",["All","OPEN","ASSIGNED","IN_PROGRESS","RESOLVED","CLOSED"])
    with c2: pf2=st.selectbox("Priority",["All","Critical","High","Medium","Low"])
    filtered=list(reversed(tickets))
    if sf!="All": filtered=[t for t in filtered if t["status"]==sf]
    if pf2!="All": filtered=[t for t in filtered if t["priority"]==pf2]
    st.markdown(f"<p style='color:#8b949e;font-size:0.85rem;'>{len(filtered)} ticket(s)</p>",unsafe_allow_html=True)

    for t in filtered:
        bc=PB.get(t["priority"],"low")
        rh=f"""<div style="background:#1b3a2d;border:1px solid #238636;border-radius:6px;padding:8px 12px;margin-top:8px;"><span style="color:#3fb950;font-size:0.8rem;font-weight:600;">✅ RESOLUTION: </span><span style="color:#e6edf3;font-size:0.85rem;">{t['resolution_notes']}</span></div>""" if t.get("resolution_notes") else ""
        st.markdown(f"""<div class="ticket-card {bc}"><div class="ticket-id">#{t['ticket_id'][:8].upper()}</div>
<div class="ticket-title">{t['title']}</div>
<div class="ticket-desc">{t['description'][:200]}{'...' if len(t['description'])>200 else ''}</div>
{rh}<div class="ticket-meta">{sb(t['status'])} &nbsp; {pb(t['priority'])} &nbsp; 🏢 {t['assigned_to']} &nbsp;&nbsp; 📅 {t['created_at']}</div></div>""",unsafe_allow_html=True)

        if t["status"]=="RESOLVED" and not has_fb(t["ticket_id"]):
            with st.expander(f"⭐ Submit Feedback — #{t['ticket_id'][:8].upper()}"):
                st.markdown('<p style="color:#f0a500;font-weight:600;">Your ticket is resolved! Please rate the support.</p>',unsafe_allow_html=True)
                rating=st.slider("Rating",1,5,4,key=f"r_{t['ticket_id']}",help="1=Poor · 5=Excellent")
                st.markdown(f"<div style='font-size:1.5rem;'>{st_stars(rating)}</div>",unsafe_allow_html=True)
                comments=st.text_area("Comments (optional)",key=f"c_{t['ticket_id']}")
                if st.button("Submit Feedback ✓",key=f"fb_{t['ticket_id']}"):
                    submit_fb(t["ticket_id"],st.session_state.email,rating,comments)
                    st.success("✅ Thank you! Ticket is now closed."); st.rerun()
        elif t["status"]=="CLOSED":
            fb=next((f for f in all_feedback() if f["ticket_id"]==t["ticket_id"]),None)
            if fb:
                st.markdown(f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:6px;padding:8px 12px;margin-top:-8px;margin-bottom:8px;"><span style="color:#8b949e;font-size:0.8rem;">Your feedback: </span><span style="font-size:1rem;">{st_stars(fb['rating'])}</span>{f'<span style="color:#8b949e;font-size:0.82rem;"> · {fb["comments"]}</span>' if fb.get("comments") else ""}</div>""",unsafe_allow_html=True)

def page_dept():
    dept=st.session_state.dept
    st.markdown(f'<div class="page-header"><div class="page-title">🛠️ {dept} — Open Tickets</div><div class="page-sub">Manage and resolve tickets assigned to your department</div></div>',unsafe_allow_html=True)
    tickets=[t for t in all_tickets() if t["assigned_to"]==dept and t["status"] not in ["RESOLVED","CLOSED"]]
    if not tickets: st.success("🎉 No open tickets right now!"); return

    cn=sum(1 for t in tickets if t["priority"]=="Critical"); hn=sum(1 for t in tickets if t["priority"]=="High")
    a,b,c=st.columns(3)
    with a: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff7b72;">{len(tickets)}</div><div class="stat-label">Open</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff4444;">{cn}</div><div class="stat-label">Critical</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff7b72;">{hn}</div><div class="stat-label">High</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    po={"Critical":0,"High":1,"Medium":2,"Low":3}
    tickets=sorted(tickets,key=lambda x:po.get(x["priority"],4))
    pf=st.selectbox("Filter by Priority",["All","Critical","High","Medium","Low"])
    if pf!="All": tickets=[t for t in tickets if t["priority"]==pf]

    for t in tickets:
        with st.expander(f"#{t['ticket_id'][:8].upper()} · {t['title']}  |  {t['priority']}  |  {t['status']}"):
            c1,c2=st.columns(2)
            with c1:
                st.markdown(f"""<div class="info-card"><p style="color:#8b949e;font-size:0.78rem;margin:0 0 10px 0;">TICKET DETAILS</p>
<p style="margin:4px 0;"><b>Reported by:</b> {t['created_by']}</p>
<p style="margin:4px 0;"><b>Category:</b> {t['category']}</p>
<p style="margin:4px 0;"><b>Priority:</b> {pb(t['priority'])}</p>
<p style="margin:4px 0;"><b>Status:</b> {sb(t['status'])}</p>
<p style="margin:4px 0;"><b>Created:</b> {t['created_at']}</p></div>""",unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="info-card"><p style="color:#8b949e;font-size:0.78rem;margin:0 0 10px 0;">DESCRIPTION</p>
<p style="color:#e6edf3;line-height:1.6;font-size:0.9rem;">{t['description']}</p></div>""",unsafe_allow_html=True)

            st.markdown("**Update Ticket**")
            u1,u2=st.columns(2)
            with u1:
                opts=["OPEN","ASSIGNED","IN_PROGRESS","RESOLVED"]
                idx=opts.index(t["status"]) if t["status"] in opts else 0
                ns=st.selectbox("New Status",opts,index=idx,key=f"st_{t['ticket_id']}")
            with u2:
                notes=st.text_input("Resolution Notes",value=t.get("resolution_notes",""),placeholder="How was the issue fixed?",key=f"nt_{t['ticket_id']}")

            if ns=="RESOLVED": st.warning("⚠️ This will send a feedback email to the reporter.")
            if st.button(f"✅ Update #{t['ticket_id'][:8].upper()}",key=f"upd_{t['ticket_id']}"):
                if ns=="RESOLVED" and not notes.strip(): st.error("Add resolution notes before marking resolved.")
                else:
                    with st.spinner("Updating..."):
                        update_ticket(t["ticket_id"],ns,notes)
                    st.success("✅ Resolved! Feedback email sent." if ns=="RESOLVED" else f"✅ Updated to {ns}.")
                    st.rerun()

def page_resolved():
    dept=st.session_state.dept
    st.markdown(f'<div class="page-header"><div class="page-title">✅ Resolved — {dept}</div><div class="page-sub">Tickets your department has resolved</div></div>',unsafe_allow_html=True)
    tickets=[t for t in all_tickets() if t["assigned_to"]==dept and t["status"] in ["RESOLVED","CLOSED"]]
    if not tickets: st.info("No resolved tickets yet."); return
    fbs={f["ticket_id"]:f for f in all_feedback()}
    for t in reversed(tickets):
        fb=fbs.get(t["ticket_id"])
        st.markdown(f"""<div class="ticket-card low"><div class="ticket-id">#{t['ticket_id'][:8].upper()}</div>
<div class="ticket-title">{t['title']}</div>
<div class="ticket-meta">{sb(t['status'])} &nbsp; {pb(t['priority'])} &nbsp; 👤 {t['created_by']} &nbsp;&nbsp; 📅 {t['updated_at']}</div>
{f'<div style="margin-top:8px;color:#3fb950;font-size:0.85rem;">✅ {t["resolution_notes"]}</div>' if t.get("resolution_notes") else ""}
{f'<div style="margin-top:6px;color:#f0a500;font-size:0.85rem;">⭐ {st_stars(fb["rating"])} · {fb.get("comments","")}</div>' if fb else '<div style="margin-top:6px;color:#8b949e;font-size:0.82rem;">⏳ Awaiting feedback</div>'}
</div>""",unsafe_allow_html=True)

def page_dashboard():
    st.markdown('<div class="page-header"><div class="page-title">📊 Executive Dashboard</div><div class="page-sub">Real-time overview of all issues · Morepen Laboratories</div></div>',unsafe_allow_html=True)
    tickets=all_tickets()
    if not tickets: st.info("No data yet."); return
    df=pd.DataFrame(tickets)
    tot=len(df); on=len(df[df["status"]=="OPEN"]); ip=len(df[df["status"]=="IN_PROGRESS"])
    rn=len(df[df["status"].isin(["RESOLVED","CLOSED"])]); cr=len(df[df["priority"]=="Critical"])
    a,b,c,d,e=st.columns(5)
    with a: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#58a6ff;">{tot}</div><div class="stat-label">Total</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff7b72;">{on}</div><div class="stat-label">Open</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#f0a500;">{ip}</div><div class="stat-label">In Progress</div></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#3fb950;">{rn}</div><div class="stat-label">Resolved</div></div>',unsafe_allow_html=True)
    with e: st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ff4444;">{cr}</div><div class="stat-label">Critical</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    BG="#161b22"; FC="#e6edf3"; GC="#21262d"
    def sty(fig):
        fig.update_layout(paper_bgcolor=BG,plot_bgcolor=BG,font_color=FC,title_font_color="#58a6ff",title_font_size=14,margin=dict(t=40,b=20,l=20,r=20),legend=dict(bgcolor=BG,bordercolor=GC))
        fig.update_xaxes(gridcolor=GC,zerolinecolor=GC); fig.update_yaxes(gridcolor=GC,zerolinecolor=GC); return fig
    c1,c2=st.columns(2)
    with c1:
        sc=df["status"].value_counts().reset_index(); sc.columns=["Status","Count"]
        cm={"OPEN":"#58a6ff","ASSIGNED":"#f0a500","IN_PROGRESS":"#3fb950","RESOLVED":"#56d364","CLOSED":"#8b949e"}
        fig=px.pie(sc,values="Count",names="Status",title="Tickets by Status",color="Status",color_discrete_map=cm,hole=0.45)
        fig.update_traces(textfont_color=FC); st.plotly_chart(sty(fig),use_container_width=True)
    with c2:
        dc=df["assigned_to"].value_counts().reset_index(); dc.columns=["Department","Count"]
        fig2=px.bar(dc,x="Department",y="Count",title="Tickets by Department",color="Count",color_continuous_scale=["#1f6feb","#58a6ff","#79c0ff"])
        st.plotly_chart(sty(fig2),use_container_width=True)
    c1,c2=st.columns(2)
    with c1:
        cc=df["category"].value_counts().reset_index(); cc.columns=["Category","Count"]
        fig3=px.bar(cc,x="Count",y="Category",orientation="h",title="Top Issue Categories",color="Count",color_continuous_scale=["#238636","#3fb950","#56d364"])
        st.plotly_chart(sty(fig3),use_container_width=True)
    with c2:
        pc=df["priority"].value_counts().reset_index(); pc.columns=["Priority","Count"]
        pcm={"Low":"#3fb950","Medium":"#f0a500","High":"#ff7b72","Critical":"#ff4444"}
        fig4=px.bar(pc,x="Priority",y="Count",title="Tickets by Priority",color="Priority",color_discrete_map=pcm)
        st.plotly_chart(sty(fig4),use_container_width=True)
    fbs=all_feedback()
    if fbs:
        fb_df=pd.DataFrame(fbs); avg=fb_df["rating"].astype(float).mean()
        st.markdown(f"""<div class="info-card" style="text-align:center;margin-top:1rem;">
<p style="color:#8b949e;font-size:0.82rem;margin:0 0 6px 0;">AVERAGE SATISFACTION SCORE</p>
<div style="font-size:2.5rem;font-weight:700;color:#f0a500;">{avg:.1f} / 5.0</div>
<div style="font-size:1.8rem;">{st_stars(round(avg))}</div>
<div style="color:#8b949e;font-size:0.85rem;margin-top:0.3rem;">Based on {len(fbs)} feedback response(s)</div></div>""",unsafe_allow_html=True)

def page_all_tickets():
    st.markdown('<div class="page-header"><div class="page-title">📋 All Tickets</div><div class="page-sub">Complete view of every ticket in the system</div></div>',unsafe_allow_html=True)
    tickets=all_tickets()
    if not tickets: st.info("No tickets yet."); return
    c1,c2,c3,c4=st.columns(4)
    with c1: sf=st.selectbox("Status",["All","OPEN","ASSIGNED","IN_PROGRESS","RESOLVED","CLOSED"])
    with c2: pf=st.selectbox("Priority",["All","Critical","High","Medium","Low"])
    with c3: df2=st.selectbox("Department",["All","IT","Lab Maintenance","Safety"])
    with c4: srch=st.text_input("🔍 Search",placeholder="Title or reporter...")
    filtered=tickets
    if sf!="All": filtered=[t for t in filtered if t["status"]==sf]
    if pf!="All": filtered=[t for t in filtered if t["priority"]==pf]
    if df2!="All": filtered=[t for t in filtered if t["assigned_to"]==df2]
    if srch:
        s=srch.lower(); filtered=[t for t in filtered if s in t["title"].lower() or s in t["created_by"].lower()]
    st.markdown(f"<p style='color:#8b949e;font-size:0.85rem;'>{len(filtered)} ticket(s)</p>",unsafe_allow_html=True)
    if filtered:
        disp=pd.DataFrame(filtered)[["ticket_id","title","category","priority","status","assigned_to","created_by","created_at"]].copy()
        disp["ticket_id"]=disp["ticket_id"].str[:8].str.upper()
        disp.columns=["ID","Title","Category","Priority","Status","Department","Reporter","Created"]
        st.dataframe(disp,use_container_width=True,hide_index=True)

def main():
    if not st.session_state.logged_in:
        login_page(); return
    render_sidebar()
    role=st.session_state.role; page=st.session_state.page
    if role=="scientist":
        if page in ("home","create","login"): page_create()
        elif page=="my_tickets":             page_my_tickets()
        else:                                page_create()
    elif role=="admin":
        if page in ("home","dept_tickets","login"): page_dept()
        elif page=="resolved":                      page_resolved()
        else:                                       page_dept()
    elif role=="management":
        if page in ("home","dashboard","login"): page_dashboard()
        elif page=="all_tickets":                page_all_tickets()
        else:                                    page_dashboard()

if __name__=="__main__":
    main()
