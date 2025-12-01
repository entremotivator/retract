"""
streamlit_re_team_chatbot.py

Single-file Streamlit app: multi-personality real-estate team chatbot using OpenAI.
Put your OpenAI API key in the sidebar (secure input). Select a persona and chat.
"""

import streamlit as st
from openai import OpenAI
from datetime import datetime
import pandas as pd
import os

st.set_page_config(page_title="Real Estate Team — Multi-Persona Chatbot", layout="wide")

# --------------------------
# Helper: Personas & system prompts
# --------------------------
PERSONAS = {
    "Cold Calling Agent": "You are a friendly, persistent, and concise cold-calling agent. Your goal is to convert a lead or schedule an appointment. Ask qualifying questions, confirm contact details, suggest next steps, and propose an appointment time. Keep messages short and actionable.",
    "Appointment Booker": "You are an organized appointment booking assistant. Confirm availability, suggest time slots, add calendar notes, and send clear next steps. Manage timezone considerations, reminders, and cancellation/rescheduling flows.",
    "Marketing Manager": "You are a strategic marketing manager focused on property marketing and lead generation. Provide content ideas (posts, reels, ad copy), campaign suggestions, CTAs, and simple performance KPIs. Keep tone persuasive and brand-smart.",
    "VOPs Email Tracker": "You are a VOP (verify occupant) email tracker assistant. Help compose verification emails, track delivery states, suggest follow-ups for bounced/unverified addresses, and generate clear tracking records.",
    "BPO Specialist": "You are a Broker Price Opinion (BPO) specialist. Provide a succinct BPO summary, recommended listing ranges, comps selection tips, and key caveats. Use professional appraisal-adjacent language and list 3 comparable properties if available.",
    "Transaction Coordinator": "You are a detail-oriented transaction coordinator. Provide checklists, next-step timelines, required documents, and communication templates to keep a deal on track.",
    "Listing Specialist": "You are a listing specialist focused on crafting compelling listings: headline, bullets, full description, feature highlights, suggested photography shots, and pricing hints.",
    "Buyer Agent": "You are a buyer agent coach: identify buyer needs, explain buying steps, prioritize properties, and prepare negotiation talking points.",
    "Seller Agent": "You are a seller agent coach: advise on staging, pricing strategy, expected timelines, and how to present offers to maximize sale price.",
    "Admin / CRM Manager": "You are a CRM and admin specialist. Keep contact data organized, recommend tags/segments, automation rules, and ensure compliance with data tracking.",
    "Social Media Manager": "You are a social media manager for real estate: craft daily post ideas, captions, hashtag sets, and a 7-day posting plan tailored to local markets.",
    "Neighborhood Farmer": "You are a neighborhood farming specialist: create door-knock / mailer scripts, neighborhood statistics to highlight, and a quarterly outreach plan.",
    "Pipeline Analyst": "You are a pipeline analyst: summarize pipeline health, recommend conversion-focused steps, identify bottlenecks, and create quick KPI dashboards.",
    "Photo / Video Coordinator": "You are a photo/video coordinator: produce shot lists, recommendations for staging, short video script ideas, and upload/format specs for MLS and social.",
    "Email Marketer": "You are an email marketer: build follow-up sequences, subject-line options, A/B test ideas, and templates for nurture vs. conversion.",
    "Open House Coordinator": "You are an open-house coordinator: create checklists, signage copy, registration forms, and follow-up scripts for attendees.",
    "Document Verifier": "You are a document verification assistant: list required docs, validation steps, red flags to watch for, and short templated requests for missing documents.",
    "Lead Nurturer": "You are a lead nurturer: craft message sequences for cold, warm, and hot leads; suggest cadence and personalization tokens for better response rates.",
    "Data Entry Specialist": "You are a precise data entry specialist: provide standardized field mappings, validation rules, and a short SOP for entering leads and transactions into the CRM.",
    "Google Reviews Manager": "You are a reviews manager: produce review request messages, reply templates to reviews (positive & negative), and a simple follow-up workflow to encourage more reviews.",
    "Content Writer (Listings & Blogs)": "You are a content writer for listings and local real-estate blogs: produce catchy listing titles, 300–500 word blog posts on local market trends, and meta descriptions.",
    "Phone Calling Agent (Phone-focused)": "You are a phone-focused calling agent — this persona emphasizes rapport-building, objection handling on calls, voicemail scripts, and clear call-to-action phrasing.",
    "Leads Agent Autopilot": "You are an automated leads agent: triage incoming leads, tag by priority, suggest immediate responses, and create an outbound plan for high-priority leads.",
    "Grant Agent": "You are a grant/assistance agent: advise on available local/state housing assistance programs, eligibility proof needed, and templates to apply or refer clients.",
    "Expired & FSBO Outreach Specialist": "You are an outreach specialist for Expired and FSBO listings: provide concise outreach scripts, value propositions, objection handling, and suggested next steps.",
    "Weekly Reports & Analytics": "You are a weekly reporting assistant: convert raw data into a short executive summary with 3 key insights and 2 recommended actions."
}

