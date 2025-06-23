import streamlit as st
from docx import Document
from docx.shared import Inches
import tempfile
import json
import os
import google.generativeai as genai

# --- CONFIG ---
FAQ_FILE = "faq_list.json"
API_KEY = st.secrets.get("GEMINI_API_KEY", "")  # Set in Streamlit secrets or replace directly

# --- INIT ---
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- HELPERS ---
def load_faq_list():
    if os.path.exists(FAQ_FILE):
        try:
            with open(FAQ_FILE) as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    st.warning("FAQ file invalid. Using default list.")
        except json.JSONDecodeError:
            st.warning("FAQ file empty/broken. Using default list.")
    return [
        "How do I check inventory levels?",
        "How to trigger a resupply request?",
        "What is the process for closing a site?"
    ]

def save_faq_list(faq_list):
    with open(FAQ_FILE, "w") as f:
        json.dump(faq_list, f, indent=2)

# --- STATE ---
if 'faq_list' not in st.session_state:
    st.session_state['faq_list'] = load_faq_list()

# --- UI ---
st.title("📄 Troubleshooting — FAQ Generator + AI Validation")

st.subheader("❓ Manage FAQ Question")
selected_faq = st.selectbox("Choose FAQ question", st.session_state['faq_list'])
new_faq = st.text_input("Add a new FAQ question (optional)")

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add to FAQ list"):
        if new_faq and new_faq not in st.session_state['faq_list']:
            st.session_state['faq_list'].append(new_faq)
            save_faq_list(st.session_state['faq_list'])
            st.success(f"Added: {new_faq}")
        elif new_faq:
            st.warning("Already in list.")
with col2:
    if st.button("❌ Remove selected FAQ"):
        if selected_faq:
            st.session_state['faq_list'].remove(selected_faq)
            save_faq_list(st.session_state['faq_list'])
            st.success(f"Removed: {selected_faq}")

faq_title = new_faq if new_faq and new_faq in st.session_state['faq_list'] else selected_faq
summary = st.text_area("📌 Summary")

num_steps = st.number_input("How many steps?", min_value=1, step=1)

if 'steps' not in st.session_state or st.button("🔄 Regenerate Steps"):
    default_steps = ""
    for i in range(1, int(num_steps)+1):
        if i % 2 == 0:
            default_steps += f"Step {i}: [INSERT_SCREENSHOT]\n"
        else:
            default_steps += f"Step {i}: [INSERT_QUERY]\n"
    st.session_state['steps'] = default_steps

st.session_state['steps'] = st.text_area("📝 Step-by-Step Instructions", value=st.session_state['steps'], height=200)

if st.button("👉 Prepare Uploads / Inputs"):
    screenshot_steps = []
    query_steps = []
    for i, line in enumerate(st.session_state['steps'].splitlines()):
        if "[INSERT_SCREENSHOT]" in line:
            screenshot_steps.append(i + 1)
        if "[INSERT_QUERY]" in line:
            query_steps.append(i + 1)
    st.session_state['screenshot_steps'] = screenshot_steps
    st.session_state['query_steps'] = query_steps
    st.session_state['screenshot_inputs'] = {}
    st.session_state['query_inputs'] = {}

if 'screenshot_steps' in st.session_state:
    for s in st.session_state['screenshot_steps']:
        st.session_state['screenshot_inputs'][s] = st.file_uploader(f"Upload screenshot for Step {s}", type=['png', 'jpg', 'jpeg'], key=f"screenshot_{s}")
if 'query_steps' in st.session_state:
    for q in st.session_state['query_steps']:
        st.session_state['query_inputs'][q] = st.text_area(f"Enter query template for Step {q}", key=f"query_{q}")

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
    st.success("✅ User-entered FAQ document generated!")
    st.download_button("📥 Download User FAQ Document", data=open(tmp_out.name, 'rb').read(),
                       file_name='FAQ_User_Generated.docx',
                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

if API_KEY and st.button("✅ Validate & Improve with Gemini"):
    with st.spinner("Contacting Gemini..."):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')  # Gemini 2.5 not yet available in Python SDK; 1.5 is current
            prompt = f"""
FAQ Question:
{faq_title}

User Steps:
{st.session_state['steps']}

Task:
- Validate if steps address FAQ.
- Improve clarity, grammar, flow.
- Suggest additional helpful steps.
- Highlight gaps.

Format:
1️⃣ Validation of Coverage  
2️⃣ Improved Step-by-Step Instructions  
3️⃣ Suggested Additional Steps or Alternatives
"""
            response = model.generate_content(prompt)
            ai_output = response.text

            st.success("✅ Gemini validation complete!")
            st.text_area("🤖 Gemini Output", value=ai_output, height=400)

            doc_ai = Document()
            doc_ai.add_heading('Troubleshooting Q&A — FAQ (AI Enhanced)', level=1)
            doc_ai.add_heading('❓ FAQ Title / Question', level=2)
            doc_ai.add_paragraph(faq_title)
            doc_ai.add_heading('📌 Summary', level=2)
            doc_ai.add_paragraph(summary)
            doc_ai.add_heading('📝 AI Enhanced Steps & Analysis', level=2)
            doc_ai.add_paragraph(ai_output)
            doc_ai.add_heading('📌 Additional Notes', level=2)
            doc_ai.add_paragraph(notes)

            tmp_out_ai = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
            doc_ai.save(tmp_out_ai.name)
            st.download_button("📥 Download AI-Enhanced FAQ Document", data=open(tmp_out_ai.name, 'rb').read(),
                               file_name='FAQ_AI_Enhanced.docx',
                               mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        except Exception as e:
            st.error(f"Error during Gemini call: {e}")
elif not API_KEY:
    st.info("ℹ️ Set your GEMINI_API_KEY in Streamlit secrets to enable AI validation.")
