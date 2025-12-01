# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import uuid

st.set_page_config(page_title="Real Estate Team Task Manager", layout="wide")

# ----- Helper functions -----
def make_task_row(task_id=None, title="", type_="", assignee="", status="Backlog", due=None, notes="", pipeline_stage="Backlog", created=None, extra=None):
    return {
        "task_id": task_id or str(uuid.uuid4()),
        "title": title,
        "type": type_,
        "assignee": assignee,
        "status": status,
        "due": due,
        "notes": notes,
        "pipeline_stage": pipeline_stage,
        "created": created or datetime.now().isoformat(),
        "extra": extra or {}
    }

def load_demo_tasks():
    tasks = []
    core_tasks = [
        "Cold Calling New Leads",
        "Appointment Booking & Calendar Management",
        "Marketing Content Creation (Posts, Reels, Ads)",
        "VOPs Email Tracker Management",
        "Lead Follow-Up (1–7 Day Sequences)",
        "Open House Scheduling & Coordination",
        "Property Showing Coordination",
        "CRM Data Entry & Updating",
        "Buyer Intake Screening",
        "Seller Intake Screening",
        "Running CMAs (Comparative Market Analysis)",
        "Creating & Completing BPOs (Broker Price Opinions)",
        "Weekly Market Update Reports",
        "Social Media Posting & Engagement (Daily)",
        "Listing Description Writing & Editing",
        "Photo / Video Shoot Scheduling for Listings",
        "Transaction Coordination Support",
        "Document Collection & Verification",
        "Pipeline Tracking (Active, Warm, Hot Leads)",
        "Appointment Reminder Texts & Emails",
        "Creating Buyer/Seller Guides & Material",
        "Email Marketing Campaign Setup",
        "Google Business Profile Updates & Reviews Follow-Up",
        "Neighborhood Farming & Outreach Tasks",
        "Weekly Team Reports & Analytics",
        "Expired & FSBO Outreach"
    ]
    for t in core_tasks:
        tasks.append(make_task_row(title=t, type_="Operational", assignee="", status="Backlog"))
    return pd.DataFrame(tasks)

def df_to_display(df):
    # Flatten extra for display
    display = df.copy()
    display["due"] = display["due"].fillna("")
    display["created"] = display["created"].apply(lambda x: x.split("T")[0] if pd.notna(x) else "")
    display["assignee"] = display["assignee"].fillna("")
    display["notes"] = display["notes"].fillna("")
    display["type"] = display["type"].fillna("")
    display["pipeline_stage"] = display["pipeline_stage"].fillna("")
    return display[["task_id","title","type","assignee","status","pipeline_stage","due","created","notes"]]

def save_session_df(df):
    st.session_state["tasks_df"] = df

# ----- Initialize session state -----
if "tasks_df" not in st.session_state:
    st.session_state["tasks_df"] = load_demo_tasks()

if "call_log" not in st.session_state:
    st.session_state["call_log"] = pd.DataFrame(columns=["call_id","lead_name","phone","agent","datetime","outcome","notes"])

if "bpo_df" not in st.session_state:
    st.session_state["bpo_df"] = pd.DataFrame(columns=["bpo_id","property_address","estimated_value","comps_summary","agent","date","notes"])

if "vop_df" not in st.session_state:
    st.session_state["vop_df"] = pd.DataFrame(columns=["vop_id","email_subject","recipient","sent_date","status","notes"])

# ----- Layout -----
st.title("🧭 Real Estate Team — Task Manager & Operations")
col1, col2 = st.columns([3,1])

