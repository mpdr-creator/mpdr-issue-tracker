import streamlit as st
import psycopg2
import psycopg2.extras
import bcrypt
import jwt
import smtplib
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import os

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MorepenPDR | Issue Management",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── DARK THEME CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background-color: #0f1117; color: #e2e8f0; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d2e 0%, #161827 100%);
        border-right: 1px solid #2d3748;
    }
    section[data-testid="stSidebar"] * { color: #cbd5e0 !important; }

    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d1b69 100%);
        padding: 2rem; border-radius: 12px; margin-bottom: 2rem;
        border: 1px solid #2d4a7a;
    }
    .main-header h1 { color: #63b3ed; margin: 0; font-size: 1.8rem; font-weight: 700; }
    .main-header p  { color: #90cdf4; margin: 0.5rem 0 0; font-size: 0.95rem; }

    .metric-card {
        background: #1a202c; border: 1px solid #2d3748;
        border-radius: 10px; padding: 1.5rem; text-align: center;
        transition: transform 0.2s; cursor: default;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #4a90d9; }
    .metric-card .value { font-size: 2.2rem; font-weight: 700; color: #63b3ed; }
    .metric-card .label { font-size: 0.85rem; color: #718096; margin-top: 0.3rem; }

    .ticket-card {
        background: #1a202c; border: 1px solid #2d3748;
        border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;
        border-left: 4px solid #4a90d9;
    }
    .ticket-card.priority-critical { border-left-color: #fc8181; }
    .ticket-card.priority-high     { border-left-color: #f6ad55; }
    .ticket-card.priority-medium   { border-left-color: #68d391; }
    .ticket-card.priority-low      { border-left-color: #63b3ed; }

    .status-badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }
    .status-OPEN        { background: #2d3748; color: #90cdf4; }
    .status-ASSIGNED    { background: #2c5282; color: #bee3f8; }
    .status-IN_PROGRESS { background: #744210; color: #fefcbf; }
    .status-RESOLVED    { background: #1c4532; color: #9ae6b4; }
    .status-CLOSED      { background: #171923; color: #718096; }

    .priority-badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;
    }
    .priority-CRITICAL { background: #742a2a; color: #fc8181; }
    .priority-HIGH     { background: #744210; color: #f6ad55; }
    .priority-MEDIUM   { background: #1c4532; color: #68d391; }
    .priority-LOW      { background: #1a365d; color: #63b3ed; }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #2b6cb0, #1a365d);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 1.5rem; font-weight: 500;
        transition: all 0.2s;
    }
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #3182ce, #2b6cb0);
        transform: translateY(-1px);
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] select {
        background: #2d3748 !important; color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important; border-radius: 8px !important;
    }

    .stDataFrame { background: #1a202c; border-radius: 10px; }

    .login-container {
        max-width: 420px; margin: 5rem auto;
        background: #1a202c; border: 1px solid #2d3748;
        border-radius: 16px; padding: 2.5rem;
    }

    .section-title {
        color: #63b3ed; font-size: 1.1rem; font-weight: 600;
        margin-bottom: 1rem; padding-bottom: 0.5rem;
        border-bottom: 1px solid #2d3748;
    }

    .info-box {
        background: #1a2744; border: 1px solid #2c5282;
        border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
        color: #90cdf4; font-size: 0.9rem;
    }
    .success-box {
        background: #1c3a2a; border: 1px solid #276749;
        border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
        color: #9ae6b4; font-size: 0.9rem;
    }
    .warning-box {
        background: #3d2a0e; border: 1px solid #975a16;
        border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
        color: #fbd38d; font-size: 0.9rem;
    }

    .stTabs [data-baseweb="tab"] { color: #718096; }
    .stTabs [aria-selected="true"] { color: #63b3ed !important; }
    .stTabs [data-baseweb="tab-border"] { background-color: #63b3ed; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1a202c; border-radius: 8px; }

    hr { border-color: #2d3748; }
    label { color: #a0aec0 !important; }
    .stAlert { border-radius: 8px; }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
SECRET_KEY  = st.secrets.get("SECRET_KEY",  "pharma-ims-secret-2024")
ALLOWED_DOMAIN = "@morepenpdr.com"

DEPARTMENTS = ["IT", "Lab Maintenance", "Safety", "HR", "Facilities"]
CATEGORIES  = ["Equipment Failure", "Software Issue", "Safety Hazard",
                "Lab Supply", "Network/Connectivity", "HVAC/Environment",
                "Chemical Spill", "Documentation", "Other"]
PRIORITIES  = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ROLES       = ["scientist", "admin", "management"]

DEPT_EMAILS = {
    "IT":               st.secrets.get("IT_EMAIL",          "it@morepenpdr.com"),
    "Lab Maintenance":  st.secrets.get("LAB_EMAIL",         "lab@morepenpdr.com"),
    "Safety":           st.secrets.get("SAFETY_EMAIL",      "safety@morepenpdr.com"),
    "HR":               st.secrets.get("HR_EMAIL",          "hr@morepenpdr.com"),
    "Facilities":       st.secrets.get("FACILITIES_EMAIL",  "facilities@morepenpdr.com"),
}

# ─── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets.get("DB_PORT", 5432),
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def db():
    conn = get_db()
    if conn.closed:
        st.cache_resource.clear()
        conn = get_db()
    return conn

def run(sql, params=None, fetch="all"):
    conn = db()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()
        if fetch == "all":
            try:    return cur.fetchall()
            except: return []
        if fetch == "one":
            try:    return cur.fetchone()
            except: return None
        return None

# ─── EMAIL ──────────────────────────────────────────────────────────────────────
def send_email(to: str, subject: str, html: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = st.secrets["SMTP_FROM"]
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASS"])
            srv.sendmail(st.secrets["SMTP_FROM"], to, msg.as_string())
        return True
    except Exception as e:
        st.warning(f"Email not sent ({e}). Check SMTP secrets.")
        return False

def email_ticket_created(ticket, reporter_email, dept_email):
    html = f"""
    <div style="font-family:Inter,sans-serif;background:#0f1117;color:#e2e8f0;padding:30px;border-radius:12px;">
      <div style="background:linear-gradient(135deg,#1e3a5f,#2d1b69);padding:20px;border-radius:8px;margin-bottom:20px;">
        <h2 style="color:#63b3ed;margin:0;">💊 MorepenPDR — New Ticket #{ticket['ticket_id'][:8]}</h2>
      </div>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px;color:#718096;">Title</td>
            <td style="padding:8px;color:#e2e8f0;font-weight:600;">{ticket['title']}</td></tr>
        <tr style="background:#1a202c;">
            <td style="padding:8px;color:#718096;">Category</td>
            <td style="padding:8px;color:#e2e8f0;">{ticket['category']}</td></tr>
        <tr><td style="padding:8px;color:#718096;">Priority</td>
            <td style="padding:8px;color:#f6ad55;font-weight:600;">{ticket['priority']}</td></tr>
        <tr style="background:#1a202c;">
            <td style="padding:8px;color:#718096;">Reported by</td>
            <td style="padding:8px;color:#e2e8f0;">{reporter_email}</td></tr>
        <tr><td style="padding:8px;color:#718096;">Description</td>
            <td style="padding:8px;color:#e2e8f0;">{ticket['description']}</td></tr>
      </table>
      <p style="color:#718096;margin-top:20px;font-size:0.85rem;">
        Login to the portal to manage this ticket.
      </p>
    </div>"""
    send_email(dept_email, f"[MorepenPDR] New {ticket['priority']} Ticket: {ticket['title']}", html)

def email_feedback_request(ticket, reporter_email):
    feedback_url = f"https://your-app.streamlit.app/?feedback={ticket['ticket_id']}"
    html = f"""
    <div style="font-family:Inter,sans-serif;background:#0f1117;color:#e2e8f0;padding:30px;border-radius:12px;">
      <div style="background:linear-gradient(135deg,#1c4532,#276749);padding:20px;border-radius:8px;margin-bottom:20px;">
        <h2 style="color:#9ae6b4;margin:0;">✅ Your Issue Has Been Resolved!</h2>
      </div>
      <p>Hello,</p>
      <p>Your ticket <strong style="color:#63b3ed;">"{ticket['title']}"</strong> has been marked as resolved.</p>
      <p style="color:#718096;">Ticket ID: {ticket['ticket_id'][:8]}</p>
      <p>Please log in to the portal to rate your experience and provide feedback. Your feedback helps us improve our support quality.</p>
      <div style="background:#1a202c;border:1px solid #2d3748;border-radius:8px;padding:15px;margin:20px 0;">
        <p style="color:#718096;margin:0;">Rate 1–5 stars and leave a comment directly in the portal under <strong>My Tickets → Feedback</strong>.</p>
      </div>
      <p style="color:#718096;font-size:0.85rem;">Thank you for helping us improve — MorepenPDR IT & Support</p>
    </div>"""
    send_email(reporter_email, f"[MorepenPDR] Please Rate Your Support Experience — #{ticket['ticket_id'][:8]}", html)

# ─── AUTH ────────────────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=8)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data["sub"]
    except:
        return None

def login_user(email: str, password: str):
    if not email.endswith(ALLOWED_DOMAIN):
        return None, f"Only {ALLOWED_DOMAIN} emails are allowed."
    user = run("SELECT * FROM users WHERE email=%s AND is_active=TRUE", (email,), "one")
    if not user:
        return None, "User not found or account inactive."
    if not verify_password(password, user["password_hash"]):
        return None, "Incorrect password."
    return dict(user), None

def register_user(name, email, password, role, department=None):
    if not email.endswith(ALLOWED_DOMAIN):
        return False, f"Only {ALLOWED_DOMAIN} emails are allowed."
    existing = run("SELECT id FROM users WHERE email=%s", (email,), "one")
    if existing:
        return False, "Email already registered."
    uid = str(uuid.uuid4())
    run("""INSERT INTO users(id,name,email,password_hash,role,department,is_active,created_at)
           VALUES(%s,%s,%s,%s,%s,%s,TRUE,%s)""",
        (uid, name, email, hash_password(password), role, department, datetime.utcnow()))
    return True, "Account created successfully."

# ─── SESSION ────────────────────────────────────────────────────────────────────
def get_current_user():
    token = st.session_state.get("token")
    if not token:
        return None
    uid = verify_token(token)
    if not uid:
        return None
    user = run("SELECT * FROM users WHERE id=%s", (uid,), "one")
    return dict(user) if user else None

# ─── TICKET HELPERS ─────────────────────────────────────────────────────────────
def create_ticket(title, description, category, priority, assigned_to_dept, created_by_id):
    tid = str(uuid.uuid4())
    now = datetime.utcnow()
    run("""INSERT INTO tickets(id,title,description,category,priority,status,
                               created_by,assigned_to_dept,created_at,updated_at)
           VALUES(%s,%s,%s,%s,%s,'OPEN',%s,%s,%s,%s)""",
        (tid, title, description, category, priority, created_by_id, assigned_to_dept, now, now))
    return tid

def update_ticket_status(ticket_id, new_status, note, updated_by):
    now = datetime.utcnow()
    run("UPDATE tickets SET status=%s,updated_at=%s WHERE id=%s", (new_status, now, ticket_id))
    run("""INSERT INTO ticket_updates(id,ticket_id,updated_by,old_status,new_status,note,created_at)
           VALUES(%s,%s,%s,(SELECT status FROM tickets WHERE id=%s),%s,%s,%s)""",
        (str(uuid.uuid4()), ticket_id, updated_by, ticket_id, new_status, note, now))

def submit_feedback(ticket_id, rating, comment):
    run("""INSERT INTO feedback(id,ticket_id,rating,comment,created_at)
           VALUES(%s,%s,%s,%s,%s)
           ON CONFLICT(ticket_id) DO UPDATE SET rating=%s,comment=%s,created_at=%s""",
        (str(uuid.uuid4()), ticket_id, rating, comment, datetime.utcnow(),
         rating, comment, datetime.utcnow()))

# ─── UI HELPERS ─────────────────────────────────────────────────────────────────
def badge(text, kind="status"):
    return f'<span class="{kind}-badge {kind}-{text}">{text}</span>'

def ticket_card(t, show_actions=False, user=None):
    priority_color = {"CRITICAL":"#fc8181","HIGH":"#f6ad55","MEDIUM":"#68d391","LOW":"#63b3ed"}
    border = priority_color.get(t.get("priority","LOW"), "#4a90d9")
    st.markdown(f"""
    <div class="ticket-card" style="border-left-color:{border}">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div>
          <span style="color:#63b3ed;font-size:0.75rem;font-weight:600;">
            #{str(t['id'])[:8].upper()}
          </span>
          <h4 style="color:#e2e8f0;margin:4px 0;">{t['title']}</h4>
        </div>
        <div>
          {badge(t['status'],'status')}
          {badge(t['priority'],'priority')}
        </div>
      </div>
      <p style="color:#a0aec0;font-size:0.88rem;margin:8px 0;">{t['description'][:200]}{"..." if len(t['description'])>200 else ""}</p>
      <div style="display:flex;gap:20px;font-size:0.8rem;color:#718096;margin-top:8px;">
        <span>📂 {t['category']}</span>
        <span>🏢 {t['assigned_to_dept']}</span>
        <span>🕐 {str(t['created_at'])[:16]}</span>
      </div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:2rem;">
          <div style="font-size:3rem;">💊</div>
          <h1 style="color:#63b3ed;font-size:1.6rem;margin:0;">MorepenPDR</h1>
          <p style="color:#718096;font-size:0.9rem;">Issue Management System</p>
        </div>""", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="you@morepenpdr.com", key="li_email")
            password = st.text_input("Password", type="password", key="li_pass")
            if st.button("Sign In", use_container_width=True):
                if email and password:
                    user, err = login_user(email.strip().lower(), password)
                    if user:
                        st.session_state.token = create_token(user["id"])
                        st.rerun()
                    else:
                        st.error(err)
                else:
                    st.warning("Please enter email and password.")

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            name  = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email (@morepenpdr.com)", key="reg_email")
            role  = st.selectbox("Role", ["scientist", "admin", "management"], key="reg_role")
            dept  = st.selectbox("Department (Admin only)", ["—"] + DEPARTMENTS, key="reg_dept") \
                    if role == "admin" else None
            pwd1  = st.text_input("Password", type="password", key="reg_p1")
            pwd2  = st.text_input("Confirm Password", type="password", key="reg_p2")
            if st.button("Create Account", use_container_width=True):
                if not all([name, email, pwd1, pwd2]):
                    st.warning("All fields required.")
                elif pwd1 != pwd2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(
                        name.strip(), email.strip().lower(), pwd1,
                        role, dept if dept and dept != "—" else None
                    )
                    if ok: st.success(msg + " Please sign in.")
                    else:  st.error(msg)

# ═══════════════════════════════════════════════════════════════════════════════
# SCIENTIST DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_scientist(user):
    st.markdown(f"""
    <div class="main-header">
      <h1>🔬 Scientist Portal</h1>
      <p>Welcome, {user['name']} · {user['email']}</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["➕ New Ticket", "📋 My Tickets", "⭐ Feedback"])

    # ── NEW TICKET ──────────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<p class="section-title">Report a New Issue</p>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            title    = st.text_input("Issue Title *")
            category = st.selectbox("Category *", CATEGORIES)
            priority = st.selectbox("Priority *", PRIORITIES, index=1)
        with col_b:
            dept = st.selectbox("Assign to Department *", DEPARTMENTS)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""<div class="info-box">
              📧 This ticket will be emailed to:<br>
              <strong>{DEPT_EMAILS.get(dept,'dept@morepenpdr.com')}</strong>
            </div>""", unsafe_allow_html=True)
        description = st.text_area("Detailed Description *", height=120)

        if st.button("🚀 Submit Ticket", use_container_width=True):
            if title and description and category and dept:
                tid = create_ticket(title, description, category, priority, dept, user["id"])
                ticket = run("SELECT * FROM tickets WHERE id=%s", (tid,), "one")
                email_ticket_created(dict(ticket), user["email"], DEPT_EMAILS.get(dept,""))
                st.markdown(f"""<div class="success-box">
                  ✅ Ticket <strong>#{tid[:8].upper()}</strong> submitted and email sent to {dept} team.
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("Please fill in all required fields.")

    # ── MY TICKETS ──────────────────────────────────────────────────────────────
    with tab2:
        tickets = run("""
            SELECT t.*, f.rating, f.comment as feedback_comment
            FROM tickets t
            LEFT JOIN feedback f ON f.ticket_id = t.id
            WHERE t.created_by=%s ORDER BY t.created_at DESC
        """, (user["id"],))

        search = st.text_input("🔍 Search tickets", placeholder="Search by title or category")
        status_filter = st.multiselect("Filter by Status", ["OPEN","ASSIGNED","IN_PROGRESS","RESOLVED","CLOSED"])

        if not tickets:
            st.info("You have not submitted any tickets yet.")
        else:
            df = [dict(t) for t in tickets]
            if search:
                df = [t for t in df if search.lower() in t["title"].lower()
                      or search.lower() in t["category"].lower()]
            if status_filter:
                df = [t for t in df if t["status"] in status_filter]
            for t in df:
                ticket_card(t)

    # ── FEEDBACK ─────────────────────────────────────────────────────────────────
    with tab3:
        resolved = run("""
            SELECT t.*, f.rating, f.comment as feedback_comment
            FROM tickets t LEFT JOIN feedback f ON f.ticket_id=t.id
            WHERE t.created_by=%s AND t.status IN ('RESOLVED','CLOSED')
            ORDER BY t.updated_at DESC
        """, (user["id"],))

        if not resolved:
            st.info("No resolved tickets yet. Feedback will appear here once your tickets are resolved.")
        else:
            for t in resolved:
                t = dict(t)
                with st.expander(f"#{t['id'][:8].upper()} — {t['title']}", expanded=not t.get("rating")):
                    if t.get("rating"):
                        stars = "⭐" * int(t["rating"])
                        st.markdown(f"""<div class="success-box">
                          Feedback submitted: {stars} ({t['rating']}/5)<br>
                          <em>{t.get('feedback_comment','')}</em>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-box">⏳ Feedback pending — please rate your experience.</div>',
                                    unsafe_allow_html=True)
                        rating  = st.slider("Rating", 1, 5, 4, key=f"r_{t['id']}")
                        comment = st.text_area("Comments", key=f"c_{t['id']}")
                        if st.button("Submit Feedback", key=f"fb_{t['id']}"):
                            submit_feedback(t["id"], rating, comment)
                            st.success("Thank you for your feedback!")
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_admin(user):
    st.markdown(f"""
    <div class="main-header">
      <h1>🛠️ Admin Panel — {user.get('department','Support')}</h1>
      <p>Support Portal · {user['name']} · {user['email']}</p>
    </div>""", unsafe_allow_html=True)

    dept = user.get("department")
    where_clause = "WHERE t.assigned_to_dept=%s" if dept else "WHERE 1=1"
    params = (dept,) if dept else ()

    tickets = run(f"""
        SELECT t.*, u.name as reporter_name, u.email as reporter_email
        FROM tickets t
        LEFT JOIN users u ON u.id = t.created_by
        {where_clause} ORDER BY
          CASE t.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                          WHEN 'MEDIUM' THEN 3 ELSE 4 END,
          t.created_at DESC
    """, params)

    # Metrics row
    all_t  = [dict(t) for t in tickets]
    open_t = [t for t in all_t if t["status"] == "OPEN"]
    prog_t = [t for t in all_t if t["status"] == "IN_PROGRESS"]
    res_t  = [t for t in all_t if t["status"] in ("RESOLVED","CLOSED")]

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, len(all_t),   "Total Tickets"),
        (c2, len(open_t),  "Open"),
        (c3, len(prog_t),  "In Progress"),
        (c4, len(res_t),   "Resolved"),
    ]:
        col.markdown(f"""<div class="metric-card">
          <div class="value">{val}</div>
          <div class="label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    search        = col_f1.text_input("🔍 Search", placeholder="Title / category")
    status_filter = col_f2.multiselect("Status", ["OPEN","ASSIGNED","IN_PROGRESS","RESOLVED","CLOSED"])
    prio_filter   = col_f3.multiselect("Priority", PRIORITIES)

    filtered = all_t
    if search:        filtered = [t for t in filtered if search.lower() in t["title"].lower()]
    if status_filter: filtered = [t for t in filtered if t["status"] in status_filter]
    if prio_filter:   filtered = [t for t in filtered if t["priority"] in prio_filter]

    if not filtered:
        st.info("No tickets match the current filters.")
    else:
        for t in filtered:
            ticket_card(t)
            with st.expander(f"🔧 Manage ticket #{t['id'][:8].upper()}"):
                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown(f"**Reporter:** {t.get('reporter_name','')} ({t.get('reporter_email','')})")
                    st.markdown(f"**Current Status:** `{t['status']}`")
                    st.markdown(f"**Created:** {str(t['created_at'])[:16]}")
                    st.markdown(f"**Description:**\n{t['description']}")
                with col_r:
                    STATUS_FLOW = {
                        "OPEN":        ["ASSIGNED"],
                        "ASSIGNED":    ["IN_PROGRESS"],
                        "IN_PROGRESS": ["RESOLVED"],
                        "RESOLVED":    ["CLOSED"],
                        "CLOSED":      [],
                    }
                    next_statuses = STATUS_FLOW.get(t["status"], [])
                    if next_statuses:
                        new_status = st.selectbox("Move to Status",
                                                  next_statuses, key=f"ns_{t['id']}")
                        note = st.text_area("Resolution Note", key=f"note_{t['id']}", height=80)
                        if st.button("✅ Update Status", key=f"upd_{t['id']}"):
                            update_ticket_status(t["id"], new_status, note, user["id"])
                            if new_status == "RESOLVED" and t.get("reporter_email"):
                                email_feedback_request(t, t["reporter_email"])
                                st.success("Status updated & feedback email sent to reporter!")
                            else:
                                st.success("Status updated!")
                            st.rerun()
                    else:
                        st.markdown('<div class="success-box">✅ Ticket is closed.</div>',
                                    unsafe_allow_html=True)

                # History
                history = run("""
                    SELECT tu.*, u.name as updater
                    FROM ticket_updates tu
                    LEFT JOIN users u ON u.id=tu.updated_by
                    WHERE tu.ticket_id=%s ORDER BY tu.created_at DESC
                """, (t["id"],))
                if history:
                    st.markdown("**Update History:**")
                    for h in history:
                        h = dict(h)
                        st.markdown(f"""
                        <div style="background:#1a202c;border-left:3px solid #4a5568;
                             padding:8px 12px;margin:4px 0;border-radius:4px;font-size:0.85rem;">
                          <span style="color:#63b3ed;">{h.get('updater','?')}</span>
                          moved to <strong>{h['new_status']}</strong>
                          · {str(h['created_at'])[:16]}
                          {f"<br><em style='color:#a0aec0;'>{h['note']}</em>" if h.get('note') else ""}
                        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MANAGEMENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_management(user):
    st.markdown(f"""
    <div class="main-header">
      <h1>📊 Executive Dashboard</h1>
      <p>Management Overview · {user['name']} · {user['email']}</p>
    </div>""", unsafe_allow_html=True)

    tickets = run("""
        SELECT t.*, u.name as reporter_name, u.department as reporter_dept,
               f.rating
        FROM tickets t
        LEFT JOIN users u ON u.id=t.created_by
        LEFT JOIN feedback f ON f.ticket_id=t.id
        ORDER BY t.created_at DESC
    """)

    if not tickets:
        st.info("No tickets in the system yet.")
        return

    df = pd.DataFrame([dict(t) for t in tickets])

    # ── KPI Row ──
    total    = len(df)
    open_c   = len(df[df.status=="OPEN"])
    res_c    = len(df[df.status.isin(["RESOLVED","CLOSED"])])
    avg_rat  = round(df["rating"].dropna().mean(), 1) if not df["rating"].dropna().empty else "—"

    kpis = [
        ("Total Tickets",   total,   "#63b3ed"),
        ("Open",            open_c,  "#fc8181"),
        ("Resolved",        res_c,   "#68d391"),
        ("Avg Satisfaction",avg_rat, "#f6ad55"),
    ]
    cols = st.columns(4)
    for col, (lbl, val, color) in zip(cols, kpis):
        col.markdown(f"""<div class="metric-card">
          <div class="value" style="color:{color};">{val}</div>
          <div class="label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Tickets by Department</p>', unsafe_allow_html=True)
        dept_counts = df.groupby("assigned_to_dept").size().reset_index(name="count")
        fig1 = px.bar(dept_counts, x="assigned_to_dept", y="count",
                      color="count", color_continuous_scale="blues",
                      labels={"assigned_to_dept":"Department","count":"Tickets"})
        fig1.update_layout(
            paper_bgcolor="#1a202c", plot_bgcolor="#1a202c",
            font_color="#a0aec0", showlegend=False,
            margin=dict(l=20,r=20,t=20,b=20)
        )
        fig1.update_xaxes(tickfont_color="#a0aec0")
        fig1.update_yaxes(tickfont_color="#a0aec0")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Tickets by Status</p>', unsafe_allow_html=True)
        status_counts = df.groupby("status").size().reset_index(name="count")
        colors = {"OPEN":"#63b3ed","ASSIGNED":"#90cdf4","IN_PROGRESS":"#f6ad55",
                  "RESOLVED":"#68d391","CLOSED":"#718096"}
        fig2 = px.pie(status_counts, names="status", values="count",
                      color="status", color_discrete_map=colors, hole=0.5)
        fig2.update_layout(
            paper_bgcolor="#1a202c", plot_bgcolor="#1a202c",
            font_color="#a0aec0", margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<p class="section-title">Tickets by Priority</p>', unsafe_allow_html=True)
        prio_counts = df.groupby("priority").size().reset_index(name="count")
        prio_colors = {"CRITICAL":"#fc8181","HIGH":"#f6ad55","MEDIUM":"#68d391","LOW":"#63b3ed"}
        fig3 = px.bar(prio_counts, x="priority", y="count",
                      color="priority", color_discrete_map=prio_colors)
        fig3.update_layout(
            paper_bgcolor="#1a202c", plot_bgcolor="#1a202c",
            font_color="#a0aec0", showlegend=False,
            margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown('<p class="section-title">Most Common Categories</p>', unsafe_allow_html=True)
        cat_counts = df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=True)
        fig4 = px.bar(cat_counts, x="count", y="category", orientation="h",
                      color="count", color_continuous_scale="teal")
        fig4.update_layout(
            paper_bgcolor="#1a202c", plot_bgcolor="#1a202c",
            font_color="#a0aec0", showlegend=False,
            margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Avg resolution time ──
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    resolved_df = df[df.status.isin(["RESOLVED","CLOSED"])].copy()
    if not resolved_df.empty:
        resolved_df["hours_to_resolve"] = (
            resolved_df["updated_at"] - resolved_df["created_at"]
        ).dt.total_seconds() / 3600
        avg_by_dept = resolved_df.groupby("assigned_to_dept")["hours_to_resolve"].mean().reset_index()
        avg_by_dept.columns = ["Department","Avg Hours to Resolve"]
        st.markdown('<p class="section-title">Avg Resolution Time by Department (hours)</p>',
                    unsafe_allow_html=True)
        fig5 = px.bar(avg_by_dept, x="Department", y="Avg Hours to Resolve",
                      color="Avg Hours to Resolve", color_continuous_scale="reds")
        fig5.update_layout(
            paper_bgcolor="#1a202c", plot_bgcolor="#1a202c",
            font_color="#a0aec0", showlegend=False,
            margin=dict(l=20,r=20,t=20,b=20)
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ── All Tickets Table ──
    st.markdown('<p class="section-title">All Tickets</p>', unsafe_allow_html=True)
    display_df = df[["id","title","category","priority","status",
                      "assigned_to_dept","reporter_name","created_at"]].copy()
    display_df["id"] = display_df["id"].str[:8].str.upper()
    display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M")
    display_df.columns = ["ID","Title","Category","Priority","Status",
                          "Department","Reporter","Created"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def sidebar(user):
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0;">
          <div style="font-size:2.5rem;">💊</div>
          <div style="color:#63b3ed;font-size:1.1rem;font-weight:700;">MorepenPDR</div>
          <div style="color:#718096;font-size:0.75rem;">Issue Management System</div>
        </div>
        <hr style="border-color:#2d3748;margin:0.5rem 0 1rem;">
        """, unsafe_allow_html=True)

        role_icons = {"scientist":"🔬","admin":"🛠️","management":"📊"}
        st.markdown(f"""
        <div style="background:#1a202c;border:1px solid #2d3748;border-radius:10px;
             padding:1rem;margin-bottom:1.5rem;">
          <div style="color:#63b3ed;font-size:1.5rem;text-align:center;">
            {role_icons.get(user['role'],'👤')}
          </div>
          <div style="color:#e2e8f0;font-weight:600;text-align:center;margin-top:4px;">
            {user['name']}
          </div>
          <div style="color:#718096;font-size:0.8rem;text-align:center;">{user['email']}</div>
          <div style="text-align:center;margin-top:8px;">
            <span style="background:#2c5282;color:#bee3f8;padding:2px 10px;
              border-radius:20px;font-size:0.75rem;font-weight:600;">
              {user['role'].upper()}
            </span>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            del st.session_state["token"]
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="color:#4a5568;font-size:0.75rem;text-align:center;margin-top:1rem;">
          MorepenPDR IMS v1.0<br>
          Internal use only
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    user = get_current_user()

    if not user:
        page_login()
        return

    sidebar(user)

    role = user.get("role", "scientist")
    if role == "scientist":
        page_scientist(user)
    elif role == "admin":
        page_admin(user)
    elif role == "management":
        page_management(user)
    else:
        st.error("Unknown role. Please contact administrator.")

if __name__ == "__main__":
    main()
