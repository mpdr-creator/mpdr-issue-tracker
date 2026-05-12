import uuid
import json
import pandas as pd

# HRMS Database schema operations
def all_hrms_profiles(get_or_create_sheet, safe_get_all_records):
    try:
        # Fetch HRMS profiles
        p_ws = get_or_create_sheet("hrms_profiles", ["email", "full_name", "designation", "department", "phone", "emergency_contact", "present_address", "permanent_address", "transport_required", "health_issues", "updated_at"])
        profiles = safe_get_all_records(p_ws)
        
        # Fetch User registration data for fallbacks - using 'dept' to match app.py
        u_ws = get_or_create_sheet("users", ["email", "password", "role", "dept", "created_at"])
        users = safe_get_all_records(u_ws)
        
        # Create a merged map
        merged = {u["email"]: {
            "email": u["email"],
            "full_name": u["email"].split('@')[0].replace('.', ' ').title(),
            "department": u.get("dept", "Unknown Dept"),
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

def submit_kra(email, year, quarter, objectives, achievements, challenges, tech_assessment, behavioral_assessment, get_or_create_sheet, safe_get_all_records, now_ist):
    ws = get_or_create_sheet("hrms_kras", ["kra_id", "email", "year", "quarter", "objectives", "achievements", "challenges", "tech_assessment", "status", "submitted_at", "assessed_at", "assessment_notes", "rating", "behavioral_assessment"])
    kra_id = str(uuid.uuid4())[:8].upper()
    now = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    tech_json = json.dumps(tech_assessment)
    behav_json = json.dumps(behavioral_assessment)
    ws.append_row([kra_id, email, year, quarter, objectives, achievements, challenges, tech_json, "SUBMITTED", now, "", "", "", behav_json])

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
            
            # Department Dropdown as requested
            DEPARTMENTS = ["Admin", "CADD", "MedChem", "API", "AR&D", "CDMO", "SSD"]
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
        with st.form("kra_form"):
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox("Year", ["2024", "2025", "2026"])
            with col2:
                quarter = st.selectbox("Quarter / Cycle", ["Q1", "Q2", "Q3", "Q4", "Annual"])
                
            
            st.markdown("---")
            st.markdown("#### Technical Assessment")
            st.info("💡 You can add/edit rows in the table below. Fill your KPI, Target, Weightage, and Self-Assessment.")
            
            df_init = pd.DataFrame([
                {"KPI": "", "SMART Target": "", "Weightage (%)": 0, "Self-Assessment": "", "Manager Assess": ""}
            ])
            edited_df = st.data_editor(
                df_init, 
                num_rows="dynamic", 
                use_container_width=True, 
                key="tech_eval_editor",
                column_config={
                    "Manager Assess": st.column_config.TextColumn(disabled=True)
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
                    "Manager Assess": ""
                },
                {
                    "Key Performance Indicators": "Ownership & Accountability", 
                    "Target": "• Assume complete responsibility for assigned deliverables and honor committed timelines.\n• Identify potential risks early and communicate corrective actions proactively.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assess": ""
                },
                {
                    "Key Performance Indicators": "Team Collaboration & Adaptability", 
                    "Target": "• Collaborate constructively with team members and other functions to achieve common goals.\n• Respond positively to priority changes while maintaining delivery standards.", 
                    "Weight": "5%", 
                    "Self-Assessment": "", 
                    "Manager Assess": ""
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

            behav_data = []
            for i, item in enumerate(behav_df_init.to_dict('records')):
                c1, c2, c3, c4, c5 = st.columns([2, 3, 0.8, 3, 3])
                c1.markdown(f"**{item['Key Performance Indicators']}**")
                c2.markdown(f"<div style='font-size:0.9rem;'>{item['Target']}</div>", unsafe_allow_html=True)
                c3.write(item['Weight'])
                
                # Scientist input
                self_val = c4.text_area(
                    f"Self Assessment {i}", 
                    key=f"behav_self_{i}",
                    height=120,
                    label_visibility="collapsed",
                    placeholder="Describe your performance..."
                )
                
                # Manager Read-only placeholder
                c5.info("Pending manager review")
                
                behav_data.append({
                    "Key Performance Indicators": item['Key Performance Indicators'],
                    "Target": item['Target'],
                    "Weight": item['Weight'],
                    "Self-Assessment": self_val,
                    "Manager Assess": ""
                })
                st.markdown("<hr style='margin:0.3rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Submit KRA for Assessment", type="primary")
            if submitted:
                with st.spinner("Submitting KRA..."):
                    tech_data = edited_df.to_dict('records')
                    # Pass empty strings for removed fields
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
                
                # Always show tech assessment table if available
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

    # Robust filtering: strip spaces and convert to upper case
    pending = [k for k in kras if str(k.get("status", "")).strip().upper() == "SUBMITTED"]
    assessed = [k for k in kras if str(k.get("status", "")).strip().upper() == "ASSESSED"]
    
    tab1, tab2 = st.tabs([f"Pending Assessment ({len(pending)})", f"Assessed ({len(assessed)})"])
    
    with tab1:
        if not pending:
            st.info("No KRAs are currently pending assessment.")
        else:
            for k in pending:
                p = prof_map.get(k["email"], {})
                name = p.get("full_name", k["email"])
                dept = p.get("department", "Unknown Dept")
                
                with st.expander(f"KRA: {name} ({dept}) | {k['year']} {k['quarter']}"):
                    with st.form(f"assess_form_{k['kra_id']}"):
                        st.markdown("#### Technical Assessment")
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
                                    "SMART Target": st.column_config.TextColumn(disabled=True),
                                    "Weightage (%)": st.column_config.NumberColumn(disabled=True),
                                    "Self-Assessment": st.column_config.TextColumn(disabled=True),
                                    "Manager Assess": st.column_config.TextColumn("Manager Assess", help="Provide your evaluation")
                                }
                            )
                        else:
                            st.warning("No technical assessment data found.")
                            edited_tech_df = pd.DataFrame()
                        
                        st.markdown("#### Behavioral Assessment")
                        try:
                            behav_val = k.get("behavioral_assessment", "[]")
                            behav_list = json.loads(behav_val) if behav_val and behav_val != "" else []
                        except:
                            behav_list = []
                        
                        # If no behavioral data (old KRA), provide the template
                        if not behav_list:
                            behav_list = [
                                {
                                    "Key Performance Indicators": "Professional Communication", 
                                    "Target": "• Share precise and well-structured updates in meetings and through written communication.\n• Ensure stakeholders are informed in advance about progress, risks, and concerns.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "N/A (Old KRA)", 
                                    "Manager Assess": ""
                                },
                                {
                                    "Key Performance Indicators": "Ownership & Accountability", 
                                    "Target": "• Assume complete responsibility for assigned deliverables and honor committed timelines.\n• Identify potential risks early and communicate corrective actions proactively.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "N/A (Old KRA)", 
                                    "Manager Assess": ""
                                },
                                {
                                    "Key Performance Indicators": "Team Collaboration & Adaptability", 
                                    "Target": "• Collaborate constructively with team members and other functions to achieve common goals.\n• Respond positively to priority changes while maintaining delivery standards.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "N/A (Old KRA)", 
                                    "Manager Assess": ""
                                },
                                {
                                    "Key Performance Indicators": "Professional Conduct & Learning Attitude", 
                                    "Target": "• Consistently follow organizational guidelines, maintain discipline, and demonstrate professional behavior.\n• Enhance skills regularly and reflect the learning in day-to-day work.", 
                                    "Weight": "5%", 
                                    "Self-Assessment": "N/A (Old KRA)", 
                                    "Manager Assess": ""
                                }
                            ]
                        
                        # Custom Header for Manager Assessment
                        h1, h2, h3, h4, h5 = st.columns([2, 3, 1, 3, 3])
                        h1.markdown("**KPI**")
                        h2.markdown("**Target**")
                        h3.markdown("**Weight**")
                        h4.markdown("**Self-Assessment**")
                        h5.markdown("**Manager Assess**")
                        st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

                        edited_behav_list = []
                        for i, item in enumerate(behav_list):
                            c1, c2, c3, c4, c5 = st.columns([2, 3, 1, 3, 3])
                            c1.markdown(f"**{item['Key Performance Indicators']}**")
                            c2.markdown(item['Target'])
                            c3.write(item['Weight'])
                            c4.info(item.get('Self-Assessment', 'N/A'))
                            
                            # Manager input
                            mgr_val = c5.text_area(
                                f"Manager Assess for {item['Key Performance Indicators']}",
                                value=item.get('Manager Assess', ''),
                                key=f"behav_mgr_{k['kra_id']}_{i}",
                                height=100,
                                label_visibility="collapsed"
                            )
                            
                            edited_behav_list.append({
                                **item,
                                "Manager Assess": mgr_val
                            })
                        behav_data = edited_behav_list
                        
                        st.markdown("---")
                        notes = st.text_area("General Assessment Notes / Feedback")
                        rating = st.slider("Overall Rating (1-5)", 1, 5, 3)
                        
                        if st.form_submit_button("Submit Assessment", type="primary"):
                            with st.spinner("Saving assessment..."):
                                tech_data = edited_tech_df.to_dict('records') if not edited_tech_df.empty else []
                                # behav_data already prepared in loop
                                assess_kra(k['kra_id'], notes, rating, tech_data, behav_data, get_or_create_sheet, safe_get_all_records, now_ist)
                            st.success("Assessment saved!")
                            st.rerun()
                            
    with tab2:
        if not assessed:
            st.info("No assessed KRAs.")
        else:
            for k in reversed(assessed):
                p = prof_map.get(k["email"], {})
                name = p.get("full_name", k["email"])
                dept = p.get("department", "Unknown Dept")
                
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
