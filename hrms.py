import uuid
import json
import pandas as pd

# HRMS Constants
DEPARTMENTS = ["Admin", "CADD", "MedChem", "API", "AR&D", "CDMO", "SSD"]

# HRMS Database schema operations
def all_hrms_profiles(get_or_create_sheet, safe_get_all_records):
    try:
        # Fetch HRMS profiles
        p_ws = get_or_create_sheet("hrms_profiles", ["email", "full_name", "designation", "department", "phone", "emergency_contact", "present_address", "permanent_address", "transport_required", "health_issues", "updated_at"])
        profiles = safe_get_all_records(p_ws)
        
        # Fetch User registration data for fallbacks
        u_ws = get_or_create_sheet("users", ["email", "password", "role", "department", "created_at"])
        users = safe_get_all_records(u_ws)
        
        # Create a merged map
        merged = {u["email"]: {
            "email": u["email"],
            "full_name": u["email"].split('@')[0].replace('.', ' ').title(),
            "department": u.get("department", "Unknown Dept"),
            "designation": "Staff",
            "phone": "",
            "emergency_contact": "",
            "present_address": "",
            "permanent_address": "",
            "transport_required": "No",
            "health_issues": "",
            "updated_at": u.get("created_at", "")
        } for u in users}
        
        # Overlay with actual profile data
        for p in profiles:
            email = p.get("email")
            if email:
                if email not in merged:
                    merged[email] = p
                else:
                    merged[email].update(p)
                    
        return list(merged.values())
    except Exception as e:
        print(f"Error fetching profiles: {e}")
        return []

def get_hrms_profile(email, get_or_create_sheet, safe_get_all_records):
    profiles = all_hrms_profiles(get_or_create_sheet, safe_get_all_records)
    for p in profiles:
        if p["email"] == email:
            return p
    return None

def update_hrms_profile(email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, transport_required, health_issues, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_profiles", ["email", "full_name", "designation", "department", "phone", "emergency_contact", "present_address", "permanent_address", "transport_required", "health_issues", "updated_at"])
    recs = safe_get_all_records(ws)
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    for i, r in enumerate(recs, start=2):
        if str(r.get("email", "")) == email:
            ws.update(f"B{i}:K{i}", [[full_name, designation, department, phone, emergency_contact, present_address, permanent_address, transport_required, health_issues, now]])
            return
    ws.append_row([email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, transport_required, health_issues, now])

def all_hrms_kras(get_or_create_sheet, safe_get_all_records):
    try:
        ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "tech_assessment", "status", "submitted_at", "assessed_at", "assessment_notes", "rating", "behavioral_assessment"])
        return safe_get_all_records(ws)
    except:
        return []

