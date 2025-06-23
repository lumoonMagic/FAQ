import streamlit as st
from docx import Document
from docx.shared import Inches
import tempfile

st.title("📄Q&A — FAQ Generator")

# Form fields
faq_title = st.text_input("❓ FAQ Title / Question", placeholder="Enter your FAQ title or question here")

summary = st.text_area("📌 Summary", placeholder="Enter a brief summary")

steps = st.text_area("📝 Step-by-Step Instructions", 
                     placeholder="Write steps here.\nExample:\n1. Step 1 description [INSERT_SCREENSHOT]\n2. Step 2 description [INSERT_QUERY]\n3. Step 3 description")

query_template = st.text_area("💬 Query Template", placeholder="Enter query example/template")

notes = st.text_area("📌 Additional Notes", 
                     placeholder="e.g., Notes about previous issues, Jira links, contacts for support")

uploaded_images = st.file_uploader("📷 Upload screenshots (order matters, match placeholders)", 
                                   type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

# Generate docx
if st.button("Generate FAQ Document"):
    doc = Document()
    doc.add_heading('Sally On-Demand Q&A — FAQ', level=1)
    
    doc.add_heading('❓ FAQ Title / Question', level=2)
    doc.add_paragraph(faq_title)

    doc.add_heading('📌 Summary', level=2)
    doc.add_paragraph(summary)

    doc.add_heading('📝 Step-by-Step Instructions', level=2)
    
    img_idx = 0
    for line in steps.splitlines():
        if "[INSERT_SCREENSHOT]" in line and img_idx < len(uploaded_images):
            clean_line = line.replace("[INSERT_SCREENSHOT]", "").strip()
            if clean_line:
                doc.add_paragraph(clean_line)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                tmpfile.write(uploaded_images[img_idx].read())
                tmpfile.flush()
                doc.add_picture(tmpfile.name, width=Inches(4))
            img_idx += 1
        elif "[INSERT_QUERY]" in line:
            clean_line = line.replace("[INSERT_QUERY]", "").strip()
            if clean_line:
                doc.add_paragraph(clean_line)
            doc.add_paragraph(f"Query Template: {query_template}")
        else:
            doc.add_paragraph(line)

    doc.add_heading('📌 Additional Notes', level=2)
    doc.add_paragraph(notes)

    # Download file
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(tmp_out.name)
    st.success("✅ FAQ document generated!")
    st.download_button("📥 Download FAQ Document", data=open(tmp_out.name, 'rb').read(),
                       file_name='FAQ_Generated.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
