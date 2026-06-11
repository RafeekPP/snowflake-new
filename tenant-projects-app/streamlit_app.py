import os
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

st.title("Tenant Projects")

request_type = st.radio("Request Type", ["Generic Access Request", "Specific Database Object Access", "AI Users Roles"], horizontal=True)

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
</style>
""", unsafe_allow_html=True)

def load_data():
    df = conn.query("SELECT TENANT, SUBTENANT, PROJECT FROM META_DATA_DB.TABLES_SCHEMA.TENANT_PROJECTS")
    return df

df = load_data()

if request_type == "Generic Access Request":
    mirrored_access = st.radio("Mirrored access of existing user", ["Yes", "No"], horizontal=True)
    if mirrored_access == "Yes":
        mirror_username = st.text_input("Provide the username to be mirrored")
    else:
        tenants = sorted(df["TENANT"].unique()) + ["New"]
        selected_subtenant = None
        selected_project = None

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_tenant = st.selectbox("Select Tenant", tenants)

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
                selected_subtenant = st.selectbox("Select Subtenant", subtenants)

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
                    selected_project = st.selectbox("Select Project", projects)

                if selected_project == "New":
                    project_name = st.text_input("Enter Project Name")
                    schema_name = st.text_input("Schemas to be created")
                    if project_name:
                        st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {project_name}")
                else:
                    st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {selected_project}")

        st.subheader("Environment to which access is needed")

        show_schema_panes = (selected_tenant != "New"
            and selected_subtenant is not None and selected_subtenant != "New"
            and selected_project is not None and selected_project != "New")

        if show_schema_panes:
            import re
            tenant_abbr = re.search(r'\[(.+?)\]', selected_tenant)
            subtenant_abbr = re.search(r'\[(.+?)\]', selected_subtenant)
            tenant_code = tenant_abbr.group(1) if tenant_abbr else selected_tenant
            subtenant_code = subtenant_abbr.group(1) if subtenant_abbr else selected_subtenant

            if "selected_schemas" not in st.session_state or not isinstance(st.session_state.selected_schemas, dict):
                st.session_state.selected_schemas = {}

            environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

            for env_label, env_code in environments:
                env_checked = st.checkbox(env_label, key=f"env_{env_code}")
                if env_checked:
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
                        left_col, right_col = st.columns(2)

                        with left_col:
                            st.write(f"**Available Schemas ({env_label})**")
                            all_selected = st.checkbox("All Schemas", key=f"all_{env_code}")
                            individual_selections = {}
                            if not all_selected:
                                for schema in schema_list:
                                    individual_selections[schema] = st.checkbox(schema, key=f"add_{env_code}_{schema}")

                        with right_col:
                            st.write(f"**Selected Schemas ({env_label})**")
                            if all_selected:
                                st.write("✓ All Schemas")
                            else:
                                for schema, checked in individual_selections.items():
                                    if checked:
                                        st.write(f"✓ {schema}")
        else:
            env_dev = st.checkbox("Dev")
            env_sit = st.checkbox("SIT")
            env_st = st.checkbox("ST")
            env_uat = st.checkbox("UAT")
            env_preprod = st.checkbox("PreProd")
            env_prod = st.checkbox("Prod")

        num_dop = st.selectbox("Number of users needed access [DOP Role]", list(range(0, 11)), key="num_dop")
        for i in range(1, num_dop + 1):
            st.text_input(f"DOP User-{i} Email", key=f"dop_user_email_{i}")

        num_etl = st.selectbox("Number of users needed access [ETL Role]", list(range(0, 11)), key="num_etl")
        for i in range(1, num_etl + 1):
            st.text_input(f"ETL User-{i} Email", key=f"etl_user_email_{i}")

        num_rpt = st.selectbox("Number of users needed access [RPT Role]", list(range(0, 11)), key="num_rpt")
        for i in range(1, num_rpt + 1):
            st.text_input(f"RPT User-{i} Email", key=f"rpt_user_email_{i}")
elif request_type == "Specific Database Object Access":
    mirrored_access_sdo = st.radio("Mirrored access of existing user", ["Yes", "No"], horizontal=True, key="sdo_mirrored")
    if mirrored_access_sdo == "Yes":
        mirror_username_sdo = st.text_input("Provide the username to be mirrored", key="sdo_mirror_username")
    else:
        tenants = sorted(df["TENANT"].unique())
        selected_subtenant = None
        selected_project = None

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_tenant = st.selectbox("Select Tenant", tenants, key="sdo_tenant")

        filtered_by_tenant = df[df["TENANT"] == selected_tenant]
        subtenants = sorted(filtered_by_tenant["SUBTENANT"].unique())
        with col2:
            selected_subtenant = st.selectbox("Select Subtenant", subtenants, key="sdo_subtenant")

        filtered_by_subtenant = filtered_by_tenant[filtered_by_tenant["SUBTENANT"] == selected_subtenant]
        projects = sorted(filtered_by_subtenant["PROJECT"].unique())
        with col3:
            selected_project = st.selectbox("Select Project", projects, key="sdo_project")

        import re
        tenant_abbr = re.search(r'\[(.+?)\]', selected_tenant)
        subtenant_abbr = re.search(r'\[(.+?)\]', selected_subtenant)
        tenant_code = tenant_abbr.group(1) if tenant_abbr else selected_tenant
        subtenant_code = subtenant_abbr.group(1) if subtenant_abbr else selected_subtenant

        if "selected_schemas_sdo" not in st.session_state or not isinstance(st.session_state.selected_schemas_sdo, dict):
            st.session_state.selected_schemas_sdo = {}

        access_mode = st.radio("Access Mode", ["All Users need same access", "Users need different access"], horizontal=True, key="sdo_access_mode")

        environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

        if access_mode == "All Users need same access":
            st.subheader("Environment to which access is needed")

            selected_envs = []
            env_cols = st.columns(len(environments))
            for idx, (env_label, env_code) in enumerate(environments):
                with env_cols[idx]:
                    env_checked = st.checkbox(env_label, key=f"sdo_env_{env_code}")
                if env_checked:
                    selected_envs.append((env_label, env_code))

            if selected_envs:
                role_combinations = ["Read", "Read/Write", "Read/Write/Create"]
                selected_role = st.radio("Select role", role_combinations, horizontal=True, key="sdo_role_select")
                num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key="sdo_num_users")
                for i in range(1, num_users + 1):
                    st.text_input(f"User-{i} Email", key=f"sdo_user_email_{i}")

                st.subheader("Select Object Types")
                obj_col1, obj_col2, obj_col3, obj_col4, obj_col5 = st.columns(5)
                with obj_col1:
                    obj_tables = st.checkbox("Tables", key="sdo_obj_Tables")
                with obj_col2:
                    obj_functions = st.checkbox("Functions", key="sdo_obj_Functions")
                with obj_col3:
                    obj_procedures = st.checkbox("Procedures", key="sdo_obj_Procedures")
                with obj_col4:
                    obj_views = st.checkbox("Views", key="sdo_obj_Views")
                with obj_col5:
                    obj_stages = st.checkbox("Stages", key="sdo_obj_Stages")

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
                        except Exception:
                            schema_list = []

                        if schema_list:
                            st.write("**Schema List**")
                            individual_selections = {}
                            for schema in schema_list:
                                individual_selections[schema] = st.checkbox(schema, key=f"sdo_add_{env_code}_{schema}")

                            chosen_schemas = [s for s, c in individual_selections.items() if c]

                            for chosen_schema in chosen_schemas:
                                for obj_type in selected_obj_types:
                                    if obj_type == "Tables":
                                        query = f"SELECT TABLE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{chosen_schema.split('.')[1]}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                    elif obj_type == "Views":
                                        query = f"SELECT TABLE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{chosen_schema.split('.')[1]}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                    elif obj_type == "Functions":
                                        query = f"SELECT FUNCTION_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{chosen_schema.split('.')[1]}' ORDER BY FUNCTION_NAME"
                                    elif obj_type == "Procedures":
                                        query = f"SELECT PROCEDURE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{chosen_schema.split('.')[1]}' ORDER BY PROCEDURE_NAME"
                                    elif obj_type == "Stages":
                                        query = f"SHOW STAGES IN {chosen_schema}"

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
                                        state_key = f"sdo_selected_{env_code}_{chosen_schema}_{obj_type}"
                                        if state_key not in st.session_state:
                                            st.session_state[state_key] = []

                                        available = [o for o in obj_names if o not in st.session_state[state_key]]
                                        obj_left, obj_right = st.columns(2)

                                        with obj_left:
                                            st.write(f"**Available {obj_type.lower()} in {chosen_schema}**")
                                            for obj_name in available:
                                                if st.button(f"➡ {obj_name}", key=f"sdo_add_{env_code}_{chosen_schema}_{obj_type}_{obj_name}"):
                                                    st.session_state[state_key].append(obj_name)
                                                    st.rerun()

                                        with obj_right:
                                            st.write(f"**Selected {obj_type.lower()}**")
                                            for obj_name in st.session_state[state_key]:
                                                if st.button(f"⬅ {obj_name}", key=f"sdo_rem_{env_code}_{chosen_schema}_{obj_type}_{obj_name}"):
                                                    st.session_state[state_key].remove(obj_name)
                                                    st.rerun()
        else:
            num_users_diff = st.selectbox("Number of users needed access", list(range(1, 11)), key="sdo_diff_num_users")

            for i in range(1, num_users_diff + 1):
                col_email, col_role = st.columns([2, 3])
                with col_email:
                    st.text_input(f"User-{i} Email", key=f"sdo_diff_user_email_{i}")
                with col_role:
                    st.radio("Role", ["Read", "Read/Write", "Read/Write/Create"], horizontal=True, key=f"sdo_diff_role_{i}")
                env_cols = st.columns(len(environments))
                user_selected_envs = []
                for idx, (env_label, env_code) in enumerate(environments):
                    with env_cols[idx]:
                        if st.checkbox(env_label, key=f"sdo_diff_env_{i}_{env_code}"):
                            user_selected_envs.append((env_label, env_code))

                for env_label, env_code in user_selected_envs:
                    st.write(f"**{env_label}-Objects-User{i}**")
                    obj_row = st.columns(5)
                    obj_selections = {}
                    with obj_row[0]:
                        obj_selections["Tables"] = st.checkbox("Tables", key=f"sdo_diff_obj_{i}_{env_code}_Tables")
                    with obj_row[1]:
                        obj_selections["Functions"] = st.checkbox("Functions", key=f"sdo_diff_obj_{i}_{env_code}_Functions")
                    with obj_row[2]:
                        obj_selections["Procedures"] = st.checkbox("Procedures", key=f"sdo_diff_obj_{i}_{env_code}_Procedures")
                    with obj_row[3]:
                        obj_selections["Views"] = st.checkbox("Views", key=f"sdo_diff_obj_{i}_{env_code}_Views")
                    with obj_row[4]:
                        obj_selections["Stages"] = st.checkbox("Stages", key=f"sdo_diff_obj_{i}_{env_code}_Stages")

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
                            individual_selections = {}
                            for schema in schema_list:
                                individual_selections[schema] = st.checkbox(schema, key=f"sdo_diff_schema_{i}_{env_code}_{schema}")

                            chosen_schemas = [s for s, c in individual_selections.items() if c]

                            for chosen_schema in chosen_schemas:
                                for obj_type in selected_obj_types:
                                    if obj_type == "Tables":
                                        query = f"SELECT TABLE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{chosen_schema.split('.')[1]}' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                                    elif obj_type == "Views":
                                        query = f"SELECT TABLE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{chosen_schema.split('.')[1]}' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME"
                                    elif obj_type == "Functions":
                                        query = f"SELECT FUNCTION_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.FUNCTIONS WHERE FUNCTION_SCHEMA = '{chosen_schema.split('.')[1]}' ORDER BY FUNCTION_NAME"
                                    elif obj_type == "Procedures":
                                        query = f"SELECT PROCEDURE_NAME FROM {chosen_schema.split('.')[0]}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = '{chosen_schema.split('.')[1]}' ORDER BY PROCEDURE_NAME"
                                    elif obj_type == "Stages":
                                        query = f"SHOW STAGES IN {chosen_schema}"

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
                                        state_key = f"sdo_diff_selected_{i}_{env_code}_{chosen_schema}_{obj_type}"
                                        if state_key not in st.session_state:
                                            st.session_state[state_key] = []

                                        available = [o for o in obj_names if o not in st.session_state[state_key]]
                                        obj_left, obj_right = st.columns(2)

                                        with obj_left:
                                            st.write(f"**Available {obj_type.lower()} in {chosen_schema}**")
                                            for obj_name in available:
                                                if st.button(f"➡ {obj_name}", key=f"sdo_diff_add_{i}_{env_code}_{chosen_schema}_{obj_type}_{obj_name}"):
                                                    st.session_state[state_key].append(obj_name)
                                                    st.rerun()

                                        with obj_right:
                                            st.write(f"**Selected {obj_type.lower()}**")
                                            for obj_name in st.session_state[state_key]:
                                                if st.button(f"⬅ {obj_name}", key=f"sdo_diff_rem_{i}_{env_code}_{chosen_schema}_{obj_type}_{obj_name}"):
                                                    st.session_state[state_key].remove(obj_name)
                                                    st.rerun()
else:
    st.subheader("AI Users & Roles")
    st.info("This section is under construction.")
