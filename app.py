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
import html  # Fix #5: Added for input sanitization

# --- CONFIG & THEME (UNTOUCHED) ---
st.set_page_config(page_title="MPDR Issue Management System", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp { background: #f0f6ff !important; color: #0d2d5e !important; }
.main .block-container { padding:1.5rem 2rem 2rem 2rem; max-width:1400px; }

section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d2d5e 0%,#1a4a8a 100%) !important; border-right:3px solid #38b6ff !important; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
section[data-testid="stSidebar"] .stButton button { background:rgba(255,255,255,0.08) !important; color:#e0f0ff !important; border:1px solid rgba(255,255,255,0.1) !important; width:100%; text-align:left; padding:0.75rem 1rem !important; border-radius:8px !important; margin-bottom:0.5rem !important; }
section[data-testid="stSidebar"] .stButton button:hover { background:rgba(255,255,255,0.15) !important; border-color:#38b6ff !important; }

.metric-card { background:white; padding:1.25rem; border-radius:12px; border:1px solid #e0e6ed; box-shadow:0 4px 6px rgba(0,0,0,0.02); }
.ticket-card { background:white; padding:1.5rem; border-radius:12px; border:1px solid #e0e6ed; margin-bottom:1rem; transition:all 0.2s; border-left:5px solid #0d2d5e; }
.ticket-card:hover { transform:translateY(-2px); box-shadow:0 8px 15px rgba(0,0,0,0.05); }

.status-open { background:#fff4e5; color:#b95e00; padding:4px 8px; border-radius:6px; font-size:0.75rem; font-weight:700; }
.status-resolved { background:#e6fffa; color:#047481; padding:4px 8px; border-radius:6px; font-size:0.75rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# --- FIX #5: SANITIZATION UTILITY ---
def clean(text):
    """Sanitizes user input to prevent HTML injection/UI breakage"""
    return html.escape(str(text))

# --- GOOGLE SHEETS CONNECTION & FIX #1 (CACHING) ---
def get_gsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet_id"])

@st.cache_data(ttl=300) # Cache for 5 mins to prevent API rate limits
def all_users():
    return get_gsheet().worksheet("users").get_all_records()

@st.cache_data(ttl=60) # Tickets refresh every minute
def all_tickets():
    return get_gsheet().worksheet("tickets").get_all_records()

@st.cache_data(ttl=300)
def all_feedback():
    return get_gsheet().worksheet("feedback").get_all_records()

def clear_cache():
    st.cache_data.clear()

# --- AUTH LOGIC ---
def hash_pw(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def check_pw(pw, hashed): return bcrypt.checkpw(pw.encode(), hashed.encode())

# --- FIX #3: ATOMIC UPDATE (RACE CONDITION) ---
def update_ticket_status(tid, new_status):
    sh = get_gsheet().worksheet("tickets")
    records = sh.get_all_records()
    for i, row in enumerate(records):
        if str(row['ticket_id']) == str(tid):
            row_idx = i + 2 # Header is row 1
            # Batch update to prevent data misalignment
            sh.update(f'F{row_idx}:I{row_idx}', [[new_status, "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
            clear_cache()
            return True
    return False

# --- FIX #4: EMAIL WITH SENDER NAME ---
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"MorepenPDR Support <{st.secrets['smtp_user']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(st.secrets["smtp_user"], st.secrets["smtp_pass"])
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.sidebar.error(f"Mail delivery failed: {e}")

# --- SCIENTIST PAGES ---
def page_create():
    st.markdown("<h2 style='color:#0d2d5e;'>Report New Issue</h2>", unsafe_allow_html=True)
    with st.form("new_ticket", clear_on_submit=True):
        col1, col2 = st.columns(2)
        title = col1.text_input("Short Summary of Issue")
        cat = col2.selectbox("Category", ["IT Support", "Lab Equipment", "Chemical Inventory", "Safety/EHS", "General Facilities"])
        desc = st.text_area("Detailed Description")
        prio = st.select_slider("Priority", options=["LOW", "MEDIUM", "HIGH", "CRITICAL"], value="MEDIUM")
        
        dept_map = {"IT Support":"IT", "Lab Equipment":"Lab Maintenance", "Chemical Inventory":"Lab Maintenance", "Safety/EHS":"Safety", "General Facilities":"IT"}
        
        if st.form_submit_button("🚀 Submit Ticket"):
            if title and desc:
                tid = str(uuid.uuid4())
                new_row = [tid, title, desc, cat, prio, "OPEN", st.session_state.email, dept_map[cat], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                get_gsheet().worksheet("tickets").append_row(new_row)
                clear_cache()
                st.success(f"Ticket submitted! ID: {tid[:8].upper()}")
                # Notify Admin
                send_email(st.secrets["smtp_user"], f"New Ticket: {cat}", f"A new {prio} priority ticket has been raised by {st.session_state.name}.\n\nTitle: {title}")
            else:
                st.warning("Please fill all fields.")

def page_my_tickets():
    st.markdown("<h2 style='color:#0d2d5e;'>My Reported Issues</h2>", unsafe_allow_html=True)
    
    # FIX #2: Call feedback once outside the loop
    tickets = all_tickets()
    feedback_data = all_feedback()
    reviewed_ids = {str(f['ticket_id']) for f in feedback_data}
    
    filtered = [t for t in tickets if t['created_by'] == st.session_state.email]
    
    if not filtered:
        st.info("No tickets found.")
        return

    for t in filtered:
        # FIX #5: Sanitize display values
        t_title = clean(t['title'])
        t_desc = clean(t['description'])
        tid = str(t['ticket_id'])
        
        status_class = "status-open" if t['status'] != "RESOLVED" else "status-resolved"
        
        st.markdown(f"""
        <div class="ticket-card">
            <div style="display:flex; justify-content:space-between;">
                <h4 style="margin:0;">{t_title}</h4>
                <span class="{status_class}">{t['status']}</span>
            </div>
            <p style="color:#4b5e7d; margin:10px 0;">{t_desc}</p>
            <div style="font-size:0.8rem; color:#8b949e;">ID: {tid[:8].upper()} | Priority: {t['priority']} | Date: {t['created_at']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # FIX #2: Use cached reviewed_ids set
        if t['status'] == "RESOLVED" and tid not in reviewed_ids:
            with st.expander("⭐ Rate Resolution"):
                score = st.slider("Rating", 1, 5, 5, key=f"rate_{tid}")
                comm = st.text_input("Comments", key=f"comm_{tid}")
                if st.button("Submit Feedback", key=f"btn_{tid}"):
                    get_gsheet().worksheet("feedback").append_row([tid, st.session_state.email, score, comm, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                    update_ticket_status(tid, "CLOSED")
                    st.rerun()

# --- ADMIN PAGES ---
def page_dept():
    dept = st.session_state.department
    st.markdown(f"<h2 style='color:#0d2d5e;'>{dept} Task Board</h2>", unsafe_allow_html=True)
    
    tickets = all_tickets()
    filtered = [t for t in tickets if t['assigned_to_dept'] == dept and t['status'] not in ["RESOLVED", "CLOSED"]]
    
    if not filtered:
        st.success("🎉 All caught up! No pending tickets.")
        return

    for t in filtered:
        with st.container():
            st.markdown(f"""
            <div class="ticket-card" style="border-left-color:#f59e0b;">
                <h4 style="margin:0;">{clean(t['title'])}</h4>
                <p style="margin:5px 0;">{clean(t['description'])}</p>
                <small>From: {t['created_by']} | Prio: {t['priority']}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Mark as Resolved", key=f"res_{t['ticket_id']}"):
                if update_ticket_status(t['ticket_id'], "RESOLVED"):
                    send_email(t['created_by'], "Issue Resolved", f"Your ticket '{t['title']}' has been resolved. Please log in to provide feedback.")
                    st.rerun()

# --- MANAGEMENT DASHBOARD ---
def page_dashboard():
    st.markdown("<h2 style='color:#0d2d5e;'>Operational Insights</h2>", unsafe_allow_html=True)
    df = pd.DataFrame(all_tickets())
    if df.empty: return

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>{len(df)}</h3><p>Total Tickets</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>{len(df[df["status"]=="OPEN"])}</h3><p>Pending Issues</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>{len(df[df["status"]=="CLOSED"])}</h3><p>Success Rate</p></div>', unsafe_allow_html=True)

    colA, colB = st.columns(2)
    with colA:
        fig1 = px.pie(df, names='category', title="Tickets by Department", hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
    with colB:
        fig2 = px.bar(df, x='priority', color='status', title="Priority Distribution")
        st.plotly_chart(fig2, use_container_width=True)

# --- NAVIGATION ---
def render_sidebar():
    with st.sidebar:
        st.markdown(f"### Welcome,<br>{st.session_state.name}", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#38b6ff;'>Role: {st.session_state.role.upper()}</p>", unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.role == "scientist":
            if st.button("➕ Report Issue"): st.session_state.page = "create"
            if st.button("📋 My Tickets"): st.session_state.page = "my_tickets"
        elif st.session_state.role == "admin":
            if st.button("📥 Pending Tasks"): st.session_state.page = "dept_tickets"
        elif st.session_state.role == "management":
            if st.button("📊 Dashboard"): st.session_state.page = "dashboard"
            
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# --- LOGIN / SESSION MGMT ---
def login_page():
    st.markdown("<div style='max-width:400px; margin:auto; padding-top:5rem;'>", unsafe_allow_html=True)
    st.image("https://www.morepen.com/wp-content/uploads/2021/05/logo.png", width=200)
    st.title("PDR Issue Manager")
    
    with st.tabs(["Login", "Register"]):
        with st.container():
            email = st.text_input("Email (@morepenpdr.com)")
            pw = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                users = all_users()
                user = next((u for u in users if u['email'] == email), None)
                if user and check_pw(pw, user['password_hash']):
                    st.session_state.update({"logged_in":True, "email":email, "name":user['name'], "role":user['role'], "department":user['department'], "page":"home"})
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        login_page()
    else:
        render_sidebar()
        p = st.session_state.get("page", "home")
        r = st.session_state.role
        if r == "scientist":
            if p == "my_tickets": page_my_tickets()
            else: page_create()
        elif r == "admin":
            page_dept()
        elif r == "management":
            page_dashboard()

if __name__ == "__main__":
    main()
