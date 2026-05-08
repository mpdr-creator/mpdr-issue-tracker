import uuid
import pandas as pd

# HRMS Database schema operations
def all_hrms_profiles(get_or_create_sheet, safe_get_all_records):
    try:
        ws = get_or_create_sheet("hrms_profiles", ["email", "full_name", "designation", "department", "phone", "emergency_contact", "present_address", "permanent_address", "updated_at"])
        return safe_get_all_records(ws)
    except:
        return []

def get_hrms_profile(email, get_or_create_sheet, safe_get_all_records):
    profiles = all_hrms_profiles(get_or_create_sheet, safe_get_all_records)
    for p in profiles:
        if p["email"] == email:
            return p
    return None

def update_hrms_profile(email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_profiles", ["email", "full_name", "designation", "department", "phone", "emergency_contact", "present_address", "permanent_address", "updated_at"])
    recs = safe_get_all_records(ws)
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    for i, r in enumerate(recs, start=2):
        if str(r.get("email", "")) == email:
            ws.update(f"B{i}:I{i}", [[full_name, designation, department, phone, emergency_contact, present_address, permanent_address, now]])
            return
    ws.append_row([email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, now])

def all_hrms_kras(get_or_create_sheet, safe_get_all_records):
    try:
        ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "status", "submitted_at", "assessed_at", "assessment_notes", "rating"])
        return safe_get_all_records(ws)
    except:
        return []

def submit_kra(email, year, quarter, objectives, achievements, challenges, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "status", "submitted_at", "assessed_at", "assessment_notes", "rating"])
    kra_id = str(uuid.uuid4())[:8].upper()
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([kra_id, email, year, quarter, objectives, achievements, challenges, "SUBMITTED", now, "", "", ""])

def assess_kra(kra_id, notes, rating, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "status", "submitted_at", "assessed_at", "assessment_notes", "rating"])
    recs = safe_get_all_records(ws)
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    for i, r in enumerate(recs, start=2):
        if str(r.get("kra_id", "")) == kra_id:
            ws.update(f"H{i}:L{i}", [["ASSESSED", r["submitted_at"], now, notes, rating]])
            return

# UI Rendering functions
def page_hrms_profile(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("<h2 style='color:#0d2d5e;'>👤 My Profile & Info</h2>", unsafe_allow_html=True)
    
    email = session_state.email
    if email == "hr@morepenpdr.com":
        st.info("ℹ️ HR profiles are not required to fill personal information.")
        return

    profile = get_hrms_profile(email, get_or_create_sheet, safe_get_all_records)
    
    with st.form("profile_form"):
        st.markdown("### Personal & Emergency Information")
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=profile.get("full_name", "") if profile else "")
            department = st.text_input("Department", value=profile.get("department", session_state.get("dept", "")) if profile else session_state.get("dept", ""), disabled=True)
            phone = st.text_input("Phone Number", value=profile.get("phone", "") if profile else "")
            
        with col2:
            st.text_input("Email", value=email, disabled=True)
            designation = st.text_input("Designation", value=profile.get("designation", "") if profile else "")
            emergency_contact = st.text_input("Emergency Contact (Name & Phone)", value=profile.get("emergency_contact", "") if profile else "")
            
        st.markdown("### Address Details")
        present_address = st.text_area("Present Address", value=profile.get("present_address", "") if profile else "")
        permanent_address = st.text_area("Permanent Address", value=profile.get("permanent_address", "") if profile else "")
        
        submitted = st.form_submit_button("Save Profile", type="primary")
        if submitted:
            if not full_name or not phone:
                st.error("Full Name and Phone Number are required.")
            else:
                with st.spinner("Saving profile..."):
                    update_hrms_profile(email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, get_or_create_sheet, safe_get_all_records, now_ist)
                st.success("Profile saved successfully!")
                st.rerun()