with col2:
    st.markdown("### Quick Controls")
    if st.button("Reset to Demo Tasks"):
        st.session_state["tasks_df"] = load_demo_tasks()
        st.success("Demo tasks reloaded.")
    uploaded = st.file_uploader("Import tasks CSV", type=["csv","xlsx"])
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df_in = pd.read_csv(uploaded)
            else:
                df_in = pd.read_excel(uploaded)
            # Expect columns similar to display; convert to app format
            loaded = []
            for _, r in df_in.iterrows():
                loaded.append(make_task_row(task_id=r.get("task_id", None),
                                            title=r.get("title",""),
                                            type_=r.get("type",""),
                                            assignee=r.get("assignee",""),
                                            status=r.get("status","Backlog"),
                                            due=r.get("due", None),
                                            notes=r.get("notes",""),
                                            pipeline_stage=r.get("pipeline_stage","")))
            st.session_state["tasks_df"] = pd.DataFrame(loaded)
            st.success("Imported tasks.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.download_button("Export tasks CSV", df_to_display(st.session_state["tasks_df"]).to_csv(index=False), file_name="tasks_export.csv")

    st.markdown("---")
    st.markdown("### Create Quick Task")
    with st.form("quick_task"):
        q_title = st.text_input("Task title")
        q_assignee = st.text_input("Assignee")
        q_type = st.selectbox("Type", ["Operational","Marketing","Sales","Admin","Other"])
        q_due = st.date_input("Due date", value=None)
        q_notes = st.text_area("Notes", max_chars=400)
        submitted = st.form_submit_button("Create Task")
        if submitted:
            df = st.session_state["tasks_df"]
            new = make_task_row(title=q_title, assignee=q_assignee, type_=q_type, due=q_due.isoformat() if q_due else None)
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_session_df(df)
            st.success("Task created.")

# ----- Main area: Tabs -----
tabs = st.tabs(["Dashboard","Tasks Board","Cold Calls","BPOs","VOPs Email Tracker","Reports & Exports","Settings"])

# ----- Dashboard Tab -----
with tabs[0]:
    st.header("Team Dashboard")
    df = st.session_state["tasks_df"]
    st.metric("Total Tasks", len(df))
    st.metric("Backlog", len(df[df["status"]=="Backlog"]))
    st.metric("In Progress", len(df[df["status"]=="In Progress"]))
    st.metric("Completed", len(df[df["status"]=="Completed"]))

    st.subheader("Pipeline Snapshot")
    pipeline_counts = df["pipeline_stage"].value_counts().to_dict()
    st.write(pipeline_counts)

    st.subheader("Quick Filters")
    f_assignee = st.selectbox("Filter by assignee", options=["All"] + sorted(df["assignee"].dropna().unique().tolist()))
    f_status = st.selectbox("Filter by status", options=["All","Backlog","In Progress","Completed","On Hold","Cancelled"])
    tmp = df.copy()
    if f_assignee != "All":
        tmp = tmp[tmp["assignee"]==f_assignee]
    if f_status != "All":
        tmp = tmp[tmp["status"]==f_status]
    st.dataframe(df_to_display(tmp), height=320)

# ----- Tasks Board Tab -----
with tabs[1]:
    st.header("Tasks Board")
    df = st.session_state["tasks_df"]

    st.markdown("**Search / Filter**")
    query = st.text_input("Search titles or notes")
    type_filter = st.selectbox("Type", options=["All"] + sorted(df["type"].dropna().unique().tolist()))
    assignee_filter = st.selectbox("Assignee", options=["All"] + sorted(df["assignee"].fillna("").unique().tolist()))
    if query:
        df = df[df["title"].str.contains(query, case=False, na=False) | df["notes"].str.contains(query, case=False, na=False)]
    if type_filter != "All":
        df = df[df["type"]==type_filter]
    if assignee_filter != "All":
        df = df[df["assignee"]==assignee_filter]

    st.dataframe(df_to_display(df), height=400)

    st.markdown("**Edit / Update Task**")
    with st.form("edit_task_form"):
        edit_id = st.selectbox("Select task to edit", options=[""] + df["task_id"].tolist())
        if edit_id:
            row = df[df["task_id"]==edit_id].iloc[0]
            e_title = st.text_input("Title", value=row["title"])
            e_type = st.selectbox("Type", ["Operational","Marketing","Sales","Admin","Other"], index=0)
            e_assignee = st.text_input("Assignee", value=row["assignee"])
            e_status = st.selectbox("Status", ["Backlog","In Progress","Completed","On Hold","Cancelled"], index=["Backlog","In Progress","Completed","On Hold","Cancelled"].index(row.get("status","Backlog")))
            e_pipeline = st.selectbox("Pipeline Stage", ["Backlog","Lead","Contacted","Appointment","Offer","Under Contract","Closed"], index=["Backlog","Lead","Contacted","Appointment","Offer","Under Contract","Closed"].index(row.get("pipeline_stage","Backlog")))
            e_due = st.date_input("Due date", value=(pd.to_datetime(row["due"]).date() if pd.notna(row["due"]) and row["due"]!="" else date.today()))
            e_notes = st.text_area("Notes", value=row["notes"])
            updated = st.form_submit_button("Update Task")
            if updated:
                df_idx = st.session_state["tasks_df"].index[st.session_state["tasks_df"]["task_id"]==edit_id].tolist()[0]
                st.session_state["tasks_df"].at[df_idx,"title"] = e_title
                st.session_state["tasks_df"].at[df_idx,"type"] = e_type
                st.session_state["tasks_df"].at[df_idx,"assignee"] = e_assignee
                st.session_state["tasks_df"].at[df_idx,"status"] = e_status
                st.session_state["tasks_df"].at[df_idx,"pipeline_stage"] = e_pipeline
                st.session_state["tasks_df"].at[df_idx,"due"] = e_due.isoformat()
                st.session_state["tasks_df"].at[df_idx,"notes"] = e_notes
                st.success("Task updated.")

    st.markdown("**Bulk actions**")
    with st.form("bulk_actions"):
        selected_ids = st.multiselect("Select tasks (by ID)", options=df["task_id"].tolist())
        bulk_action = st.selectbox("Action", ["Set status to In Progress","Set status to Completed","Assign to...","Delete selected"])
        assign_to = st.text_input("Assign to (if applicable)")
        do_bulk = st.form_submit_button("Apply")
        if do_bulk:
            if not selected_ids:
                st.warning("No tasks selected.")
            else:
                for tid in selected_ids:
                    idx_list = st.session_state["tasks_df"].index[st.session_state["tasks_df"]["task_id"]==tid].tolist()
                    if not idx_list:
                        continue
                    idx = idx_list[0]
                    if bulk_action=="Set status to In Progress":
                        st.session_state["tasks_df"].at[idx,"status"] = "In Progress"
                    elif bulk_action=="Set status to Completed":
                        st.session_state["tasks_df"].at[idx,"status"] = "Completed"
                    elif bulk_action=="Assign to...":
                        st.session_state["tasks_df"].at[idx,"assignee"] = assign_to
                    elif bulk_action=="Delete selected":
                        st.session_state["tasks_df"].drop(index=idx, inplace=True)
                st.session_state["tasks_df"].reset_index(drop=True, inplace=True)
                st.success("Bulk action applied.")

# ----- Cold Calls Tab -----
with tabs[2]:
    st.header("Cold Call Log")
    with st.expander("Log a new cold call"):
        with st.form("call_form"):
            lead_name = st.text_input("Lead name")
            phone = st.text_input("Phone")
            agent = st.text_input("Agent")
            call_dt = st.datetime_input("Call date & time", value=datetime.now())
            outcome = st.selectbox("Outcome", ["No answer","Left voicemail","Spoke - interested","Spoke - not interested","Callback later"])
            call_notes = st.text_area("Notes")
            call_submit = st.form_submit_button("Save call")
            if call_submit:
                row = {
                    "call_id": str(uuid.uuid4()),
                    "lead_name": lead_name,
                    "phone": phone,
                    "agent": agent,
                    "datetime": call_dt.isoformat(),
                    "outcome": outcome,
                    "notes": call_notes
                }
                st.session_state["call_log"] = pd.concat([st.session_state["call_log"], pd.DataFrame([row])], ignore_index=True)
                st.success("Call logged.")

    st.subheader("Call History")
    st.dataframe(st.session_state["call_log"].sort_values("datetime", ascending=False), height=300)
    st.download_button("Export call log CSV", st.session_state["call_log"].to_csv(index=False), file_name="call_log.csv")

# ----- BPOs Tab -----
with tabs[3]:
    st.header("Broker Price Opinions (BPOs)")
    st.markdown("Create and track BPOs for properties.")
    with st.form("bpo_form"):
        prop_addr = st.text_input("Property address")
        est_value = st.number_input("Estimated value ($)", min_value=0, step=1000.0, format="%.2f")
        comps = st.text_area("Comps summary (short)")
        bpo_agent = st.text_input("Agent completing BPO")
        bpo_date = st.date_input("Date", value=date.today())
        bpo_notes = st.text_area("Notes")
        bpo_save = st.form_submit_button("Save BPO")
        if bpo_save:
            bpo_row = {
                "bpo_id": str(uuid.uuid4()),
                "property_address": prop_addr,
                "estimated_value": est_value,
                "comps_summary": comps,
                "agent": bpo_agent,
                "date": bpo_date.isoformat(),
                "notes": bpo_notes
            }
            st.session_state["bpo_df"] = pd.concat([st.session_state["bpo_df"], pd.DataFrame([bpo_row])], ignore_index=True)
            st.success("BPO saved.")

    st.subheader("BPO Records")
    st.dataframe(st.session_state["bpo_df"].sort_values("date", ascending=False), height=300)
    st.download_button("Export BPOs CSV", st.session_state["bpo_df"].to_csv(index=False), file_name="bpos.csv")

# ----- VOPs Email Tracker Tab -----
with tabs[4]:
    st.header("VOPs Email Tracker")
    st.markdown("Track emails sent to verify owner/occupants (VOPs) or other verification emails.")
    with st.form("vop_form"):
        subj = st.text_input("Email subject")
        recipient = st.text_input("Recipient")
        sent_date = st.date_input("Sent date", value=date.today())
        vop_status = st.selectbox("Status", ["Sent","Delivered","Opened","Click","Bounced","Unverified"])
        vop_notes = st.text_area("Notes")
        vop_save = st.form_submit_button("Save Email Record")
        if vop_save:
            vop_row = {
                "vop_id": str(uuid.uuid4()),
                "email_subject": subj,
                "recipient": recipient,
                "sent_date": sent_date.isoformat(),
                "status": vop_status,
                "notes": vop_notes
            }
            st.session_state["vop_df"] = pd.concat([st.session_state["vop_df"], pd.DataFrame([vop_row])], ignore_index=True)
            st.success("VOP record saved.")

    st.subheader("Email Records")
    st.dataframe(st.session_state["vop_df"].sort_values("sent_date", ascending=False), height=300)
    st.download_button("Export VOPs CSV", st.session_state["vop_df"].to_csv(index=False), file_name="vops_emails.csv")

# ----- Reports & Exports -----
with tabs[5]:
    st.header("Reports & Exports")
    df = st.session_state["tasks_df"]
    st.subheader("Tasks by Assignee")
    try:
        tb = df.groupby("assignee").size().reset_index(name="count").sort_values("count", ascending=False)
        st.table(tb)
    except Exception:
        st.write("No assignees yet.")

    st.subheader("Pipeline stages")
    pipeline = df["pipeline_stage"].value_counts().reset_index()
    pipeline.columns = ["stage","count"]
    st.table(pipeline)

    st.markdown("### Export everything")
    st.download_button("Export tasks CSV", df_to_display(df).to_csv(index=False), file_name="all_tasks.csv")
    st.download_button("Export all data (ZIP-style CSVs)", 
                       data=(df_to_display(df).to_csv(index=False) + "\n\n\n" + st.session_state["call_log"].to_csv(index=False) + "\n\n\n" + st.session_state["bpo_df"].to_csv(index=False) + "\n\n\n" + st.session_state["vop_df"].to_csv(index=False)),
                       file_name="all_data_bundle.csv")

# ----- Settings Tab -----
with tabs[6]:
    st.header("Settings & Roles")
    st.markdown("Define team roles and quick SOP links.")
    if "roles" not in st.session_state:
        st.session_state["roles"] = {"Admin": ["manage_tasks","export"], "Agent": ["manage_own_tasks"], "VA": ["create_tasks"]}

    st.json(st.session_state["roles"])
    with st.form("roles_form"):
        new_role = st.text_input("New role name")
        perms = st.text_area("Permissions (comma separated)")
        add_role = st.form_submit_button("Add role")
        if add_role and new_role:
            st.session_state["roles"][new_role] = [p.strip() for p in perms.split(",") if p.strip()]
            st.success("Role added.")

# ----- Footer -----
st.markdown("---")
st.markdown("Built for real estate operations — features: Cold calls, Appointment booking, Marketing tasks, VOPs email tracking, BPOs, pipeline stages, import/export, and quick reporting.")

