# Streamlit app for user access request management with tenant/project hierarchy
# Co-authored with CoCo
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

        sr = st.session_state["sdo_reset"]
        environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

        num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key=f"sdo_num_users_{sr}")

        if num_users > 1:
            access_mode = st.radio("Access Mode", ["All Users need same access", "Users need different access"], index=None, horizontal=True, key=f"sdo_access_mode_{sr}")
        else:
            access_mode = "All Users need same access"

        if access_mode == "All Users need same access":
            for i in range(1, num_users + 1):
                st.text_input(f"User-{i} Email", key=f"sdo_user_email_{i}_{sr}")

            st.radio("Role", ["Read", "Read/Write", "Read/Write/Create"], index=None, horizontal=True, key=f"sdo_role_{sr}")

            st.subheader("Environment to which access is needed")
            env_cols = st.columns(len(environments))
            selected_envs = []
            for idx, (env_label, env_code) in enumerate(environments):
                with env_cols[idx]:
                    if st.checkbox(env_label, key=f"sdo_env_{env_code}_{sr}"):
                        selected_envs.append((env_label, env_code))

            if selected_envs:
                st.subheader("Select Object Types")
                obj_row = st.columns(5)
                with obj_row[0]:
                    st.checkbox("Tables", key=f"sdo_objtype_Tables_{sr}")
                with obj_row[1]:
                    st.checkbox("Functions", key=f"sdo_objtype_Functions_{sr}")
                with obj_row[2]:
                    st.checkbox("Procedures", key=f"sdo_objtype_Procedures_{sr}")
                with obj_row[3]:
                    st.checkbox("Views", key=f"sdo_objtype_Views_{sr}")
                with obj_row[4]:
                    st.checkbox("Stages", key=f"sdo_objtype_Stages_{sr}")

                selected_obj_types = []
                for ot in ["Tables", "Functions", "Procedures", "Views", "Stages"]:
                    if st.session_state.get(f"sdo_objtype_{ot}_{sr}", False):
                        selected_obj_types.append(ot)

                if selected_obj_types:
                    for env_label, env_code in selected_envs:
                        db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                        try:
                            schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                            if not schema_df.empty:
                                schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                            else:
                                schema_list = []
                        except Exception:
                            schema_list = []

                        if schema_list:
                            st.write(f"**Schema List ({env_label})**")
                            for schema in schema_list:
                                schema_checked = st.checkbox(schema, key=f"sdo_schema_{env_code}_{schema}_{sr}")
                                if schema_checked:
                                    db_part = schema.split('.')[0]
                                    schema_part = schema.split('.')[1]
                                    for obj_type in selected_obj_types:
                                        if obj_type == "Tables":
                                            query = f"SELECT TABLE_NAME FROM {db_part}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_part}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                        elif obj_type == "Views":
                                            query = f"SELECT TABLE_NAME FROM {db_part}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_part}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                        elif obj_type == "Functions":
                                            query = f"SELECT FUNCTION_NAME FROM {db_part}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{schema_part}' ORDER BY FUNCTION_NAME"
                                        elif obj_type == "Procedures":
                                            query = f"SELECT PROCEDURE_NAME FROM {db_part}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{schema_part}' ORDER BY PROCEDURE_NAME"
                                        elif obj_type == "Stages":
                                            query = f"SHOW STAGES IN {schema}"

                                        try:
                                            if obj_type == "Stages":
                                                obj_df = conn.query(query)
                                                obj_names = obj_df["name"].tolist() if not obj_df.empty else []
                                            else:
                                                obj_df = conn.query(query)
                                                obj_names = obj_df.iloc[:, 0].tolist() if not obj_df.empty else []
                                        except Exception as e:
                                            obj_names = []
                                            st.warning(f"Could not fetch {obj_type.lower()} from {schema}: {e}")

                                        if obj_names:
                                            st.write(f"*{obj_type} in {schema}:*")
                                            for obj_name in obj_names:
                                                st.checkbox(f"  {obj_name}", key=f"sdo_obj_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}")

        elif access_mode == "Users need different access":
            for i in range(1, num_users + 1):
                st.markdown(f"---")
                st.text_input(f"User-{i} Email", key=f"sdo_user_email_{i}_{sr}")

                env_cols = st.columns(len(environments))
                user_selected_envs = []
                for idx, (env_label, env_code) in enumerate(environments):
                    with env_cols[idx]:
                        if st.checkbox(env_label, key=f"sdo_env_{i}_{env_code}_{sr}"):
                            user_selected_envs.append((env_label, env_code))

                for env_label, env_code in user_selected_envs:
                    role_options = [f"Read-{env_label}", f"Read/Write-{env_label}", f"Read/Write/Create-{env_label}"]
                    st.radio(f"Role ({env_label}) - User{i} :", role_options, index=None, horizontal=True, key=f"sdo_role_{i}_{env_code}_{sr}")

                    obj_row = st.columns(5)
                    with obj_row[0]:
                        st.checkbox("Tables", key=f"sdo_objtype_{i}_{env_code}_Tables_{sr}")
                    with obj_row[1]:
                        st.checkbox("Functions", key=f"sdo_objtype_{i}_{env_code}_Functions_{sr}")
                    with obj_row[2]:
                        st.checkbox("Procedures", key=f"sdo_objtype_{i}_{env_code}_Procedures_{sr}")
                    with obj_row[3]:
                        st.checkbox("Views", key=f"sdo_objtype_{i}_{env_code}_Views_{sr}")
                    with obj_row[4]:
                        st.checkbox("Stages", key=f"sdo_objtype_{i}_{env_code}_Stages_{sr}")

                    selected_obj_types = []
                    for ot in ["Tables", "Functions", "Procedures", "Views", "Stages"]:
                        if st.session_state.get(f"sdo_objtype_{i}_{env_code}_{ot}_{sr}", False):
                            selected_obj_types.append(ot)

                    if selected_obj_types:
                        db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                        try:
                            schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                            if not schema_df.empty:
                                schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                            else:
                                schema_list = []
                        except Exception:
                            schema_list = []

                        if schema_list:
                            st.write(f"**Schema List ({env_label})**")
                            for schema in schema_list:
                                schema_checked = st.checkbox(schema, key=f"sdo_schema_{i}_{env_code}_{schema}_{sr}")
                                if schema_checked:
                                    db_part = schema.split('.')[0]
                                    schema_part = schema.split('.')[1]
                                    for obj_type in selected_obj_types:
                                        if obj_type == "Tables":
                                            query = f"SELECT TABLE_NAME FROM {db_part}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_part}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                        elif obj_type == "Views":
                                            query = f"SELECT TABLE_NAME FROM {db_part}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_part}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                        elif obj_type == "Functions":
                                            query = f"SELECT FUNCTION_NAME FROM {db_part}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{schema_part}' ORDER BY FUNCTION_NAME"
                                        elif obj_type == "Procedures":
                                            query = f"SELECT PROCEDURE_NAME FROM {db_part}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{schema_part}' ORDER BY PROCEDURE_NAME"
                                        elif obj_type == "Stages":
                                            query = f"SHOW STAGES IN {schema}"

                                        try:
                                            if obj_type == "Stages":
                                                obj_df = conn.query(query)
                                                obj_names = obj_df["name"].tolist() if not obj_df.empty else []
                                            else:
                                                obj_df = conn.query(query)
                                                obj_names = obj_df.iloc[:, 0].tolist() if not obj_df.empty else []
                                        except Exception as e:
                                            obj_names = []
                                            st.warning(f"Could not fetch {obj_type.lower()} from {schema}: {e}")

                                        if obj_names:
                                            st.write(f"*{obj_type} in {schema}:*")
                                            for obj_name in obj_names:
                                                st.checkbox(f"  {obj_name}", key=f"sdo_obj_{i}_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}")

        # Submit and Display buttons for Specific Database Object Access
        if access_mode is not None:
            if st.button("Submit", key="sdo_submit"):
                sdo_validation_errors = []
                num_users = st.session_state.get(f"sdo_num_users_{sr}", 1)
                access_mode = st.session_state.get(f"sdo_access_mode_{sr}", "All Users need same access") if num_users > 1 else "All Users need same access"

                if access_mode == "All Users need same access":
                    for ui in range(1, num_users + 1):
                        email = st.session_state.get(f"sdo_user_email_{ui}_{sr}", "")
                        if not email:
                            sdo_validation_errors.append(f"User-{ui} Email is empty.")
                else:
                    for ui in range(1, num_users + 1):
                        email = st.session_state.get(f"sdo_user_email_{ui}_{sr}", "")
                        if not email:
                            sdo_validation_errors.append(f"User-{ui} Email is empty.")

                if sdo_validation_errors:
                    st.error("Please enter all details")
                else:
                    t_val = selected_tenant
                    s_val = selected_subtenant
                    p_val = selected_project
                    rows_to_insert = []

                    if access_mode == "All Users need same access":
                        shared_role = st.session_state.get(f"sdo_role_{sr}", "Read")
                        for ui in range(1, num_users + 1):
                            user_email = st.session_state.get(f"sdo_user_email_{ui}_{sr}", "")
                            if not user_email:
                                continue
                            # Collect checked objects (shared): sdo_obj_{env_code}_{schema}_{obj_type}_{obj_name}_{sr}
                            for key, val in st.session_state.items():
                                if key.startswith("sdo_obj_") and key.endswith(f"_{sr}") and val is True:
                                    parts = key[len("sdo_obj_"):]
                                    parts = parts[:-(len(str(sr)) + 1)]
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
                                    env_label_found = env_code_found
                                    for el, ec in environments:
                                        if ec == env_code_found:
                                            env_label_found = el
                                            break
                                    rows_to_insert.append((user_email, shared_role, env_label_found, full_schema, obj_type_found.lower(), obj_name))
                    else:
                        # Users need different access
                        for ui in range(1, num_users + 1):
                            user_email = st.session_state.get(f"sdo_user_email_{ui}_{sr}", "")
                            if not user_email:
                                continue
                            prefix = f"sdo_obj_{ui}_"
                            for key, val in st.session_state.items():
                                if key.startswith(prefix) and key.endswith(f"_{sr}") and val is True:
                                    parts = key[len(prefix):]
                                    parts = parts[:-(len(str(sr)) + 1)]
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
                                    env_label_found = env_code_found
                                    for el, ec in environments:
                                        if ec == env_code_found:
                                            env_label_found = el
                                            break
                                    # Get role for this user + environment
                                    env_role = st.session_state.get(f"sdo_role_{ui}_{env_code_found}_{sr}", "")
                                    rows_to_insert.append((user_email, env_role, env_label_found, full_schema, obj_type_found.lower(), obj_name))

                    if rows_to_insert:
                        session = conn.session()
                        for user_email, role_type, env_label, schema_name, obj_type, obj_name in rows_to_insert:
                            session.sql(
                                f"""INSERT INTO META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST
                                    (TENANT, SUBTENANT, PROJECT, REQUEST_TYPE, "USER", ENVIRONMENT, SCHEMA, OBJECTS, OBJECT_NAMES)
                                    VALUES ('{t_val}', '{s_val}', '{p_val}', '{role_type}', '{user_email}', '{env_label}', '{schema_name}', '{obj_type}', '{obj_name}')"""
                            ).collect()
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

        if "ai_reset" not in st.session_state:
            st.session_state["ai_reset"] = 0
        ai_sr = st.session_state["ai_reset"]

        environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

        st.subheader("Environment to which access is needed")
        selected_envs = []
        env_cols = st.columns(len(environments))
        for idx, (env_label, env_code) in enumerate(environments):
            with env_cols[idx]:
                if st.checkbox(env_label, key=f"ai_env_{env_code}_{ai_sr}"):
                    selected_envs.append((env_label, env_code))

        if selected_envs:
            num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key=f"ai_num_users_{ai_sr}")

            if num_users > 1:
                access_mode_ai = st.radio("Access Mode", ["All Users need same access", "Users need different access"], index=None, horizontal=True, key=f"ai_access_mode_{ai_sr}")
            else:
                access_mode_ai = "All Users need same access"

            if access_mode_ai == "All Users need same access":
                for i in range(1, num_users + 1):
                    st.text_input(f"User-{i} Email", key=f"ai_user_email_{i}_{ai_sr}")

                st.subheader("Select AI Roles")
                rc1, rc2, rc3 = st.columns(3)
                with rc1:
                    st.checkbox("Create Agent", key=f"ai_role_create_agent_{ai_sr}")
                    st.checkbox("Cortex Services/Functions", key=f"ai_role_cortex_services_{ai_sr}")
                    st.checkbox("Agent Usage", key=f"ai_role_agent_usage_{ai_sr}")
                with rc2:
                    st.checkbox("Create Cortex Search Service", key=f"ai_role_cortex_search_{ai_sr}")
                    st.checkbox("Copilot access", key=f"ai_role_copilot_access_{ai_sr}")
                with rc3:
                    st.checkbox("Create Semantic View", key=f"ai_role_semantic_view_{ai_sr}")
                    st.checkbox("Agent Monitoring", key=f"ai_role_agent_monitoring_{ai_sr}")

                # Read selected AI roles from session_state
                selected_ai_roles = []
                for role_name, role_key in [
                    ("Create Agent", f"ai_role_create_agent_{ai_sr}"),
                    ("Cortex Services/Functions", f"ai_role_cortex_services_{ai_sr}"),
                    ("Agent Usage", f"ai_role_agent_usage_{ai_sr}"),
                    ("Create Cortex Search Service", f"ai_role_cortex_search_{ai_sr}"),
                    ("Copilot access", f"ai_role_copilot_access_{ai_sr}"),
                    ("Create Semantic View", f"ai_role_semantic_view_{ai_sr}"),
                    ("Agent Monitoring", f"ai_role_agent_monitoring_{ai_sr}"),
                ]:
                    if st.session_state.get(role_key, False):
                        selected_ai_roles.append(role_name)

                # Show schemas only if non-Copilot roles are checked
                schema_roles = [r for r in selected_ai_roles if r != "Copilot access"]

                if schema_roles:
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
                                st.checkbox(schema, key=f"ai_schema_{env_code}_{schema}_{ai_sr}")

            elif access_mode_ai == "Users need different access":
                for i in range(1, num_users + 1):
                    col_email, col_role = st.columns([2, 3])
                    with col_email:
                        st.text_input(f"User-{i} Email", key=f"ai_diff_user_email_{i}_{ai_sr}")

                    env_cols = st.columns(len(environments))
                    user_selected_envs = []
                    for idx, (env_label, env_code) in enumerate(environments):
                        with env_cols[idx]:
                            if st.checkbox(env_label, key=f"ai_diff_env_{i}_{env_code}_{ai_sr}"):
                                user_selected_envs.append((env_label, env_code))

                    for env_label, env_code in user_selected_envs:
                        st.write(f"**{env_label} - AI Roles - User{i}**")
                        rc1, rc2, rc3 = st.columns(3)
                        with rc1:
                            st.checkbox("Create Agent", key=f"ai_diff_role_create_agent_{i}_{env_code}_{ai_sr}")
                            st.checkbox("Cortex Services/Functions", key=f"ai_diff_role_cortex_services_{i}_{env_code}_{ai_sr}")
                            st.checkbox("Agent Usage", key=f"ai_diff_role_agent_usage_{i}_{env_code}_{ai_sr}")
                        with rc2:
                            st.checkbox("Create Cortex Search Service", key=f"ai_diff_role_cortex_search_{i}_{env_code}_{ai_sr}")
                            st.checkbox("Copilot access", key=f"ai_diff_role_copilot_access_{i}_{env_code}_{ai_sr}")
                        with rc3:
                            st.checkbox("Create Semantic View", key=f"ai_diff_role_semantic_view_{i}_{env_code}_{ai_sr}")
                            st.checkbox("Agent Monitoring", key=f"ai_diff_role_agent_monitoring_{i}_{env_code}_{ai_sr}")

                        # Read selected AI roles for this user/env from session_state
                        user_ai_roles = []
                        for role_name, role_key in [
                            ("Create Agent", f"ai_diff_role_create_agent_{i}_{env_code}_{ai_sr}"),
                            ("Cortex Services/Functions", f"ai_diff_role_cortex_services_{i}_{env_code}_{ai_sr}"),
                            ("Agent Usage", f"ai_diff_role_agent_usage_{i}_{env_code}_{ai_sr}"),
                            ("Create Cortex Search Service", f"ai_diff_role_cortex_search_{i}_{env_code}_{ai_sr}"),
                            ("Copilot access", f"ai_diff_role_copilot_access_{i}_{env_code}_{ai_sr}"),
                            ("Create Semantic View", f"ai_diff_role_semantic_view_{i}_{env_code}_{ai_sr}"),
                            ("Agent Monitoring", f"ai_diff_role_agent_monitoring_{i}_{env_code}_{ai_sr}"),
                        ]:
                            if st.session_state.get(role_key, False):
                                user_ai_roles.append(role_name)

                        # Show schemas only if non-Copilot roles are checked
                        user_schema_roles = [r for r in user_ai_roles if r != "Copilot access"]

                        if user_schema_roles:
                            db_name = f"{tenant_code}_{subtenant_code}_{selected_project}_{env_code}_DB"
                            try:
                                schema_df = conn.query(f"SELECT SCHEMA_NAME FROM {db_name}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME != 'INFORMATION_SCHEMA' ORDER BY SCHEMA_NAME")
                                if not schema_df.empty:
                                    schema_list = [f"{db_name}.{row['SCHEMA_NAME']}" for _, row in schema_df.iterrows()]
                                else:
                                    schema_list = []
                            except Exception as e:
                                schema_list = []
                                st.warning(f"Could not fetch schemas from {db_name}: {e}")

                            if schema_list:
                                st.write(f"**Schema List ({env_label}) - User-{i}**")
                                for schema in schema_list:
                                    st.checkbox(schema, key=f"ai_diff_schema_{i}_{env_code}_{schema}_{ai_sr}")

            # Submit and Display buttons for AI Users Roles
            if access_mode_ai is not None:
                if st.button("Submit", key="ai_submit"):
                    ai_validation_errors = []
                    ai_rows_to_insert = []

                    t_val = selected_tenant
                    s_val = selected_subtenant
                    p_val = selected_project

                    if access_mode_ai == "All Users need same access":
                        if not selected_envs:
                            ai_validation_errors.append("At least one environment must be selected.")

                        # Check user emails
                        num_users = st.session_state.get(f"ai_num_users_{ai_sr}", 1)
                        user_emails = []
                        for i in range(1, num_users + 1):
                            email = st.session_state.get(f"ai_user_email_{i}_{ai_sr}", "")
                            if not email:
                                ai_validation_errors.append(f"User-{i} Email is empty.")
                            else:
                                user_emails.append(email)

                        # Check roles
                        selected_ai_roles = []
                        for role_name, role_key in [
                            ("Create Agent", f"ai_role_create_agent_{ai_sr}"),
                            ("Cortex Services/Functions", f"ai_role_cortex_services_{ai_sr}"),
                            ("Agent Usage", f"ai_role_agent_usage_{ai_sr}"),
                            ("Create Cortex Search Service", f"ai_role_cortex_search_{ai_sr}"),
                            ("Copilot access", f"ai_role_copilot_access_{ai_sr}"),
                            ("Create Semantic View", f"ai_role_semantic_view_{ai_sr}"),
                            ("Agent Monitoring", f"ai_role_agent_monitoring_{ai_sr}"),
                        ]:
                            if st.session_state.get(role_key, False):
                                selected_ai_roles.append(role_name)

                        if not selected_ai_roles:
                            ai_validation_errors.append("At least one AI role must be selected.")

                        # Collect checked schemas per env
                        schema_roles = [r for r in selected_ai_roles if r != "Copilot access"]
                        has_copilot = "Copilot access" in selected_ai_roles

                        checked_schemas_by_env = {}
                        for env_label, env_code in selected_envs:
                            env_schemas = []
                            for key, val in st.session_state.items():
                                if key.startswith(f"ai_schema_{env_code}_") and key.endswith(f"_{ai_sr}") and val is True:
                                    schema_name = key[len(f"ai_schema_{env_code}_"):-(len(str(ai_sr)) + 1)]
                                    env_schemas.append(schema_name)
                            checked_schemas_by_env[env_code] = env_schemas

                        if schema_roles:
                            for env_label, env_code in selected_envs:
                                if not checked_schemas_by_env.get(env_code):
                                    ai_validation_errors.append(f"{env_label}: At least one schema must be selected for non-Copilot roles.")

                        if not ai_validation_errors:
                            for user_email in user_emails:
                                for env_label, env_code in selected_envs:
                                    if has_copilot:
                                        ai_rows_to_insert.append((user_email, "Copilot access", env_label, None))
                                    for role_label in schema_roles:
                                        for schema_name in checked_schemas_by_env.get(env_code, []):
                                            ai_rows_to_insert.append((user_email, role_label, env_label, schema_name))

                    else:
                        # Users need different access
                        num_users_diff = st.session_state.get(f"ai_num_users_{ai_sr}", 1)

                        for i in range(1, num_users_diff + 1):
                            email = st.session_state.get(f"ai_diff_user_email_{i}_{ai_sr}", "")
                            if not email:
                                ai_validation_errors.append(f"User-{i} Email is empty.")
                                continue

                            for env_label, env_code in environments:
                                if not st.session_state.get(f"ai_diff_env_{i}_{env_code}_{ai_sr}", False):
                                    continue

                                user_roles = []
                                for role_name, role_key in [
                                    ("Create Agent", f"ai_diff_role_create_agent_{i}_{env_code}_{ai_sr}"),
                                    ("Cortex Services/Functions", f"ai_diff_role_cortex_services_{i}_{env_code}_{ai_sr}"),
                                    ("Agent Usage", f"ai_diff_role_agent_usage_{i}_{env_code}_{ai_sr}"),
                                    ("Create Cortex Search Service", f"ai_diff_role_cortex_search_{i}_{env_code}_{ai_sr}"),
                                    ("Copilot access", f"ai_diff_role_copilot_access_{i}_{env_code}_{ai_sr}"),
                                    ("Create Semantic View", f"ai_diff_role_semantic_view_{i}_{env_code}_{ai_sr}"),
                                    ("Agent Monitoring", f"ai_diff_role_agent_monitoring_{i}_{env_code}_{ai_sr}"),
                                ]:
                                    if st.session_state.get(role_key, False):
                                        user_roles.append(role_name)

                                if not user_roles:
                                    ai_validation_errors.append(f"User-{i} ({env_label}): At least one AI role must be selected.")
                                    continue

                                user_schema_roles = [r for r in user_roles if r != "Copilot access"]
                                user_has_copilot = "Copilot access" in user_roles

                                user_schemas = []
                                for key, val in st.session_state.items():
                                    if key.startswith(f"ai_diff_schema_{i}_{env_code}_") and key.endswith(f"_{ai_sr}") and val is True:
                                        schema_name = key[len(f"ai_diff_schema_{i}_{env_code}_"):-(len(str(ai_sr)) + 1)]
                                        user_schemas.append(schema_name)

                                if user_schema_roles and not user_schemas:
                                    ai_validation_errors.append(f"User-{i} ({env_label}): At least one schema must be selected for non-Copilot roles.")
                                    continue

                                if user_has_copilot:
                                    ai_rows_to_insert.append((email, "Copilot access", env_label, None))
                                for role_label in user_schema_roles:
                                    for schema_name in user_schemas:
                                        ai_rows_to_insert.append((email, role_label, env_label, schema_name))

                    if ai_validation_errors:
                        for err in ai_validation_errors:
                            st.error(err)
                    else:
                        if ai_rows_to_insert:
                            session = conn.session()
                            for user_email, request_type_val, env_label, schema_val in ai_rows_to_insert:
                                schema_sql = f"'{schema_val}'" if schema_val else "NULL"
                                session.sql(
                                    f"""INSERT INTO META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST
                                        (TENANT, SUBTENANT, PROJECT, REQUEST_TYPE, "USER", ENVIRONMENT, SCHEMA, OBJECTS, OBJECT_NAMES)
                                        VALUES ('{t_val}', '{s_val}', '{p_val}', '{request_type_val}', '{user_email}', '{env_label}', {schema_sql}, NULL, NULL)"""
                                ).collect()
                            st.session_state["show_success"] = True
                            st.session_state["ai_reset"] += 1
                            st.rerun()
                        else:
                            st.warning("No entries to submit. Please check your selections.")

                if st.button("Display", key="ai_display"):
                    display_df = conn.query("SELECT * FROM META_DATA_DB.TABLES_SCHEMA.ACCESS_REQUEST")
                    if not display_df.empty:
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.info("No records found in ACCESS_REQUEST table.")
