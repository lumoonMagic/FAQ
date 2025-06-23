import streamlit as st
from docx import Document
from docx.shared import Inches
import tempfile
import google.generativeai as genai

st.set_page_config(page_title="FAQ Generator", layout="wide")
st.title("📄 Dynamic FAQ Generator with Gemini + Assignment")

# Configure Gemini API
API_KEY = st.secrets.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("⚠️ No GEMINI_API_KEY found in Streamlit secrets. Validation won't work.")

# Initialize assignees + FAQ list + steps
if 'assignees' not in st.session_state:
    st.session_state['assignees'] = ["Alice", "Bob", "Charlie"]

if 'faq_list' not in st.session_state:
    st.session_state['faq_list'] = [
        {"question": "How do I check inventory levels?", "assignee": "Alice"},
        {"question": "How to trigger a resupply request?", "assignee": "Bob"},
        {"question": "What is the process for closing a site?", "assignee": "Alice"}
    ]

if 'steps' not in st.session_state:
    st.session_state['steps'] = []

# Select assignee
st.subheader("👤 Select User")
selected_user = st.selectbox("Select the user working on FAQs", st.session_state['assignees'])

# Filter FAQs for selected user
user_faqs = [faq["question"] for faq in st.session_state['faq_list'] if faq["assignee"] == selected_user]

# Select or add FAQ
st.subheader("❓ Select or Add FAQ Question")
col1, col2 = st.columns([2, 1])
with col1:
    if user_faqs:
        selected_faq = st.selectbox("Choose FAQ question", user_faqs)
    else:
        selected_faq = None
        st.info("No FAQs assigned to this user yet.")

with col2:
    new_faq = st.text_input("Add new FAQ question")
    new_assignee = st.selectbox("Assign to", st.session_state['assignees'], key="assignee_select")
    if st.button("➕ Add"):
        if new_faq and not any(faq["question"] == new_faq for faq in st.session_state['faq_list']):
            st.session_state['faq_list'].append({"question": new_faq, "assignee": new_assignee})
            st.success(f"Added: {new_faq} (Assigned to {new_assignee})")
        elif new_faq:
            st.warning("This question is already in the list.")

faq_title = new_faq if new_faq else selected_faq
summary = st.text_area("📌 Summary")

# Add step
if st.button("➕ Add Step"):
    st.session_state['steps'].append({
        "text": "",
        "screenshot": None,
        "query": ""
    })

# Step inputs
for idx, step in enumerate(st.session_state['steps']):
    st.markdown(f"### Step {idx + 1}")
    step["text"] = st.text_area(f"Step {idx + 1} Description", value=step["text"], key=f"text_{idx}")
    step["screenshot"] = st.file_uploader(f"Screenshot for Step {idx + 1} (optional)", type=['png', 'jpg', 'jpeg'], key=f"ss_{idx}")
    step["query"] = st.text_area(f"Query Template for Step {idx + 1} (optional)", value=step["query"], key=f"query_{idx}")
    if st.button(f"❌ Remove Step {idx + 1}", key=f"remove_{idx}"):
        st.session_state['steps'].pop(idx)
        st.experimental_rerun()

notes = st.text_area("📌 Additional Notes")

# Generate base doc
if st.button("📄 Generate FAQ Document"):
    doc = Document()
    doc.add_heading("Sally On-Demand Q&A — FAQ", level=1)
    doc.add_heading("👤 Assignee", level=2)
    doc.add_paragraph(selected_user)
    doc.add_heading("❓ FAQ Title / Question", level=2)
    doc.add_paragraph(faq_title)
    doc.add_heading("📌 Summary", level=2)
    doc.add_paragraph(summary)
    doc.add_heading("📝 Step-by-Step Instructions", level=2)

    for idx, step in enumerate(st.session_state['steps']):
        doc.add_paragraph(f"Step {idx + 1}: {step['text']}")
        if step["query"]:
            doc.add_paragraph(f"Query Template: {step['query']}")
        if step["screenshot"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                tmpfile.write(step["screenshot"].read())
                tmpfile.flush()
                doc.add_picture(tmpfile.name, width=Inches(4))

    doc.add_heading("📌 Additional Notes", level=2)
    doc.add_paragraph(notes)

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(tmp_out.name)
    st.success("✅ FAQ document generated!")
    st.download_button("📥 Download FAQ Document", data=open(tmp_out.name, 'rb').read(),
                       file_name='FAQ_Generated.docx',
                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

# Validate with Gemini
if st.button("🤖 Validate with Gemini"):
    if not API_KEY:
        st.error("❌ No GEMINI_API_KEY configured — cannot validate.")
    else:
        steps_text = "\n".join([f"Step {i+1}: {s['text']}" for i, s in enumerate(st.session_state['steps'])])
        prompt = f"""
You are an AI assistant helping create clear and complete troubleshooting FAQs.

FAQ Question: {faq_title}

Summary: {summary}

Steps:
{steps_text}

Additional Notes: {notes}

Please:
- Check if the steps address the FAQ question adequately.
- Suggest alternative or missing steps to improve clarity.
- Return a rephrased, cleaner version of the steps.
"""

        with st.spinner("Validating and enhancing steps with Gemini..."):
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            enhanced_text = response.text

        st.subheader("✅ Gemini Enhanced Steps")
        st.markdown(enhanced_text)

        doc2 = Document()
        doc2.add_heading("Troubleshoot Guide Q&A — FAQ (AI Enhanced)", level=1)
        doc2.add_heading("👤 Assignee", level=2)
        doc2.add_paragraph(selected_user)
        doc2.add_heading("❓ FAQ Title / Question", level=2)
        doc2.add_paragraph(faq_title)
        doc2.add_heading("📌 Summary", level=2)
        doc2.add_paragraph(summary)
        doc2.add_heading("📝 Step-by-Step Instructions (AI Enhanced)", level=2)
        for line in enhanced_text.splitlines():
            doc2.add_paragraph(line)
        doc2.add_heading("📌 Additional Notes", level=2)
        doc2.add_paragraph(notes)

        tmp_out2 = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc2.save(tmp_out2.name)
        st.download_button("📥 Download AI Enhanced FAQ Document", data=open(tmp_out2.name, 'rb').read(),
                           file_name='FAQ_Generated_AI_Enhanced.docx',
                           mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
