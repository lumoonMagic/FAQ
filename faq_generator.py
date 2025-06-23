import streamlit as st
from docx import Document
from docx.shared import Inches
import tempfile
import json
import os

FAQ_FILE = "faq_list.json"

# Helper: load FAQ list
def load_faq_list():
    if os.path.exists(FAQ_FILE):
        with open(FAQ_FILE) as f:
            return json.load(f)
    else:
        return [
            "How do I check inventory levels?", 
            "How to trigger a resupply request?",
            "What is the process for closing a site?"
        ]

# Helper: save FAQ list
def save_faq_list(faq_list):
    with open(FAQ_FILE, "w") as f:
        json.dump(faq_list, f, indent=2)

# Initialize FAQ list
if 'faq_list' not in st.session_state:
    st.session_state['faq_list'] = load_faq_list()

st.title("📄 Troubleshooting — FAQ Generator")

st.subheader("❓ Select or Manage FAQ Question")

# Dropdown to select
selected_faq = st.selectbox("Choose FAQ question", st.session_state['faq_list'])

# Input to add new
new_faq = st.text_input("Add a new FAQ question (optional)")

col1, col2 = st.columns(2)

with col1:
    if st.button("➕ Add to FAQ list"):
        if new_faq and new_faq not in st.session_state['faq_list']:
            st.session_state['faq_list'].append(new_faq)
            save_faq_list(st.session_state['faq_list'])
            st.success(f"Added: {new_faq}")
        elif new_faq:
            st.warning("This question is already in the list.")

with col2:
    if st.button("❌ Remove selected FAQ"):
        if selected_faq:
            st.session_state['faq_list'].remove(selected_faq)
            save_faq_list(st.session_state['faq_list'])
            st.success(f"Removed: {selected_faq}")

# Final FAQ title
faq_title = new_faq if new_faq and new_faq in st.session_state['faq_list'] else selected_faq

summary = st.text_area("📌 Summary")

num_steps = st.number_input("How many steps?", min_value=1, step=1)

# Generate default steps
if 'steps' not in st.session_state:
    default_steps = ""
    for i in range(1, int(num_steps)+1):
        if i % 2 == 0:
            default_steps += f"Step {i}: [INSERT_SCREENSHOT]\n"
        else:
            default_steps += f"Step {i}: [INSERT_QUERY]\n"
    st.session_state['steps'] = default_steps

st.session_state['steps'] = st.text_area("📝 Step-by-Step Instructions (edit if needed)",
                                         value=st.session_state['steps'], height=200)

if st.button("👉 Prepare Uploads / Inputs"):
    screenshot_steps = []
    query_steps = []

    for i, line in enumerate(st.session_state['steps'].splitlines()):
        if "[INSERT_SCREENSHOT]" in line:
            screenshot_steps.append(i+1)
        if "[INSERT_QUERY]" in line:
            query_steps.append(i+1)

    st.session_state['screenshot_steps'] = screenshot_steps
    st.session_state['query_steps'] = query_steps
    st.session_state['screenshot_inputs'] = {}
    st.session_state['query_inputs'] = {}

# Dynamic input generation
if 'screenshot_steps' in st.session_state:
    for s in st.session_state['screenshot_steps']:
        st.session_state['screenshot_inputs'][s] = st.file_uploader(
            f"Upload screenshot for Step {s}", type=['png', 'jpg', 'jpeg'], key=f"screenshot_{s}"
        )
if 'query_steps' in st.session_state:
    for q in st.session_state['query_steps']:
        st.session_state['query_inputs'][q] = st.text_area(
            f"Enter query template for Step {q}", key=f"query_{q}"
        )

notes = st.text_area("📌 Additional Notes")

if st.button("📄 Generate FAQ Document"):
    doc = Document()
    doc.add_heading('Sally On-Demand Q&A — FAQ', level=1)

    doc.add_heading('❓ FAQ Title / Question', level=2)
    doc.add_paragraph(faq_title)

    doc.add_heading('📌 Summary', level=2)
    doc.add_paragraph(summary)

    doc.add_heading('📝 Step-by-Step Instructions', level=2)
    for i, line in enumerate(st.session_state['steps'].splitlines()):
        step_num = i + 1
        clean_line = line.replace("[INSERT_SCREENSHOT]", "").replace("[INSERT_QUERY]", "").strip()
        if clean_line:
            doc.add_paragraph(clean_line)

        if step_num in st.session_state['screenshot_inputs']:
            uploaded_file = st.session_state['screenshot_inputs'][step_num]
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    tmpfile.write(uploaded_file.read())
                    tmpfile.flush()
                    doc.add_picture(tmpfile.name, width=Inches(4))

        if step_num in st.session_state['query_inputs']:
            query_text = st.session_state['query_inputs'][step_num]
            if query_text:
                doc.add_paragraph(f"Query Template: {query_text}")

    doc.add_heading('📌 Additional Notes', level=2)
    doc.add_paragraph(notes)

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(tmp_out.name)
    st.success("✅ FAQ document generated!")
    st.download_button("📥 Download FAQ Document", data=open(tmp_out.name, 'rb').read(),
                       file_name='FAQ_Generated.docx',
                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
