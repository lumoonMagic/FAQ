import streamlit as st
from docx import Document
from docx.shared import Inches
import tempfile

st.title("📄 Troubleshooting — FAQ Generator")

faq_title = st.text_input("❓ FAQ Title / Question")
summary = st.text_area("📌 Summary")

# 1️⃣ Number of steps
num_steps = st.number_input("How many steps?", min_value=1, step=1)

# 2️⃣ Auto-generate step text
default_steps = ""
for i in range(1, int(num_steps)+1):
    if i % 2 == 0:
        default_steps += f"Step {i}: [INSERT_SCREENSHOT]\n"
    else:
        default_steps += f"Step {i}: [INSERT_QUERY]\n"

steps = st.text_area("📝 Step-by-Step Instructions (edit if needed)", value=default_steps, height=200)

if st.button("👉 Prepare Uploads / Inputs"):
    # Find placeholders
    screenshot_steps = []
    query_steps = []

    for i, line in enumerate(steps.splitlines()):
        if "[INSERT_SCREENSHOT]" in line:
            screenshot_steps.append(i+1)
        if "[INSERT_QUERY]" in line:
            query_steps.append(i+1)

    st.session_state['screenshot_steps'] = screenshot_steps
    st.session_state['query_steps'] = query_steps

# 3️⃣ Dynamic upload / input fields
screenshot_inputs = {}
query_inputs = {}

if 'screenshot_steps' in st.session_state:
    for s in st.session_state['screenshot_steps']:
        screenshot_inputs[s] = st.file_uploader(f"Upload screenshot for Step {s}", type=['png', 'jpg', 'jpeg'])
if 'query_steps' in st.session_state:
    for q in st.session_state['query_steps']:
        query_inputs[q] = st.text_area(f"Enter query template for Step {q}")

notes = st.text_area("📌 Additional Notes")

# 4️⃣ Generate DOCX
if st.button("📄 Generate FAQ Document"):
    doc = Document()
    doc.add_heading('Sally On-Demand Q&A — FAQ', level=1)
    doc.add_heading('❓ FAQ Title / Question', level=2)
    doc.add_paragraph(faq_title)
    doc.add_heading('📌 Summary', level=2)
    doc.add_paragraph(summary)
    doc.add_heading('📝 Step-by-Step Instructions', level=2)

    for i, line in enumerate(steps.splitlines()):
        step_num = i + 1
        clean_line = line.replace("[INSERT_SCREENSHOT]", "").replace("[INSERT_QUERY]", "").strip()
        if clean_line:
            doc.add_paragraph(clean_line)

        if step_num in screenshot_inputs and screenshot_inputs[step_num] is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                tmpfile.write(screenshot_inputs[step_num].read())
                tmpfile.flush()
                doc.add_picture(tmpfile.name, width=Inches(4))

        if step_num in query_inputs and query_inputs[step_num]:
            doc.add_paragraph(f"Query Template: {query_inputs[step_num]}")

    doc.add_heading('📌 Additional Notes', level=2)
    doc.add_paragraph(notes)

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(tmp_out.name)
    st.success("✅ FAQ document generated!")
    st.download_button("📥 Download FAQ Document", data=open(tmp_out.name, 'rb').read(),
                       file_name='FAQ_Generated.docx',
                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
