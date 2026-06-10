import os
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

st.title("Tenant Projects")

request_type = st.radio("Request Type", ["Generic Access Request", "Specific Database Object Access"], horizontal=True)

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
                    num_users = st.selectbox("Number of users needed access", list(range(1, 11)))
                    role_combinations = ["Read", "Read/Write", "Read/Write/Create"]
                    for i in range(1, num_users + 1):
                        st.text_input(f"User-{i} Email", key=f"user_email_{i}")
                        st.write("**Roles Needed**")
                        role_cols = st.columns(len(role_combinations))
                        for idx, role in enumerate(role_combinations):
                            with role_cols[idx]:
                                st.checkbox(role, key=f"user_{i}_role_{role}")
                    if project_name:
                        st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {project_name}")
                else:
                    num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key="existing_num_users")
                    role_combinations = ["Read", "Read/Write", "Read/Write/Create"]
                    for i in range(1, num_users + 1):
                        st.text_input(f"User-{i} Email", key=f"existing_user_email_{i}")
                        st.write("**Roles Needed**")
                        role_cols = st.columns(len(role_combinations))
                        for idx, role in enumerate(role_combinations):
                            with role_cols[idx]:
                                st.checkbox(role, key=f"existing_user_{i}_role_{role}")
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

    num_users = st.selectbox("Number of users needed access", list(range(1, 11)), key="sdo_num_users")
    role_combinations = ["Read", "Read/Write", "Read/Write/Create"]
    for i in range(1, num_users + 1):
        st.text_input(f"User-{i} Email", key=f"sdo_user_email_{i}")
        st.write("**Roles Needed**")
        role_cols = st.columns(len(role_combinations))
        for idx, role in enumerate(role_combinations):
            with role_cols[idx]:
                st.checkbox(role, key=f"sdo_user_{i}_role_{role}")

    st.subheader("Environment to which access is needed")

    import re
    tenant_abbr = re.search(r'\[(.+?)\]', selected_tenant)
    subtenant_abbr = re.search(r'\[(.+?)\]', selected_subtenant)
    tenant_code = tenant_abbr.group(1) if tenant_abbr else selected_tenant
    subtenant_code = subtenant_abbr.group(1) if subtenant_abbr else selected_subtenant

    if "selected_schemas_sdo" not in st.session_state or not isinstance(st.session_state.selected_schemas_sdo, dict):
        st.session_state.selected_schemas_sdo = {}

    environments = [("Dev", "DEV"), ("SIT", "SIT"), ("ST", "ST"), ("UAT", "UAT"), ("PreProd", "PREPROD"), ("Prod", "PROD")]

    for env_label, env_code in environments:
        env_checked = st.checkbox(env_label, key=f"sdo_env_{env_code}")
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
                    all_selected = st.checkbox("All Schemas", key=f"sdo_all_{env_code}")
                    individual_selections = {}
                    if not all_selected:
                        for schema in schema_list:
                            individual_selections[schema] = st.checkbox(schema, key=f"sdo_add_{env_code}_{schema}")

                with right_col:
                    st.write(f"**Selected Schemas ({env_label})**")
                    if all_selected:
                        st.write("✓ All Schemas")
                    else:
                        for schema, checked in individual_selections.items():
                            if checked:
                                st.write(f"✓ {schema}")