def page_hrms_kra(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("<h2 style='color:#0d2d5e;'>📝 My KRA Submission</h2>", unsafe_allow_html=True)
    
    email = session_state.email
    kras = [k for k in all_hrms_kras(get_or_create_sheet, safe_get_all_records) if k.get("email") == email]
    
    tab1, tab2 = st.tabs(["Submit New KRA", "My Previous KRAs"])
    
    with tab1:
        with st.form("kra_form"):
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("Year", ["2024", "2025", "2026"])
            with col2:
                quarter = st.selectbox("Quarter / Cycle", ["Q1", "Q2", "Q3", "Q4", "Annual"])
                
            objectives = st.text_area("Key Objectives (Set at the beginning)", height=150)
            achievements = st.text_area("Achievements & Deliverables", height=150)
            challenges = st.text_area("Challenges & Support Required", height=100)
            
            submitted = st.form_submit_button("Submit KRA for Assessment", type="primary")
            if submitted:
                if not objectives or not achievements:
                    st.error("Objectives and Achievements are required.")
                else:
                    with st.spinner("Submitting KRA..."):
                        submit_kra(email, year, quarter, objectives, achievements, challenges, get_or_create_sheet, safe_get_all_records, now_ist)
                    st.success("KRA submitted successfully!")
                    st.rerun()
                    
    with tab2:
        if not kras:
            st.info("No KRAs submitted yet.")
        else:
            for k in reversed(kras):
                status_color = "#f0a500" if k["status"] == "SUBMITTED" else "#3fb950"
                st.markdown(f"""
                <div style="background:white;padding:1.5rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:1rem;border-left:4px solid {status_color};">
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                        <span style="font-weight:600;color:#0d2d5e;font-size:1.1rem;">KRA: {k['year']} - {k['quarter']}</span>
                        <span style="background:{status_color};color:white;padding:2px 8px;border-radius:12px;font-size:0.8rem;font-weight:bold;">{k['status']}</span>
                    </div>
                    <div style="margin-bottom:0.5rem;"><strong>Objectives:</strong><br>{k['objectives']}</div>
                    <div style="margin-bottom:0.5rem;"><strong>Achievements:</strong><br>{k['achievements']}</div>
                """, unsafe_allow_html=True)
                
                if k["status"] == "ASSESSED":
                    st.markdown(f"""
                    <div style="margin-top:1rem;padding:1rem;background:#f8f9fa;border-radius:6px;border:1px solid #e1e4e8;">
                        <strong style="color:#0d2d5e;">Manager Assessment:</strong><br>
                        {k['assessment_notes']}<br><br>
                        <strong style="color:#3fb950;">Rating: {k['rating']} / 5</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("</div>", unsafe_allow_html=True)

def page_hrms_db(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("<h2 style='color:#0d2d5e;'>🏢 Employee Database</h2>", unsafe_allow_html=True)
    
    profiles = all_hrms_profiles(get_or_create_sheet, safe_get_all_records)
    if not profiles:
        st.info("No employee profiles found.")
        return
        
    df = pd.DataFrame(profiles)
    
    # Show more columns for HR/Management
    if session_state.role == "management" or session_state.email == "hr@morepenpdr.com":
        display_df = df[['full_name', 'email', 'department', 'designation', 'phone', 'emergency_contact', 'present_address', 'permanent_address', 'updated_at']].copy()
    else:
        display_df = df[['full_name', 'email', 'department', 'designation', 'phone', 'updated_at']].copy()
    
    search = st.text_input("🔍 Search Employees", placeholder="Name, Email, or Department...")
    if search:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        display_df = display_df[mask]
        
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def page_hrms_assess(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("<h2 style='color:#0d2d5e;'>📊 KRA Assessments</h2>", unsafe_allow_html=True)
    
    kras = all_hrms_kras(get_or_create_sheet, safe_get_all_records)
    if not kras:
        st.info("No KRAs available.")
        return
        
    pending = [k for k in kras if k["status"] == "SUBMITTED"]
    assessed = [k for k in kras if k["status"] == "ASSESSED"]
    
    tab1, tab2 = st.tabs([f"Pending Assessment ({len(pending)})", f"Assessed ({len(assessed)})"])
    
    with tab1:
        if not pending:
            st.success("All KRAs have been assessed!")
        else:
            for k in pending:
                with st.expander(f"KRA: {k['full_name'] if 'full_name' in k else k['email']} | {k['year']} {k['quarter']}"):
                    st.markdown(f"**Objectives:** {k['objectives']}")
                    st.markdown(f"**Achievements:** {k['achievements']}")
                    st.markdown(f"**Challenges:** {k['challenges']}")
                    
                    with st.form(f"assess_form_{k['kra_id']}"):
                        notes = st.text_area("Assessment Notes / Feedback")
                        rating = st.slider("Rating (1-5)", 1, 5, 3)
                        
                        if st.form_submit_button("Submit Assessment", type="primary"):
                            with st.spinner("Saving assessment..."):
                                assess_kra(k['kra_id'], notes, rating, get_or_create_sheet, safe_get_all_records, now_ist)
                            st.success("Assessment saved!")
                            st.rerun()
                            
    with tab2:
        if not assessed:
            st.info("No assessed KRAs.")
        else:
            for k in reversed(assessed):
                st.markdown(f"""
                <div style="background:white;padding:1.5rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:1rem;border-left:4px solid #3fb950;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                        <span style="font-weight:600;color:#0d2d5e;font-size:1.1rem;">{k['email']} - {k['year']} {k['quarter']}</span>
                        <span style="color:#3fb950;font-weight:bold;">Rating: {k['rating']}/5</span>
                    </div>
                    <div style="margin-bottom:0.5rem;"><strong>Assessment Notes:</strong><br>{k['assessment_notes']}</div>
                </div>
                """, unsafe_allow_html=True)
