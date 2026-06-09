import os
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

st.title("Tenant Projects")

@st.cache_data
def load_data():
    df = conn.query("SELECT TENANT, SUBTENANT, PROJECT FROM META_DATA_DB.TABLES_SCHEMA.TENANT_PROJECTS")
    return df

df = load_data()

tenants = sorted(df["TENANT"].unique()) + ["New"]
selected_tenant = st.selectbox("Select Tenant", tenants)

if selected_tenant == "New":
    tenant_name = st.text_input("Enter Tenant Name")
    subtenant_name = st.text_input("Enter Subtenant Name")
    project_name = st.text_input("Enter Project Name")
    if tenant_name and subtenant_name and project_name:
        st.success(f"Selected: {tenant_name} → {subtenant_name} → {project_name}")
else:
    filtered_by_tenant = df[df["TENANT"] == selected_tenant]
    subtenants = sorted(filtered_by_tenant["SUBTENANT"].unique()) + ["New"]
    selected_subtenant = st.selectbox("Select Subtenant", subtenants)

    if selected_subtenant == "New":
        subtenant_name = st.text_input("Enter Subtenant Name")
        project_name = st.text_input("Enter Project Name")
        if subtenant_name and project_name:
            st.success(f"Selected: {selected_tenant} → {subtenant_name} → {project_name}")
    else:
        filtered_by_subtenant = filtered_by_tenant[filtered_by_tenant["SUBTENANT"] == selected_subtenant]
        projects = sorted(filtered_by_subtenant["PROJECT"].unique()) + ["New"]
        selected_project = st.selectbox("Select Project", projects)

        if selected_project == "New":
            project_name = st.text_input("Enter Project Name")
            if project_name:
                st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {project_name}")
        else:
            st.success(f"Selected: {selected_tenant} → {selected_subtenant} → {selected_project}")
