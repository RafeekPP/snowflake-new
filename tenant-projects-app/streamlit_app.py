import os
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

st.title("User Access Details")

request_type = st.radio("Request Type", ["Generic Access Request :[ DOP/ETL/RPT ]", "Specific Database Object Access", "AI Users Roles"], horizontal=True)

st.markdown("""
<style>
    .stTextInput, .stSelectbox, .stRadio, .stCheckbox, .stMultiSelect {
        max-width: 100%;
    }
    .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    [data-testid="stFormSubmitButton"], .stTextInput, .stSelectbox {
        text-align: left;
    }
    .stApp {
        background: linear-gradient(135deg, #e8f4f8 0%, #d4e9f7 50%, #c8dff0 100%);
    }
    .stApp > header {
        background-color: transparent;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #d4e9f7 0%, #b8d4e8 100%);
    }
    h1 {
        color: #1b4965 !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: 0.5px;
    }
    h2, h3, [data-testid="stSubheader"] {
        color: #1b4965 !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
        border-bottom: 2px solid #2c6e8a;
        padding-bottom: 0.3rem;
        letter-spacing: 0.3px;
    }
    .stRadio > label, .stCheckbox > label, .stSelectbox > label, .stTextInput > label {
        color: #1a3a4a !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] strong {
        color: #1a3a4a !important;
        font-weight: 600 !important;
    }
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stRadio [role="radiogroup"] label {
        font-size: 0.9rem !important;
        min-height: 38px !important;
        padding: 6px 12px !important;
    }
    .stTextInput input {
        border: 1px solid #2c6e8a;
        border-radius: 8px;
    }
    .stSelectbox [data-baseweb="select"] {
        border-radius: 8px;
    }
    .stRadio [role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.6);
        border: 1px solid #2c6e8a;
        border-radius: 8px;
        color: #1a3a4a;
    }
    .stCheckbox [data-testid="stCheckbox"] {
        background-color: rgba(255, 255, 255, 0.4);
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 0.9rem !important;
    }
    button[kind="secondary"], button[kind="primary"] {
        font-size: 0.9rem !important;
        min-height: 38px !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
    }
    [data-testid="stSelectbox"] label, [data-testid="stTextInput"] label {
        color: #1b4965 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    df = conn.query("SELECT TENANT, SUBTENANT, PROJECT FROM META_DATA_DB.TABLES_SCHEMA.TENANT_PROJECTS")
    return df

df = load_data()

def clear_form_state(prefixes):
    """Clear all session state keys that start with any of the given prefixes."""
    keys_to_clear = []
    for key in list(st.session_state.keys()):
        for prefix in prefixes:
            if key.startswith(prefix):
                keys_to_clear.append(key)
                break
    for key in keys_to_clear:
        del st.session_state[key]

# Reset counters to force fresh widget keys after submit
if "generic_reset" not in st.session_state:
    st.session_state["generic_reset"] = 0
if "sdo_reset" not in st.session_state:
    st.session_state["sdo_reset"] = 0
if "show_success" not in st.session_state:
    st.session_state["show_success"] = False

# Show success message from previous submit, then clear it
if st.session_state["show_success"]:
    st.success("Details submitted successfully")
    st.session_state["show_success"] = False

if request_type == "Generic Access Request :[ DOP/ETL/RPT ]":
    mirrored_access = st.radio("Mirrored access of existing user", ["Yes", "No"], index=None, horizontal=True, key=f"generic_mirrored_{st.session_state['generic_reset']}")
    if mirrored_access == "Yes":
        mirror_username = st.text_input("Provide the username to be mirrored")
    elif mirrored_access == "No":
        tenants = sorted(df["TENANT"].unique()) + ["New"]
        selected_subtenant = None
        selected_project = None

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_tenant = st.selectbox("Tenants", tenants)

        if selected_tenant == "New":
            tenant_name = st.text_input("Enter Tenant Name")
            subtenant_name = st.text_input("Enter Subtenant Name")
            project_name = st.text_input("Enter Project Name")
            schema_name = st.text_input("Schemas to be created")
            if tenant_name and subtenant_name and project_name:
                st.success(f"Selected: {tenant_name} → {subtenant_name} → {project_name}")
        else:
            filtered_by_tenant = df[df["TENANT"] == selected_tenant]
            subtenants = sorted(filtered_by_tenant["SUBTENANT"].unique()) + ["New"]
            with col2:
                selected_subtenant = st.selectbox("Subtenants", subtenants)

            if selected_subtenant == "New":
                subtenant_name = st.text_input("Enter Subtenant Name")
                project_name = st.text_input("Enter Project Name")
                schema_name = st.text_input("Schemas to be created")
                if subtenant_name and project_name:
                    st.success(f"Selected: {selected_tenant} → {subtenant_name} → {project_name}")
            else:
                filtered_by_subtenant = filtered_by_tenant[filtered_by_tenant["SUBTENANT"] == selected_subtenant]
                projects = sorted(filtered_by_subtenant["PROJECT"].unique()) + ["New"]
                with col3:
                    selected_project = st.selectbox("Projects", projects)

                if selected_project == "New":
                    project_name = st.text_input("Enter Project Name")
                    schema_name = st.text_input("Schemas to be created")
                    if project_name:
                        st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {project_name}")
                else:
                    st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {selected_project}")

        st.subheader("Environments to which access is needed")

        gr = st.session_state["generic_reset"]
        env_options = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]
        selected_envs = []
        env_cols = st.columns(len(env_options))
        for idx, (env_label, env_code) in enumerate(env_options):
            with env_cols[idx]:
                if st.checkbox(env_label, key=f"env_{env_code}_{gr}"):
                    selected_envs.append((env_label, env_code))

        # For each selected environment, show DOP/ETL/RPT user inputs
        for env_label, env_code in selected_envs:
            st.markdown(f"---")
            num_dop = st.selectbox(f"Number of users needed access [{env_label}-DOP Role]", list(range(0, 11)), key=f"num_dop_{env_code}_{gr}")
            for i in range(1, num_dop + 1):
                st.text_input(f"{env_label}-DOP User-{i} Email", key=f"dop_user_email_{env_code}_{i}_{gr}")

            num_etl = st.selectbox(f"Number of users needed access [{env_label}-ETL Role]", list(range(0, 11)), key=f"num_etl_{env_code}_{gr}")
            for i in range(1, num_etl + 1):
                st.text_input(f"{env_label}-ETL User-{i} Email", key=f"etl_user_email_{env_code}_{i}_{gr}")

            num_rpt = st.selectbox(f"Number of users needed access [{env_label}-RPT Role]", list(range(0, 11)), key=f"num_rpt_{env_code}_{gr}")
            for i in range(1, num_rpt + 1):
                st.text_input(f"{env_label}-RPT User-{i} Email", key=f"rpt_user_email_{env_code}_{i}_{gr}")

        if st.button("Submit", key="generic_submit"):
            # Validation: check all required fields
            validation_errors = []

            # Check at least one environment is selected
            if not selected_envs:
                validation_errors.append("At least one environment must be selected.")

            # Check all user email fields are filled
            for env_label, env_code in selected_envs:
                num_dop = st.session_state.get(f"num_dop_{env_code}_{gr}", 0)
                for i in range(1, num_dop + 1):
                    email = st.session_state.get(f"dop_user_email_{env_code}_{i}_{gr}", "")
                    if not email:
                        validation_errors.append(f"{env_label}-DOP User-{i} Email is empty.")
                num_etl = st.session_state.get(f"num_etl_{env_code}_{gr}", 0)
                for i in range(1, num_etl + 1):
                    email = st.session_state.get(f"etl_user_email_{env_code}_{i}_{gr}", "")
                    if not email:
                        validation_errors.append(f"{env_label}-ETL User-{i} Email is empty.")
                num_rpt = st.session_state.get(f"num_rpt_{env_code}_{gr}", 0)
                for i in range(1, num_rpt + 1):
                    email = st.session_state.get(f"rpt_user_email_{env_code}_{i}_{gr}", "")
                    if not email:
                        validation_errors.append(f"{env_label}-RPT User-{i} Email is empty.")

            # Check at least one user count > 0
            has_users = False
            for env_label, env_code in selected_envs:
                if (st.session_state.get(f"num_dop_{env_code}_{gr}", 0) > 0 or
                    st.session_state.get(f"num_etl_{env_code}_{gr}", 0) > 0 or
                    st.session_state.get(f"num_rpt_{env_code}_{gr}", 0) > 0):
                    has_users = True
                    break
            if not has_users and selected_envs:
                validation_errors.append("At least one user must be specified.")

            if validation_errors:
                st.error("Please enter all details")
            else:
                # Determine tenant/subtenant/project values
                if selected_tenant == "New":
                    t_val = st.session_state.get("tenant_name", tenant_name if 'tenant_name' in dir() else None)
                    s_val = st.session_state.get("subtenant_name", subtenant_name if 'subtenant_name' in dir() else None)
                    p_val = st.session_state.get("project_name", project_name if 'project_name' in dir() else None)
                elif selected_subtenant == "New":
                    t_val = selected_tenant
                    s_val = st.session_state.get("subtenant_name", subtenant_name if 'subtenant_name' in dir() else None)
                    p_val = st.session_state.get("project_name", project_name if 'project_name' in dir() else None)
                elif selected_project == "New":
                    t_val = selected_tenant
                    s_val = selected_subtenant
                    p_val = st.session_state.get("project_name", project_name if 'project_name' in dir() else None)
                else:
                    t_val = selected_tenant
                    s_val = selected_subtenant
                    p_val = selected_project

                # Collect all users per environment and role type
                users_to_insert = []
                for env_label, env_code in selected_envs:
                    num_dop = st.session_state.get(f"num_dop_{env_code}_{gr}", 0)
                    for i in range(1, num_dop + 1):
                        email = st.session_state.get(f"dop_user_email_{env_code}_{i}_{gr}", "")
                        if email:
                            users_to_insert.append((email, f"{env_label}-DOP Role", env_label))
                    num_etl = st.session_state.get(f"num_etl_{env_code}_{gr}", 0)
                    for i in range(1, num_etl + 1):
                        email = st.session_state.get(f"etl_user_email_{env_code}_{i}_{gr}", "")
                        if email:
                            users_to_insert.append((email, f"{env_label}-ETL Role", env_label))
                    num_rpt = st.session_state.get(f"num_rpt_{env_code}_{gr}", 0)
                    for i in range(1, num_rpt + 1):
                        email = st.session_state.get(f"rpt_user_email_{env_code}_{i}_{gr}", "")
                        if email:
                            users_to_insert.append((email, f"{env_label}-RPT Role", env_label))

                if users_to_insert:
                    insert_count = 0
                    session = conn.session()
                    for user_email, role_type, env_label in users_to_insert:
                        session.sql(
                            f"""INSERT INTO META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST
                                (TENANT, SUBTENANT, PROJECT, REQUEST_TYPE, "USER", ENVIRONMENT, SCHEMA, OBJECTS, OBJECT_NAMES)
                                VALUES ('{t_val}', '{s_val}', '{p_val}', '{role_type}', '{user_email}', '{env_label}', NULL, NULL, NULL)"""
                        ).collect()
                        insert_count += 1
                    st.session_state["show_success"] = True
                    st.session_state["generic_reset"] += 1
                    st.rerun()

        if st.button("Display", key="generic_display"):
            display_df = conn.query("SELECT * FROM META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST")
            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No records found in ACCESS_REQUEST table.")

elif request_type == "Specific Database Object Access":
    mirrored_access_sdo = st.radio("Mirrored access of existing user", ["Yes", "No"], index=None, horizontal=True, key=f"sdo_mirrored_{st.session_state['sdo_reset']}")
    if mirrored_access_sdo == "Yes":
        mirror_username_sdo = st.text_input("Provide the username to be mirrored", key="sdo_mirror_username")
    elif mirrored_access_sdo == "No":
        tenants = sorted(df["TENANT"].unique())
        selected_subtenant = None
        selected_project = None

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_tenant = st.selectbox("Tenants", tenants, key="sdo_tenant")

        filtered_by_tenant = df[df["TENANT"] == selected_tenant]
        subtenants = sorted(filtered_by_tenant["SUBTENANT"].unique())
        with col2:
            selected_subtenant = st.selectbox("Subtenants", subtenants, key="sdo_subtenant")

        filtered_by_subtenant = filtered_by_tenant[filtered_by_tenant["SUBTENANT"] == selected_subtenant]
        projects = sorted(filtered_by_subtenant["PROJECT"].unique())
        with col3:
            selected_project = st.selectbox("Projects", projects, key="sdo_project")

        import re
        tenant_abbr = re.search(r'\[(.+?)\]', selected_tenant)
        subtenant_abbr = re.search(r'\[(.+?)\]', selected_subtenant)
        tenant_code = tenant_abbr.group(1) if tenant_abbr else selected_tenant
        subtenant_code = subtenant_abbr.group(1) if subtenant_abbr else selected_subtenant

        if "selected_schemas_sdo" not in st.session_state or not isinstance(st.session_state.selected_schemas_sdo, dict):
            st.session_state.selected_schemas_sdo = {}

        access_mode = st.radio("Access Mode", ["All Users need same access", "Users need different access"], index=None, horizontal=True, key=f"sdo_access_mode_{st.session_state['sdo_reset']}")

        sr = st.session_state["sdo_reset"]
        environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]
        selected_envs = []

        if access_mode == "All Users need same access":
            st.subheader("Environment to which access is needed")

            selected_envs = []
            env_cols = st.columns(len(environments))
            for idx, (env_label, env_code) in enumerate(environments):
                with env_cols[idx]:
                    env_checked = st.checkbox(env_label, key=f"sdo_env_{env_code}_{sr}")
                if env_checked:
                    selected_envs.append((env_label, env_code))

            if selected_envs:
                role_combinations = ["Read", "Read/Write", "Read/Write/Create"]
                selected_role = st.radio("Select role", role_combinations, index=None, horizontal=True, key=f"sdo_role_select_{sr}")
                num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key=f"sdo_num_users_{sr}")
                for i in range(1, num_users + 1):
                    st.text_input(f"User-{i} Email", key=f"sdo_user_email_{i}_{sr}")

                st.subheader("Select Object Types")
                obj_col1, obj_col2, obj_col3, obj_col4, obj_col5 = st.columns(5)
                with obj_col1:
                    obj_tables = st.checkbox("Tables", key=f"sdo_objtype_Tables_{sr}")
                with obj_col2:
                    obj_functions = st.checkbox("Functions", key=f"sdo_objtype_Functions_{sr}")
                with obj_col3:
                    obj_procedures = st.checkbox("Procedures", key=f"sdo_objtype_Procedures_{sr}")
                with obj_col4:
                    obj_views = st.checkbox("Views", key=f"sdo_objtype_Views_{sr}")
                with obj_col5:
                    obj_stages = st.checkbox("Stages", key=f"sdo_objtype_Stages_{sr}")

                obj_selections = {
                    "Tables": obj_tables,
                    "Functions": obj_functions,
                    "Procedures": obj_procedures,
                    "Views": obj_views,
                    "Stages": obj_stages,
                }
                selected_obj_types = [ot for ot, oc in obj_selections.items() if oc]

                if selected_obj_types:
                    for env_label, env_code in selected_envs:
                        db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                        try:
                            schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                            if not schema_df.empty:
                                schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                            else:
                                schema_list = []
                                st.info(f"No schemas found in {db_name}")
                        except Exception as e:
                            schema_list = []
                            st.warning(f"Could not fetch schemas from {db_name}: {e}")

                        if schema_list:
                            st.write(f"**Schema List ({env_label})**")
                            for schema in schema_list:
                                schema_checked = st.checkbox(schema, key=f"sdo_schema_{env_code}_{schema}_{sr}")
                                if schema_checked:
                                    # Show objects indented to the right
                                    _, obj_col = st.columns([0.5, 9.5])
                                    with obj_col:
                                        for obj_type in selected_obj_types:
                                            if obj_type == "Tables":
                                                query = f"SELECT TABLE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema.split('.')[1]}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                            elif obj_type == "Views":
                                                query = f"SELECT TABLE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema.split('.')[1]}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                            elif obj_type == "Functions":
                                                query = f"SELECT FUNCTION_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{schema.split('.')[1]}' ORDER BY FUNCTION_NAME"
                                            elif obj_type == "Procedures":
                                                query = f"SELECT PROCEDURE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{schema.split('.')[1]}' ORDER BY PROCEDURE_NAME"
                                            elif obj_type == "Stages":
                                                query = f"SHOW STAGES IN {schema}"

                                            try:
                                                if obj_type == "Stages":
                                                    obj_df = conn.query(query)
                                                    obj_names = obj_df["name"].tolist() if not obj_df.empty else []
                                                else:
                                                    obj_df = conn.query(query)
                                                    obj_names = obj_df.iloc[:, 0].tolist() if not obj_df.empty else []
                                            except Exception:
                                                obj_names = []

                                            if obj_names:
                                                st.write(f"*{obj_type} in {schema}:*")
                                                for obj_name in obj_names:
                                                    st.checkbox(obj_name, key=f"sdo_obj_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}")
        elif access_mode == "Users need different access":
            num_users_diff = st.selectbox("Number of users needed access", list(range(1, 11)), key=f"sdo_diff_num_users_{sr}")

            for i in range(1, num_users_diff + 1):
                col_email, col_role = st.columns([2, 3])
                with col_email:
                    st.text_input(f"User-{i} Email", key=f"sdo_diff_user_email_{i}_{sr}")
                with col_role:
                    st.radio("Role", ["Read", "Read/Write", "Read/Write/Create"], index=None, horizontal=True, key=f"sdo_diff_role_{i}_{sr}")
                env_cols = st.columns(len(environments))
                user_selected_envs = []
                for idx, (env_label, env_code) in enumerate(environments):
                    with env_cols[idx]:
                        if st.checkbox(env_label, key=f"sdo_diff_env_{i}_{env_code}_{sr}"):
                            user_selected_envs.append((env_label, env_code))

                for env_label, env_code in user_selected_envs:
                    st.write(f"**{env_label}-Objects-User{i}**")
                    obj_row = st.columns(5)
                    obj_selections = {}
                    with obj_row[0]:
                        obj_selections["Tables"] = st.checkbox("Tables", key=f"sdo_diff_objtype_{i}_{env_code}_Tables_{sr}")
                    with obj_row[1]:
                        obj_selections["Functions"] = st.checkbox("Functions", key=f"sdo_diff_objtype_{i}_{env_code}_Functions_{sr}")
                    with obj_row[2]:
                        obj_selections["Procedures"] = st.checkbox("Procedures", key=f"sdo_diff_objtype_{i}_{env_code}_Procedures_{sr}")
                    with obj_row[3]:
                        obj_selections["Views"] = st.checkbox("Views", key=f"sdo_diff_objtype_{i}_{env_code}_Views_{sr}")
                    with obj_row[4]:
                        obj_selections["Stages"] = st.checkbox("Stages", key=f"sdo_diff_objtype_{i}_{env_code}_Stages_{sr}")

                    db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                    selected_obj_types = [ot for ot, oc in obj_selections.items() if oc]

                    if selected_obj_types:
                        try:
                            schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                            if not schema_df.empty:
                                schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                            else:
                                schema_list = []
                        except Exception:
                            schema_list = []

                        if schema_list:
                            st.write("**Schema List**")
                            for schema in schema_list:
                                schema_checked = st.checkbox(schema, key=f"sdo_diff_schema_{i}_{env_code}_{schema}_{sr}")
                                if schema_checked:
                                    # Show objects indented to the right
                                    _, obj_col = st.columns([0.5, 9.5])
                                    with obj_col:
                                        for obj_type in selected_obj_types:
                                            if obj_type == "Tables":
                                                query = f"SELECT TABLE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema.split('.')[1]}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                            elif obj_type == "Views":
                                                query = f"SELECT TABLE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema.split('.')[1]}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                            elif obj_type == "Functions":
                                                query = f"SELECT FUNCTION_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{schema.split('.')[1]}' ORDER BY FUNCTION_NAME"
                                            elif obj_type == "Procedures":
                                                query = f"SELECT PROCEDURE_NAME FROM {schema.split('.')[0]}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{schema.split('.')[1]}' ORDER BY PROCEDURE_NAME"
                                            elif obj_type == "Stages":
                                                query = f"SHOW STAGES IN {schema}"

                                            try:
                                                if obj_type == "Stages":
                                                    obj_df = conn.query(query)
                                                    obj_names = obj_df["name"].tolist() if not obj_df.empty else []
                                                else:
                                                    obj_df = conn.query(query)
                                                    obj_names = obj_df.iloc[:, 0].tolist() if not obj_df.empty else []
                                            except Exception:
                                                obj_names = []

                                            if obj_names:
                                                st.write(f"*{obj_type} in {schema}:*")
                                                for obj_name in obj_names:
                                                    st.checkbox(obj_name, key=f"sdo_diff_obj_{i}_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}")

        # Submit and Display buttons for Specific Database Object Access
        if access_mode is not None:
            if st.button("Submit", key="sdo_submit"):
                # Validation
                sdo_validation_errors = []

                # Check role is selected (for "All Users need same access" mode)
                if access_mode == "All Users need same access":
                    # Check at least one environment selected
                    if not selected_envs:
                        sdo_validation_errors.append("At least one environment must be selected.")

                    selected_role = st.session_state.get(f"sdo_role_select_{sr}", None)
                    if not selected_role:
                        sdo_validation_errors.append("Role must be selected.")

                    # Check user emails filled
                    num_users = st.session_state.get(f"sdo_num_users_{sr}", 1)
                    for i in range(1, num_users + 1):
                        email = st.session_state.get(f"sdo_user_email_{i}_{sr}", "")
                        if not email:
                            sdo_validation_errors.append(f"User-{i} Email is empty.")

                    # Check at least one object selected per checked object type
                    checked_obj_types = []
                    for ot in ["Tables", "Functions", "Procedures", "Views", "Stages"]:
                        if st.session_state.get(f"sdo_objtype_{ot}_{sr}", False):
                            checked_obj_types.append(ot)

                    if not checked_obj_types:
                        sdo_validation_errors.append("At least one object type must be selected.")
                    else:
                        for ot in checked_obj_types:
                            has_obj_for_type = False
                            for key, val in st.session_state.items():
                                if key.startswith("sdo_obj_") and f"_{ot}_" in key and key.endswith(f"_{sr}") and val is True:
                                    has_obj_for_type = True
                                    break
                            if not has_obj_for_type:
                                sdo_validation_errors.append(f"At least one {ot.lower()} must be selected.")
                else:
                    # Users need different access
                    num_users_diff = st.session_state.get(f"sdo_diff_num_users_{sr}", 1)
                    for i in range(1, num_users_diff + 1):
                        email = st.session_state.get(f"sdo_diff_user_email_{i}_{sr}", "")
                        if not email:
                            sdo_validation_errors.append(f"User-{i} Email is empty.")
                        role = st.session_state.get(f"sdo_diff_role_{i}_{sr}", None)
                        if not role:
                            sdo_validation_errors.append(f"User-{i} Role must be selected.")
                        # Check at least one environment selected per user
                        user_has_env = False
                        for _, ec in environments:
                            if st.session_state.get(f"sdo_diff_env_{i}_{ec}_{sr}", False):
                                user_has_env = True
                                break
                        if not user_has_env:
                            sdo_validation_errors.append(f"User-{i}: At least one environment must be selected.")

                    # Check at least one object selected per checked object type per user
                    for i in range(1, num_users_diff + 1):
                        for ot in ["Tables", "Functions", "Procedures", "Views", "Stages"]:
                            # Check if this object type is checked for any env for this user
                            ot_checked = False
                            for _, ec in environments:
                                if st.session_state.get(f"sdo_diff_objtype_{i}_{ec}_{ot}_{sr}", False):
                                    ot_checked = True
                                    break
                            if ot_checked:
                                has_obj_for_type = False
                                for key, val in st.session_state.items():
                                    if key.startswith(f"sdo_diff_obj_{i}_") and f"_{ot}_" in key and key.endswith(f"_{sr}") and val is True:
                                        has_obj_for_type = True
                                        break
                                if not has_obj_for_type:
                                    sdo_validation_errors.append(f"User-{i}: At least one {ot.lower()} must be selected.")

                if sdo_validation_errors:
                    st.error("Please enter all details")
                else:
                    t_val = selected_tenant
                    s_val = selected_subtenant
                    p_val = selected_project

                    rows_to_insert = []

                    if access_mode == "All Users need same access":
                        # Collect user emails
                        num_users = st.session_state.get(f"sdo_num_users_{sr}", 1)
                        user_emails = []
                        for i in range(1, num_users + 1):
                            email = st.session_state.get(f"sdo_user_email_{i}_{sr}", "")
                            if email:
                                user_emails.append(email)

                        selected_role = st.session_state.get(f"sdo_role_select_{sr}", "Read")

                        # Collect checked objects from checkbox keys: sdo_obj_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}
                        for key, val in st.session_state.items():
                            if key.startswith("sdo_obj_") and key.endswith(f"_{sr}") and val is True:
                                # Parse: sdo_obj_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}
                                parts = key[len("sdo_obj_"):]  # remove prefix
                                parts = parts[:-(len(str(sr)) + 1)]  # remove trailing _{sr}
                                # Find env_code (first segment before _)
                                # Format: {env_code}_{db_name}.{schema_name}_{obj_type}_{obj_name}
                                # env_code is one of DEV, SIT, ST, UAT, PREPROD, PROD
                                env_code_found = None
                                for _, ec in environments:
                                    if parts.startswith(f"{ec}_"):
                                        env_code_found = ec
                                        break
                                if not env_code_found:
                                    continue
                                remainder = parts[len(env_code_found) + 1:]
                                # remainder: {db_name}.{schema_name}_{obj_type}_{obj_name}
                                # obj_name is last segment, obj_type is second-to-last
                                # But obj_name and schema can contain underscores, so we need a different approach
                                # Schema format is DB_NAME.SCHEMA_NAME which contains a dot
                                # Split on the dot to find the schema boundary
                                dot_idx = remainder.find(".")
                                if dot_idx < 0:
                                    continue
                                # Find next underscore after the dot to get schema end
                                after_dot = remainder[dot_idx + 1:]
                                # after_dot: SCHEMA_NAME_{obj_type}_{obj_name}
                                # We know obj_types: Tables, Views, Functions, Procedures, Stages
                                obj_type_found = None
                                schema_end_idx = None
                                for ot in ["Tables", "Views", "Functions", "Procedures", "Stages"]:
                                    marker = f"_{ot}_"
                                    pos = after_dot.find(marker)
                                    if pos >= 0:
                                        obj_type_found = ot
                                        schema_end_idx = dot_idx + 1 + pos
                                        obj_name = after_dot[pos + len(marker):]
                                        break
                                if not obj_type_found:
                                    continue
                                schema_name = remainder[:schema_end_idx]
                                full_schema = f"{remainder[:dot_idx]}.{after_dot[:after_dot.find(f'_{obj_type_found}_')]}"

                                # Map env_code to label
                                env_label = env_code_found
                                for el, ec in environments:
                                    if ec == env_code_found:
                                        env_label = el
                                        break

                                for user_email in user_emails:
                                    rows_to_insert.append((user_email, selected_role, env_label, full_schema, obj_type_found.lower(), obj_name))
                    else:
                        # Users need different access
                        num_users_diff = st.session_state.get(f"sdo_diff_num_users_{sr}", 1)
                        for i in range(1, num_users_diff + 1):
                            user_email = st.session_state.get(f"sdo_diff_user_email_{i}_{sr}", "")
                            user_role = st.session_state.get(f"sdo_diff_role_{i}_{sr}", "Read")
                            if not user_email:
                                continue

                            # Collect checked objects: sdo_diff_obj_{i}_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}
                            prefix = f"sdo_diff_obj_{i}_"
                            for key, val in st.session_state.items():
                                if key.startswith(prefix) and key.endswith(f"_{sr}") and val is True:
                                    parts = key[len(prefix):]
                                    parts = parts[:-(len(str(sr)) + 1)]  # remove trailing _{sr}
                                    # Find env_code
                                    env_code_found = None
                                    for _, ec in environments:
                                        if parts.startswith(f"{ec}_"):
                                            env_code_found = ec
                                            break
                                    if not env_code_found:
                                        continue
                                    remainder = parts[len(env_code_found) + 1:]
                                    dot_idx = remainder.find(".")
                                    if dot_idx < 0:
                                        continue
                                    after_dot = remainder[dot_idx + 1:]
                                    obj_type_found = None
                                    for ot in ["Tables", "Views", "Functions", "Procedures", "Stages"]:
                                        marker = f"_{ot}_"
                                        pos = after_dot.find(marker)
                                        if pos >= 0:
                                            obj_type_found = ot
                                            obj_name = after_dot[pos + len(marker):]
                                            break
                                    if not obj_type_found:
                                        continue
                                    full_schema = f"{remainder[:dot_idx]}.{after_dot[:after_dot.find(f'_{obj_type_found}_')]}"

                                    # Map env_code to label
                                    env_label = env_code_found
                                    for el, ec in environments:
                                        if ec == env_code_found:
                                            env_label = el
                                            break

                                    rows_to_insert.append((user_email, user_role, env_label, full_schema, obj_type_found.lower(), obj_name))

                    if rows_to_insert:
                        insert_count = 0
                        session = conn.session()
                        for user_email, role_type, env_label, schema_name, obj_type, obj_name in rows_to_insert:
                            session.sql(
                                f"""INSERT INTO META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST
                                    (TENANT, SUBTENANT, PROJECT, REQUEST_TYPE, "USER", ENVIRONMENT, SCHEMA, OBJECTS, OBJECT_NAMES)
                                    VALUES ('{t_val}', '{s_val}', '{p_val}', '{role_type}', '{user_email}', '{env_label}', '{schema_name}', '{obj_type}', '{obj_name}')"""
                            ).collect()
                            insert_count += 1
                        st.session_state["show_success"] = True
                        st.session_state["sdo_reset"] += 1
                        st.rerun()

            if st.button("Display", key="sdo_display"):
                display_df = conn.query("SELECT * FROM META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST")
                if not display_df.empty:
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("No records found in ACCESS_REQUEST table.")
else:
    mirrored_access_ai = st.radio("Mirrored access of existing user", ["Yes", "No"], index=None, horizontal=True, key="ai_mirrored")
    if mirrored_access_ai == "Yes":
        mirror_username_ai = st.text_input("Provide the username to be mirrored", key="ai_mirror_username")
    elif mirrored_access_ai == "No":
        tenants = sorted(df["TENANT"].unique())
        selected_subtenant = None
        selected_project = None

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_tenant = st.selectbox("Tenants", tenants, key="ai_tenant")

        filtered_by_tenant = df[df["TENANT"] == selected_tenant]
        subtenants = sorted(filtered_by_tenant["SUBTENANT"].unique())
        with col2:
            selected_subtenant = st.selectbox("Subtenants", subtenants, key="ai_subtenant")

        filtered_by_subtenant = filtered_by_tenant[filtered_by_tenant["SUBTENANT"] == selected_subtenant]
        projects = sorted(filtered_by_subtenant["PROJECT"].unique())
        with col3:
            selected_project = st.selectbox("Projects", projects, key="ai_project")

        import re
        tenant_abbr = re.search(r'\[(.+?)\]', selected_tenant)
        subtenant_abbr = re.search(r'\[(.+?)\]', selected_subtenant)
        tenant_code = tenant_abbr.group(1) if tenant_abbr else selected_tenant
        subtenant_code = subtenant_abbr.group(1) if subtenant_abbr else selected_subtenant

        environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

        st.subheader("Environments to which access is needed")
        selected_envs = []
        env_cols = st.columns(len(environments))
        for idx, (env_label, env_code) in enumerate(environments):
            with env_cols[idx]:
                if st.checkbox(env_label, key=f"ai_env_{env_code}"):
                    selected_envs.append((env_label, env_code))

        if selected_envs:
            env_names_str = "/".join([env_label for env_label, _ in selected_envs])

            # Per-environment user and schema listing
            for env_label, env_code in selected_envs:
                st.markdown(f"---")
                num_users = st.selectbox(f"Number of users needed access-[{env_label}]", list(range(1, 11)), key=f"ai_num_users_{env_code}")

                # Show "All users need same access" only if more than 1 user selected
                all_same_access = False
                if num_users > 1:
                    all_same_access = st.checkbox(f"All [{env_label}] Users need same access", key=f"ai_all_same_{env_code}")

                db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                try:
                    schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                    if not schema_df.empty:
                        schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                    else:
                        schema_list = []
                except Exception:
                    schema_list = []

                if all_same_access:
                    # When "All users need same access" is checked: shared role checkboxes below
                    rc1, rc2, rc3 = st.columns(3)
                    with rc1:
                        st.checkbox("Create Agent", key=f"ai_role_create_agent_{env_code}")
                        st.checkbox("Cortex Services/Functions Cortex Copilot", key=f"ai_role_cortex_copilot_{env_code}")
                        agent_usage_checked = st.checkbox("Agent Usage", key=f"ai_role_agent_usage_{env_code}")
                    with rc2:
                        st.checkbox("Create Cortex Search Service", key=f"ai_role_cortex_search_{env_code}")
                        st.checkbox("Copilot access", key=f"ai_role_copilot_access_{env_code}")
                    with rc3:
                        st.checkbox("Create Semantic View", key=f"ai_role_semantic_view_{env_code}")
                        agent_monitoring_checked = st.checkbox("Agent Monitoring", key=f"ai_role_agent_monitoring_{env_code}")

                    # Shared schema list for all users in this environment
                    if schema_list:
                        st.write(f"**Schema List ({env_label})**")
                        for schema in schema_list:
                            st.checkbox(schema, key=f"ai_shared_schema_{env_code}_{schema}")

                    # Show agents in schema if Agent Usage or Agent Monitoring is checked
                    if (agent_usage_checked or agent_monitoring_checked) and schema_list:
                        for schema in schema_list:
                            schema_parts = schema.split(".")
                            try:
                                agents_df = conn.query(f"SHOW CORTEX SEARCH SERVICES IN {schema}")
                                if agents_df.empty:
                                    agents_df = conn.query(f"SHOW SNOWFLAKE.ML.ANOMALY_DETECTION IN {schema}")
                            except Exception:
                                agents_df = None
                            try:
                                agent_list_df = conn.query(f"SELECT AGENT_NAME FROM {schema_parts[0]}.INFORMATION_SCHEMA.CORTEX_AGENTS WHERE AGENT_SCHEMA = '{schema_parts[1]}' ORDER BY AGENT_NAME")
                            except Exception:
                                try:
                                    agent_list_df = conn.query(f"SHOW CORTEX AGENTS IN {schema}")
                                except Exception:
                                    agent_list_df = None
                            if agent_list_df is not None and not agent_list_df.empty:
                                st.write(f"**Agents in {schema}**")
                                agent_names = agent_list_df.iloc[:, 0].tolist() if not agent_list_df.empty else []
                                for agent_name in agent_names:
                                    st.checkbox(agent_name, key=f"ai_agent_{env_code}_{schema}_{agent_name}")

                    for i in range(1, num_users + 1):
                        st.text_input(f"User-{i} Email-[{env_label}]", key=f"ai_user_email_{env_code}_{i}")
                else:
                    # Per-user: checkboxes next to each user email
                    for i in range(1, num_users + 1):
                        st.text_input(f"User-{i} Email-[{env_label}]", key=f"ai_user_email_{env_code}_{i}")
                        rc1, rc2, rc3 = st.columns(3)
                        with rc1:
                            st.checkbox("Create Agent", key=f"ai_role_create_agent_{env_code}_{i}")
                            st.checkbox("Cortex Services/Functions Cortex Copilot", key=f"ai_role_cortex_copilot_{env_code}_{i}")
                            agent_usage_checked_i = st.checkbox("Agent Usage", key=f"ai_role_agent_usage_{env_code}_{i}")
                        with rc2:
                            st.checkbox("Create Cortex Search Service", key=f"ai_role_cortex_search_{env_code}_{i}")
                            st.checkbox("Copilot access", key=f"ai_role_copilot_access_{env_code}_{i}")
                        with rc3:
                            st.checkbox("Create Semantic View", key=f"ai_role_semantic_view_{env_code}_{i}")
                            agent_monitoring_checked_i = st.checkbox("Agent Monitoring", key=f"ai_role_agent_monitoring_{env_code}_{i}")

                        if schema_list:
                            st.write(f"**Schema List ({env_label}) - User-{i}**")
                            for schema in schema_list:
                                st.checkbox(schema, key=f"ai_schema_{env_code}_{i}_{schema}")

                        # Show agents in schema if Agent Usage or Agent Monitoring is checked for this user
                        if (agent_usage_checked_i or agent_monitoring_checked_i) and schema_list:
                            for schema in schema_list:
                                schema_parts = schema.split(".")
                                try:
                                    agent_list_df = conn.query(f"SELECT AGENT_NAME FROM {schema_parts[0]}.INFORMATION_SCHEMA.CORTEX_AGENTS WHERE AGENT_SCHEMA = '{schema_parts[1]}' ORDER BY AGENT_NAME")
                                except Exception:
                                    try:
                                        agent_list_df = conn.query(f"SHOW CORTEX AGENTS IN {schema}")
                                    except Exception:
                                        agent_list_df = None
                                if agent_list_df is not None and not agent_list_df.empty:
                                    st.write(f"**Agents in {schema} - User-{i}**")
                                    agent_names = agent_list_df.iloc[:, 0].tolist() if not agent_list_df.empty else []
                                    for agent_name in agent_names:
                                        st.checkbox(agent_name, key=f"ai_agent_{env_code}_{i}_{schema}_{agent_name}")