def render_kra_table(st, data_list, headers):
    if not data_list: return
    
    # Create HTML Table
    header_html = "".join([f'<th style="background:#f8fafc;color:#475569;padding:12px;text-align:left;border-bottom:2px solid #e2e8f0;font-weight:600;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.025em;">{h}</th>' for h in headers])
    
    rows_html = ""
    for item in data_list:
        row_cells = ""
        for h in headers:
            val = item.get(h, "")
            # Apply wrapping and padding
            row_cells += f'<td style="padding:12px;border-bottom:1px solid #f1f5f9;color:#1e293b;font-size:0.9rem;line-height:1.5;vertical-align:top;word-wrap:break-word;max-width:300px;">{val}</td>'
        rows_html += f'<tr>{row_cells}</tr>'
        
    st.markdown(f"""
    <div style="overflow-x:auto;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);margin-bottom:1.5rem;background:white;">
        <table style="width:100%;border-collapse:collapse;table-layout:auto;">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

def render_status_grid(st, rows, cycles):
    # CSS for the status grid
    st.markdown("""
    <style>
    .kra-summary-table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-family: 'Inter', sans-serif; border-radius: 8px; overflow: hidden; }
    .kra-summary-table th { background: #f1f5f9; color: #0d2d5e; padding: 12px; border: 1px solid #cbd5e1; font-weight: bold; text-align: center; }
    .kra-summary-table td { border: 1px solid #cbd5e1; padding: 0; text-align: center; font-size: 0.9rem; }
    .emp-name-cell { background: #1f4e78; color: white !important; font-weight: bold; padding: 10px !important; text-align: left !important; min-width: 150px; }
    .status-cell { font-weight: bold; width: 120px; }
    .status-done { background-color: #92d050; color: black; } 
    .status-pending { background-color: #ffc000; color: black; }
    .status-na { background-color: #ff0000; color: white; }
    </style>
    """, unsafe_allow_html=True)
    
    header = "<tr><th>Employee</th>" + "".join([f"<th>{c}</th>" for c in cycles]) + "</tr>"
    
    body = ""
    for row in rows:
        cells = f'<td class="emp-name-cell">{row["Employee"]}</td>'
        for c in cycles:
            status = row[c]
            cls = "status-na"
            if status == "Done": cls = "status-done"
            elif status == "Pending": cls = "status-pending"
            cells += f'<td class="status-cell {cls}">{status}</td>'
        body += f"<tr>{cells}</tr>"
        
    st.markdown(f'<div style="overflow-x:auto;"><table class="kra-summary-table"><thead>{header}</thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)

def submit_kra(email, year, quarter, objectives, achievements, challenges, tech_assessment, behavioral_assessment, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "tech_assessment", "status", "submitted_at", "assessed_at", "assessment_notes", "rating", "behavioral_assessment"])
    kra_id = str(uuid.uuid4())[:8].upper()
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    tech_json = json.dumps(tech_assessment)
    behav_json = json.dumps(behavioral_assessment)
    ws.append_row([kra_id, email, year, quarter, objectives, achievements, challenges, tech_json, "SUBMITTED", now, "", "", "", behav_json])
    st.cache_data.clear()

def assess_kra(kra_id, notes, rating, tech_assessment, behavioral_assessment, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "tech_assessment", "status", "submitted_at", "assessed_at", "assessment_notes", "rating", "behavioral_assessment"])
    recs = safe_get_all_records(ws)
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    tech_json = json.dumps(tech_assessment)
    behav_json = json.dumps(behavioral_assessment)
    for i, r in enumerate(recs, start=2):
        if str(r.get("kra_id", "")) == kra_id:
            ws.update(f"H{i}:N{i}", [[tech_json, "ASSESSED", r["submitted_at"], now, notes, rating, behav_json]])
            return

def delete_kra(kra_id, get_or_create_sheet, safe_get_all_records):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "tech_assessment", "status", "submitted_at", "assessed_at", "assessment_notes", "rating", "behavioral_assessment"])
    recs = safe_get_all_records(ws)
    for i, r in enumerate(recs, start=2):
        if str(r.get("kra_id", "")) == kra_id:
            ws.delete_rows(i)
            st.cache_data.clear()
            return

# UI Rendering functions
def page_hrms_profile(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("""
    <div class="page-header">
        <div class="page-title">👤 My Profile & Info</div>
        <div class="page-sub">Keep your personal and emergency contact information up to date</div>
    </div>
    """, unsafe_allow_html=True)
    
    email = session_state.email
    if email == "hr@morepenpdr.com":
        st.markdown('<div class="alert-info">ℹ️ HR profiles are not required to fill personal information. Access the Employee Database to view other profiles.</div>', unsafe_allow_html=True)
        return

    profile = get_hrms_profile(email, get_or_create_sheet, safe_get_all_records)
    
    with st.form("profile_form"):
        st.markdown("### Personal & Emergency Information")
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=profile.get("full_name", "") if profile else "")
            
            current_dept = profile.get("department", session_state.get("dept", "")) if profile else session_state.get("dept", "")
            try:
                dept_index = DEPARTMENTS.index(current_dept)
            except:
                dept_index = 0
            department = st.selectbox("Department", DEPARTMENTS, index=dept_index)
            
            phone = st.text_input("Phone Number", value=profile.get("phone", "") if profile else "")
            
        with col2:
            st.text_input("Email", value=email, disabled=True)
            designation = st.text_input("Designation", value=profile.get("designation", "") if profile else "")
            emergency_contact = st.text_input("Emergency Contact (Name & Phone)", value=profile.get("emergency_contact", "") if profile else "")
            
        st.markdown("### Address Details")
        present_address = st.text_area("Present Address", value=profile.get("present_address", "") if profile else "")
        permanent_address = st.text_area("Permanent Address", value=profile.get("permanent_address", "") if profile else "")
        
        st.markdown("### Additional Information")
        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            transport_required = st.selectbox("Office Transport Facility Required?", ["No", "Yes"], index=0 if (not profile or profile.get("transport_required", "No")=="No") else 1)
        with col_extra2:
            health_issues = st.text_area("Any Health Issues / Medical Conditions", value=profile.get("health_issues", "") if profile else "", height=100)
        
        submitted = st.form_submit_button("Save Profile", type="primary")
        if submitted:
            if not full_name or not phone:
                st.error("Full Name and Phone Number are required.")
            else:
                with st.spinner("Saving profile..."):
                    update_hrms_profile(email, full_name, designation, department, phone, emergency_contact, present_address, permanent_address, transport_required, health_issues, get_or_create_sheet, safe_get_all_records, now_ist)
                st.success("Profile saved successfully!")
                st.rerun()

def page_hrms_kra(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📝 KRA & Performance</div>
        <div class="page-sub">Submit your Key Result Areas and track performance cycles</div>
    </div>
    """, unsafe_allow_html=True)
    
    email = session_state.email
    kras = [k for k in all_hrms_kras(get_or_create_sheet, safe_get_all_records) if k.get("email") == email]
    
    tab1, tab2 = st.tabs(["Submit New KRA", "My Previous KRAs"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Year", ["2024", "2025", "2026", "2027"])
        with col2:
            quarter = st.selectbox("Quarter / Cycle", ["Q1", "Q2", "Q3", "Q4", "Half-Yearly", "Annual"])

        can_submit = True
        existing_kra = next((k for k in kras if str(k["year"]) == str(year) and str(k["quarter"]) == str(quarter)), None)
        
        if existing_kra:
            st.warning(f"⚠️ You have already submitted a KRA for **{year} {quarter}**. You cannot submit another one for the same period.")
            st.info("If you need to make changes, please delete your existing entry from the 'My Previous KRAs' tab first.")
            can_submit = False
        
        with st.form("kra_form"):
            st.markdown("---")
            st.markdown("#### Technical Assessment")
            st.info("💡 You can add/edit rows in the table below. Fill your KPI, Target, Weightage, and Self-Assessment.")
            
            df_init = pd.DataFrame([
                {"KPI": "", "Target": "", "Weightage (%)": 0, "Self-Assessment": "", "Manager Assessment": ""}
            ])
            edited_df = st.data_editor(
                df_init, 
                num_rows="dynamic", 
                use_container_width=True, 
                key="tech_eval_editor",
                disabled=not can_submit,
                column_config={
                    "Manager Assessment": st.column_config.TextColumn(disabled=True)
                }
            )
            
            st.markdown("---")
            st.markdown("#### Behavioral Assessment (20%)")
            st.info("💡 Review the key performance indicators and targets below. Fill in your Self-Assessment.")
            
            behav_df_init = pd.DataFrame([
                {
                    "Key Performance Indicators": "Professional Communication", 
                    "Target": "• Share precise and well-structured updates in meetings and through written communication.\n• Ensure stakeholders are informed in advance about progress, risks, and concerns.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assessment": ""
                },
                {
                    "Key Performance Indicators": "Ownership & Accountability", 
                    "Target": "• Assume complete responsibility for assigned deliverables and honor committed timelines.\n• Identify potential risks early and communicate corrective actions proactively.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assessment": ""
                },
                {
                    "Key Performance Indicators": "Team Collaboration & Adaptability", 
                    "Target": "• Collaborate constructively with team members and other functions to achieve common goals.\n• Respond positively to priority changes while maintaining delivery standards.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assessment": ""
                },
                {
                    "Key Performance Indicators": "Professional Conduct & Learning Attitude", 
                    "Target": "• Consistently follow organizational guidelines, maintain discipline, and demonstrate professional behavior.\n• Enhance skills regularly and reflect the learning in day-to-day work.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assess": ""
                }
            ])

            # Custom Header for Behavioral Assessment
            h1, h2, h3, h4, h5 = st.columns([2, 3, 0.8, 3, 3])
            h1.markdown("<div style='font-weight:bold; color:#0d2d5e;'>KPI</div>", unsafe_allow_html=True)
            h2.markdown("<div style='font-weight:bold; color:#0d2d5e;'>Target</div>", unsafe_allow_html=True)
            h3.markdown("<div style='font-weight:bold; color:#0d2d5e;'>Weight</div>", unsafe_allow_html=True)
            h4.markdown("<div style='font-weight:bold; color:#0d2d5e;'>Self-Assessment</div>", unsafe_allow_html=True)
            h5.markdown("<div style='font-weight:bold; color:#0d2d5e;'>Manager Assessment</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0.5rem 0; border-top: 2px solid #0d2d5e;'>", unsafe_allow_html=True)

            behav_inputs = {}
            for i, item in enumerate(behav_df_init.to_dict('records')):
                c1, c2, c3, c4, c5 = st.columns([2, 3, 0.8, 3, 3])
                c1.markdown(f"**{item['Key Performance Indicators']}**")
                c2.markdown(f"<div style='font-size:0.9rem;'>{item['Target']}</div>", unsafe_allow_html=True)
                c3.write(item['Weight'])
                
                # Scientist input
                val = c4.text_area(
                    f"Self Assessment {i}", 
                    key=f"behav_self_{i}",
                    height=120,
                    label_visibility="collapsed",
                    placeholder="Describe your performance...",
                    disabled=not can_submit
                )
                behav_inputs[i] = val
                
                # Manager Read-only placeholder
                c5.info("Pending manager review")
                st.markdown("<hr style='margin:0.3rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Submit KRA for Assessment", type="primary", disabled=not can_submit)
            if submitted:
                with st.spinner("Submitting KRA..."):
                    # Build behav_data from the inputs captured above
                    behav_data = []
                    for i, item in enumerate(behav_df_init.to_dict('records')):
                        behav_data.append({
                            "Key Performance Indicators": item['Key Performance Indicators'],
                            "Target": item['Target'],
                            "Weight": item['Weight'],
                            "Self-Assessment": behav_inputs[i],
                            "Manager Assessment": ""
                        })
                    
                    tech_data = edited_df.to_dict('records')
                    submit_kra(email, year, quarter, "", "", "", tech_data, behav_data, get_or_create_sheet, safe_get_all_records, now_ist)
                st.success("KRA submitted successfully!")
                st.rerun()
                    
    with tab2:
        if not kras:
            st.info("No KRAs submitted yet.")
        else:
            for k in reversed(kras):
                status = str(k.get("status", "")).strip()
                status_color = "#f0a500" if status == "SUBMITTED" else "#3fb950"
                st.markdown(f"""
                <div style="background:white;padding:1.5rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:1rem;border-left:4px solid {status_color};">
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                        <span style="font-weight:600;color:#0d2d5e;font-size:1.1rem;">KRA: {k['year']} - {k['quarter']}</span>
                        <span style="background:{status_color};color:white;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:bold;">{status}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Delete option
                if st.button(f"🗑️ Delete {k['year']} {k['quarter']} KRA", key=f"del_{k['kra_id']}", type="secondary"):
                    with st.spinner("Deleting record..."):
                        delete_kra(k['kra_id'], get_or_create_sheet, safe_get_all_records)
                    st.success("KRA deleted successfully!")
                    st.rerun()
                
                # Always show tech assessment table if available
                if k.get("tech_assessment"):
                    try:
                        tech_list = json.loads(k["tech_assessment"])
                        if tech_list:
                            st.markdown("<div style='margin-bottom:8px;font-weight:600;color:#334155;font-size:0.95rem;'>Technical Assessment:</div>", unsafe_allow_html=True)
                            render_kra_table(st, tech_list, ["KPI", "Target", "Weightage (%)", "Self-Assessment", "Manager Assessment"])
                    except:
                        pass
                
                if k.get("behavioral_assessment"):
                    try:
                        behav_list = json.loads(k["behavioral_assessment"])
                        if behav_list:
                            st.markdown("<div style='margin-top:0.5rem;margin-bottom:8px;font-weight:600;color:#334155;font-size:0.95rem;'>Behavioral Assessment:</div>", unsafe_allow_html=True)
                            render_kra_table(st, behav_list, ["Key Performance Indicators", "Target", "Weight", "Self-Assessment", "Manager Assessment"])
                    except:
                        pass
                
                if status == "ASSESSED":
                    st.markdown(f"""
                    <div style="margin-top:1.5rem;padding:1.2rem;background:#f0f9ff;border-radius:8px;border:1px solid #bae6fd;">
                        <div style="color:#0369a1;font-weight:600;margin-bottom:0.5rem;display:flex;align-items:center;gap:8px;">
                            <span>🎯 Manager Assessment</span>
                            <span style="background:#0369a1;color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;">Rating: {k['rating']}/5</span>
                        </div>
                        <div style="color:#1e293b;font-size:0.95rem;line-height:1.5;">{k['assessment_notes']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

def page_hrms_db(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🏢 Employee Database</div>
        <div class="page-sub">Centralized directory of all company personnel</div>
    </div>
    """, unsafe_allow_html=True)
    
    profiles = all_hrms_profiles(get_or_create_sheet, safe_get_all_records)
    if not profiles:
        st.info("No employee profiles found.")
        return
        
    df = pd.DataFrame(profiles)
    
    # Filter: Only show profiles where personal info has been filled
    # We check if phone or present_address is not empty
    df = df[(df['phone'] != "") | (df['present_address'] != "")]
    
    if df.empty:
        st.info("No employees have completed their profiles yet.")
        return
    
    # Show more columns for HR/Management
    if session_state.role == "management" or session_state.email == "hr@morepenpdr.com":
        display_df = df[['full_name', 'email', 'department', 'designation', 'phone', 'emergency_contact', 'present_address', 'permanent_address', 'transport_required', 'health_issues', 'updated_at']].copy()
    else:
        display_df = df[['full_name', 'email', 'department', 'designation', 'phone', 'updated_at']].copy()
    
    search = st.text_input("🔍 Search Employees", placeholder="Name, Email, or Department...")
    if search:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        display_df = display_df[mask]
        
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def page_hrms_assess(st, session_state, get_or_create_sheet, safe_get_all_records, now_ist):
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📊 KRA Assessments</div>
        <div class="page-sub">Review and evaluate employee performance submissions</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

    kras = all_hrms_kras(get_or_create_sheet, safe_get_all_records)
    
    if not kras:
        st.info("No KRAs found in the database.")
        return
        
    profiles = all_hrms_profiles(get_or_create_sheet, safe_get_all_records)
    prof_map = {p["email"]: p for p in profiles}

    is_management = session_state.role == "management" or session_state.email == "hr@morepenpdr.com"
    
    # 1. Management Filter & Overview
    import datetime
    curr_year = str(datetime.datetime.now().year)
    year_options = ["2024", "2025", "2026", "2027"]
    try:
        curr_year_idx = year_options.index(curr_year)
    except:
        curr_year_idx = 1

    # Custom CSS for Colored Buttons in the Grid
    st.markdown("""
        <style>
        /* Target buttons by their text content */
        div[data-testid="stButton"] button p:contains("Pending") { color: black !important; font-weight: bold; }
        div[data-testid="stButton"] button:has(p:contains("Pending")) { background-color: #ffc000 !important; border: 1px solid #cc9900 !important; }
        
        div[data-testid="stButton"] button p:contains("Done") { color: black !important; font-weight: bold; }
        div[data-testid="stButton"] button:has(p:contains("Done")) { background-color: #92d050 !important; border: 1px solid #76a741 !important; }
        
        div[data-testid="stButton"] button p:contains("N/A") { color: white !important; }
        div[data-testid="stButton"] button:has(p:contains("N/A")) { background-color: #ff0000 !important; border: 1px solid #cc0000 !important; }
        </style>
    """, unsafe_allow_html=True)

    if is_management:
        st.markdown("### 🏢 Departmental Management")
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            selected_dept = st.selectbox("1. Select Department to View", ["All Departments"] + DEPARTMENTS)
        with col_m2:
            view_year = st.selectbox("2. Select Assessment Year", year_options, index=curr_year_idx)
            
        if selected_dept != "All Departments":
            # Show the Grid for selected department
            st.markdown(f"#### 📊 {selected_dept} - {view_year} KRA Completion Grid")
            dept_profiles = [p for p in profiles if p.get("department") == selected_dept]
            
            if not dept_profiles:
                st.info(f"No employee profiles found for {selected_dept}.")
            else:
                cycles = ["Q1", "Q2", "Q3", "Q4", "Half-Yearly", "Annual"]
                grid_rows = []
                for p in dept_profiles:
                    email = p["email"]
                    name = p.get("full_name", email)
                    row = {"Employee": name}
                    for cycle in cycles:
                        # Find KRA for this cycle and year (Robust matching)
                        kra = next((k for k in kras if str(k.get("email", "")).strip().lower() == email.strip().lower() 
                                    and str(k.get("year", "")).strip() == str(view_year).strip() 
                                    and str(k.get("quarter", "")).strip() == cycle.strip()), None)
                        status = "N/A"
                        if kra:
                            s = str(kra.get("status", "")).strip().upper()
                            status = "Done" if s == "ASSESSED" else "Pending"
                        row[cycle] = status
                    row["Email"] = email # Hidden but needed for logic
                    grid_rows.append(row)
                
                # Interactive Grid using st.columns and buttons
                st.info("👉 **Click on a 'Pending' or 'Done' box to open that KRA for assessment.**")
                
                # Header Row
                h_cols = st.columns([2.5, 1, 1, 1, 1, 1, 1])
                h_cols[0].markdown("**Employee**")
                for i, cycle in enumerate(cycles):
                    h_cols[i+1].markdown(f"**{cycle}**")
                
                st.markdown("<hr style='margin:0.2rem 0;'>", unsafe_allow_html=True)
                
                for r_idx, row in enumerate(grid_rows):
                    r_cols = st.columns([2.5, 1, 1, 1, 1, 1, 1])
                    r_cols[0].write(f"**{row['Employee']}**")
                    for i, cycle in enumerate(cycles):
                        status = row[cycle]
                        btn_key = f"grid_btn_{row['Email']}_{cycle}_{view_year}"
                        
                        if status == "Pending":
                            if r_cols[i+1].button("Pending", key=btn_key, use_container_width=True):
                                st.session_state["target_email"] = row["Email"]
                                st.session_state["target_year"] = view_year
                                st.session_state["target_quarter"] = cycle
                                st.rerun()
                        elif status == "Done":
                            if r_cols[i+1].button("Done", key=btn_key, use_container_width=True):
                                st.session_state["target_email"] = row["Email"]
                                st.session_state["target_year"] = view_year
                                st.session_state["target_quarter"] = cycle
                                st.rerun()
                        else:
                            r_cols[i+1].button("N/A", key=btn_key, use_container_width=True, disabled=True)
                
                st.markdown("---")
                
                # Hide the assessment section if no selection is made
                if "target_email" not in st.session_state or not st.session_state["target_email"]:
                    st.info("💡 **Select an employee's status in the grid above to start the assessment.**")
                    return # Exit early so tabs don't show
                else:
                    col_sel1, col_sel2 = st.columns([3, 1])
                    with col_sel1:
                        st.success(f"🎯 **Active Selection:** {prof_map.get(st.session_state['target_email'], {}).get('full_name', st.session_state['target_email'])} - {st.session_state['target_quarter']} ({st.session_state['target_year']})")
                    with col_sel2:
                        if st.button("❌ Clear Selection", use_container_width=True):
                            del st.session_state["target_email"]
                            st.rerun()
            
            # Filter the global lists for the tabs below
            dept_emails = [p["email"] for p in dept_profiles]
            kras = [k for k in kras if k["email"] in dept_emails]
        else:
            st.info("💡 Select a specific department above to view the KRA completion grid.")

    # Split KRAs for tabs
    pending = [k for k in kras if str(k.get("status", "")).strip().upper() == "SUBMITTED"]
    assessed = [k for k in kras if str(k.get("status", "")).strip().upper() == "ASSESSED"]
    
    tab1, tab2 = st.tabs([f"Pending Assessment ({len(pending)})", f"Assessment History ({len(assessed)})"])
    
    with tab1:
        if not pending:
            st.success("🎉 All pending KRAs have been assessed!")
        else:
            # 1. Select Employee
            pending_emails = sorted(list(set(k["email"] for k in pending)))
            
            def get_emp_label(email):
                p = prof_map.get(email, {})
                name = p.get("full_name", email)
                dept = p.get("department", "Unknown")
                return f"{name} ({dept})"

            # Default to target_email if jump feature used
            default_idx = 0
            if "target_email" in st.session_state and st.session_state["target_email"] in pending_emails:
                try:
                    default_idx = pending_emails.index(st.session_state["target_email"])
                except:
                    pass

            selected_email = st.selectbox("1. Select Employee", pending_emails, index=default_idx, format_func=get_emp_label)
            
            if selected_email:
                # 2. Select Year and Quarter for this employee
                emp_pending = [k for k in pending if k["email"] == selected_email]
                if not emp_pending:
                    st.info("No pending assessments for this employee.")
                else:
                    years = sorted(list(set(str(k["year"]) for k in emp_pending)), reverse=True)
                    
                    # Default Year from Jump
                    y_idx = 0
                    if "target_year" in st.session_state and str(st.session_state["target_year"]) in years:
                        y_idx = years.index(str(st.session_state["target_year"]))
                    
                    selected_year = st.selectbox("2. Select Year", years, index=y_idx, key=f"yr_{selected_email}")
                    
                    available_quarters = sorted(list(set(k["quarter"] for k in emp_pending if str(k["year"]) == str(selected_year))))
                    
                    # Default Quarter from Jump
                    q_idx = 0
                    if "target_quarter" in st.session_state and st.session_state["target_quarter"] in available_quarters:
                        q_idx = available_quarters.index(st.session_state["target_quarter"])
                        
                    selected_quarter = st.selectbox("3. Select Quarter", available_quarters, index=q_idx, key=f"qtr_{selected_email}")
                
                # 3. Find the specific KRA (Pick latest if duplicates exist)
                emp_pending_sorted = sorted(emp_pending, key=lambda x: x.get("submitted_at", ""), reverse=True)
                k = next((k for k in emp_pending_sorted if str(k["year"]) == str(selected_year) and str(k["quarter"]) == str(selected_quarter)), None)
                
                if k:
                    st.markdown("---")
                    with st.form(f"assess_form_{k['kra_id']}"):
                        st.markdown(f"#### Evaluation for {get_emp_label(selected_email)} - {selected_year} {selected_quarter}")
                        
                        # Technical Assessment
                        st.markdown("##### Technical Assessment")
                        try:
                            tech_list = json.loads(k.get("tech_assessment", "[]"))
                        except:
                            tech_list = []
                        
                        if tech_list:
                            df_tech = pd.DataFrame(tech_list)
                            edited_tech_df = st.data_editor(
                                df_tech, 
                                num_rows="fixed", 
                                use_container_width=True, 
                                key=f"tech_edit_{k['kra_id']}",
                                column_config={
                                    "KPI": st.column_config.TextColumn(disabled=True),
                                    "Target": st.column_config.TextColumn(disabled=True),
                                    "Weightage (%)": st.column_config.NumberColumn(disabled=True),
                                    "Self-Assessment": st.column_config.TextColumn(disabled=True),
                                    "Manager Assessment": st.column_config.TextColumn("Manager Assessment", help="Provide your evaluation")
                                }
                            )
                        else:
                            st.warning("No technical assessment data found.")
                            edited_tech_df = pd.DataFrame()
                        
                        # Behavioral Assessment
                        st.markdown("##### Behavioral Assessment")
                        try:
                            behav_val = k.get("behavioral_assessment", "[]")
                            behav_list = json.loads(behav_val) if behav_val and behav_val != "" else []
                        except:
                            behav_list = []
                        
                        if not behav_list:
                            # Fallback template for legacy KRAs or if not provided
                            behav_list = [
                                {
                                    "Key Performance Indicators": "Professional Communication", 
                                    "Target": "• Share precise and well-structured updates in meetings and through written communication.\n• Ensure stakeholders are informed in advance about progress, risks, and concerns.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "Not Provided", 
                                    "Manager Assessment": ""
                                },
                                {
                                    "Key Performance Indicators": "Ownership & Accountability", 
                                    "Target": "• Assume complete responsibility for assigned deliverables and honor committed timelines.\n• Identify potential risks early and communicate corrective actions proactively.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "Not Provided", 
                                    "Manager Assessment": ""
                                },
                                {
                                    "Key Performance Indicators": "Team Collaboration & Adaptability", 
                                    "Target": "• Collaborate constructively with team members and other functions to achieve common goals.\n• Respond positively to priority changes while maintaining delivery standards.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "Not Provided", 
                                    "Manager Assessment": ""
                                },
                                {
                                    "Key Performance Indicators": "Professional Conduct & Learning Attitude", 
                                    "Target": "• Consistently follow organizational guidelines, maintain discipline, and demonstrate professional behavior.\n• Enhance skills regularly and reflect the learning in day-to-day work.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "Not Provided", 
                                    "Manager Assessment": ""
                                }
                            ]

                        # Custom Header for Manager Assessment
                        h1, h2, h3, h4, h5 = st.columns([2, 3, 0.8, 3, 3])
                        h1.markdown("**KPI**")
                        h2.markdown("**Target**")
                        h3.markdown("**Weight**")
                        h4.markdown("**Self-Assessment**")
                        h5.markdown("**Manager Assessment**")
                        st.markdown("<hr style='margin:0.5rem 0; border-top: 2px solid #0d2d5e;'>", unsafe_allow_html=True)

                        edited_behav_list = []
                        for i, item in enumerate(behav_list):
                            c1, c2, c3, c4, c5 = st.columns([2, 3, 0.8, 3, 3])
                            c1.markdown(f"**{item['Key Performance Indicators']}**")
                            c2.markdown(f"<div style='font-size:0.9rem;'>{item['Target']}</div>", unsafe_allow_html=True)
                            c3.write(item['Weight'])
                            c4.info(item.get('Self-Assessment', 'N/A'))
                            
                            mgr_val = c5.text_area(
                                f"Manager Assessment for {item['Key Performance Indicators']}",
                                value=item.get('Manager Assessment', ''),
                                key=f"behav_mgr_{k['kra_id']}_{i}",
                                height=120,
                                label_visibility="collapsed"
                            )
                            
                            edited_behav_list.append({**item, "Manager Assessment": mgr_val})
                            st.markdown("<hr style='margin:0.3rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
                        
                        behav_data = edited_behav_list
                        
                        st.markdown("---")
                        notes = st.text_area("General Assessment Notes / Feedback")
                        rating = st.slider("Overall Rating (1-5)", 1, 5, 3)
                        
                        st.markdown("---")
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.form_submit_button("✅ Finalize Assessment", type="primary"):
                                with st.spinner("Saving assessment..."):
                                    tech_data = edited_tech_df.to_dict('records') if not edited_tech_df.empty else []
                                    assess_kra(k['kra_id'], notes, rating, tech_data, behav_data, get_or_create_sheet, safe_get_all_records, now_ist)
                                    st.success("Assessment saved!")
                                    st.rerun()
                        with col_btn2:
                            if st.button(f"🗑️ Delete Submission", key=f"btn_del_{k['kra_id']}", use_container_width=True, type="secondary"):
                                try:
                                    ws = get_or_create_sheet("hrms_kras", [])
                                    records = safe_get_all_records(ws)
                                    row_idx = -1
                                    for i, r in enumerate(records):
                                        if str(r.get("kra_id")) == str(k["kra_id"]):
                                            row_idx = i + 2 # +1 for header, +1 for 0-index
                                            break
                                    if row_idx != -1:
                                        ws.delete_rows(row_idx)
                                        st.warning("🗑️ KRA Submission deleted.")
                                        st.rerun()
                                    else:
                                        st.error("Could not find record to delete.")
                                except Exception as e:
                                    st.error(f"Error deleting record: {e}")

    with tab2:
        if not assessed:
            st.info("No assessed KRAs.")
        else:
            # Filtering and selection for history
            assessed_emails = sorted(list(set(k["email"] for k in assessed)))
            
            default_h_idx = 0
            if "target_email" in st.session_state and st.session_state["target_email"] in assessed_emails:
                try:
                    default_h_idx = assessed_emails.index(st.session_state["target_email"])
                except:
                    pass

            h_email = st.selectbox("1. Select Employee (History)", assessed_emails, index=default_h_idx, format_func=get_emp_label, key="h_email")
            
            emp_assessed = [k for k in assessed if k["email"] == h_email]
            h_years = sorted(list(set(str(k["year"]) for k in emp_assessed)), reverse=True)
            
            y_h_idx = 0
            if "target_year" in st.session_state and str(st.session_state["target_year"]) in h_years:
                y_h_idx = h_years.index(str(st.session_state["target_year"]))

            h_year = st.selectbox("2. Select Year", h_years, index=y_h_idx, key=f"h_yr_{h_email}")
            
            h_quarters = sorted(list(set(k["quarter"] for k in emp_assessed if str(k["year"]) == str(h_year))))
            
            q_h_idx = 0
            if "target_quarter" in st.session_state and st.session_state["target_quarter"] in h_quarters:
                q_h_idx = h_quarters.index(st.session_state["target_quarter"])

            h_quarter = st.selectbox("3. Select Quarter", h_quarters, index=q_h_idx, key=f"h_qtr_{h_email}")
            
            k = next((k for k in emp_assessed if str(k["year"]) == str(h_year) and k["quarter"] == h_quarter), None)
            
            if k:
                st.markdown(f"### 📋 Assessment Record: {h_quarter} {h_year}")
                # Render history details...
                
                st.markdown(f"""
                <div style="background:white;padding:1.5rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:1rem;border-left:4px solid #3fb950;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                        <span style="font-weight:600;color:#0d2d5e;font-size:1.1rem;">{name} ({dept}) - {k['year']} {k['quarter']}</span>
                        <span style="color:#3fb950;font-weight:bold;">Rating: {k['rating']}/5</span>
                    </div>
                    <div style="margin-bottom:0.8rem;"><strong>Assessment Notes:</strong><br>{k['assessment_notes']}</div>
                """, unsafe_allow_html=True)
                
                if k.get("tech_assessment"):
                    try:
                        tech_list = json.loads(k["tech_assessment"])
                        if tech_list:
                            st.markdown("<strong>Technical Assessment:</strong>", unsafe_allow_html=True)
                            st.dataframe(pd.DataFrame(tech_list), use_container_width=True, hide_index=True)
                    except:
                        pass
                
                if k.get("behavioral_assessment"):
                    try:
                        behav_list = json.loads(k["behavioral_assessment"])
                        if behav_list:
                            st.markdown("<strong>Behavioral Assessment:</strong>", unsafe_allow_html=True)
                            st.dataframe(pd.DataFrame(behav_list), use_container_width=True, hide_index=True)
                    except:
                        pass
                
                st.markdown("</div>", unsafe_allow_html=True)