# Ensure persona list is deterministic order for UI
PERSONA_NAMES = list(PERSONAS.keys())

# --------------------------
# Sidebar: API key, settings
# --------------------------
st.sidebar.title("🔐 OpenAI & App Settings")
api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key (will not be saved).")
model = st.sidebar.selectbox("Model", options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"], index=0, help="Choose model (if you have access).")
max_tokens = st.sidebar.slider("Response max tokens", 150, 2000, 500, step=50)
temperature = st.sidebar.slider("Temperature", 0.0, 1.2, 0.6, step=0.1)

# Initialize OpenAI client
if api_key:
    client = OpenAI(api_key=api_key)
elif os.environ.get("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
else:
    client = None

st.sidebar.markdown("---")
st.sidebar.markdown("💡 Tip: Enter the API key here (or set OPENAI_API_KEY env var). This app keeps conversation in session only.")


# --------------------------
# Session state initialization
# --------------------------
if "history" not in st.session_state:
    # history holds dict keyed by persona name, value is list of messages in chat format
    st.session_state["history"] = {name: [{"role":"system","content":PERSONAS[name]}] for name in PERSONA_NAMES}
if "active_persona" not in st.session_state:
    st.session_state["active_persona"] = PERSONA_NAMES[0]
if "convos_meta" not in st.session_state:
    st.session_state["convos_meta"] = {}  # store metadata like created_at, convo_id

# --------------------------
# UI: Top controls
# --------------------------
st.title("🏘️ Real Estate Team — Multi-Persona Chatbot")
st.markdown("Choose a team member persona on the left, type a prompt, and the assistant will reply using that role's tone and priorities.")

col1, col2 = st.columns([3,1])

with col1:
    persona = st.selectbox("Choose persona", options=PERSONA_NAMES, index=PERSONA_NAMES.index(st.session_state["active_persona"]))
    st.session_state["active_persona"] = persona

    # Conversation display
    st.markdown(f"### Chat — **{persona}**")
    chat_container = st.container()
    with chat_container:
        messages = st.session_state["history"][persona]
        # show all except system
        for i, m in enumerate(messages):
            if m["role"] == "system":
                continue
            speaker = "You" if m["role"] == "user" else persona
            time_str = ""
            # optionally show timestamps (if stored)
            ts = m.get("ts", None)
            if ts:
                time_str = f" — {ts}"
            if m["role"] == "user":
                st.markdown(f"**You**{time_str}: {m['content']}")
            else:
                st.markdown(f"**{persona}**{time_str}: {m['content']}")

    # Input box
    with st.form(key="prompt_form", clear_on_submit=True):
        user_input = st.text_area("Your message", height=120, placeholder="Ask this persona for help (e.g., 'Create a 3-email follow-up for a cold lead')...")
        submit = st.form_submit_button("Send")

    if submit:
        if client is None:
            st.error("Please provide an OpenAI API key in the sidebar.")
        elif not user_input.strip():
            st.warning("Type a message before sending.")
        else:
            # Append user message to history
            user_msg = {"role":"user", "content": user_input.strip(), "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            st.session_state["history"][persona].append(user_msg)

            # Build messages to send (include system prompt then conversation)
            messages_to_send = st.session_state["history"][persona].copy()

            # Call OpenAI Chat API
            try:
                with st.spinner("Waiting for assistant..."):
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages_to_send,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                assistant_text = response.choices[0].message.content.strip()
                assistant_msg = {"role":"assistant", "content": assistant_text, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                st.session_state["history"][persona].append(assistant_msg)
                # show assistant reply immediately
                st.rerun()
            except Exception as e:
                st.error(f"OpenAI request failed: {e}")

with col2:
    st.markdown("### Quick Actions")
    if st.button("Reset conversation"):
        st.session_state["history"][persona] = [{"role":"system","content":PERSONAS[persona]}]
        st.success("Conversation reset.")
        st.rerun()

    if st.button("Export conversation (CSV)"):
        # Export visible conversation entries (user + assistant)
        conv = [m for m in st.session_state["history"][persona] if m["role"] != "system"]
        df = pd.DataFrame([{"role": m["role"], "content": m["content"], "ts": m.get("ts","")} for m in conv])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"chat_{persona.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    if st.button("Copy persona prompt to clipboard"):
        st.write(PERSONAS[persona])
        st.success("Persona prompt shown above — copy it manually (browser clipboard access may be restricted).")

    st.markdown("---")
    st.markdown("### Active persona system prompt")
    st.info(PERSONAS[persona])

# --------------------------
# Footer: small role legend
# --------------------------
st.markdown("---")
st.caption("Personas are tuned to typical real-estate team roles. Use them as starting points — you can customize messages and refine prompts for stronger brand voice or compliance.")
