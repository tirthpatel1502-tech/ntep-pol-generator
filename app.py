import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
import io
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NTEP Automation", layout="wide")
st.title("📄 NTEP Monthly POL Document Generator")

# Your verified Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lvBqt_rLHPChNZyWDe-v951iIFBOgStZWHiDVClBtE0/edit"

try:
    # 1. Connect and Fetch Data
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, header=1) 
    
    # Data Cleaning: Keep only rows with valid data
    df = df.dropna(subset=['Name of Employee'])
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df = df[df['Total'] > 0] 

    st.success("✅ Connected to Google Sheets!")
    st.write(f"Processing {len(df)} employees.")

    # 2. Perform Calculations
    vehicle_total = df['V.P'].fillna(0).sum() + df['V.M'].fillna(0).sum()
    office_total = df['Mis'].fillna(0).sum()
    meeting_total = df['Tb harega desh jitega'].fillna(0).sum()
    grand_total = df['Total'].fillna(0).sum()

    # 3. User Input for Gujarati Text
    st.markdown("### 📝 Step 2: Finalize Details")
    st.info(f"**Calculated Grand Total: ₹{int(grand_total)}**")
    
    grand_total_words = st.text_input(
        "Type the Gujarati words for the total amount:", 
        placeholder="e.g. એકસઠ હજાર છસો નેવું"
    )

    # 4. Prepare Data Dictionary for Word Template
    employees_list = []
    for index, row in df.iterrows():
        employees_list.append({
            'sr_no': int(row['Sr. No.']),
            'name': str(row['Name of Employee']),
            'account': str(row['Bank  A/c No.']), 
            'ifsc': str(row['IFSC Code']),
            'designation': str(row['Designation']),
            'total': int(row['Total'])
        })

    context = {
        'employees': employees_list,
        'vehicle_total': int(vehicle_total),
        'office_total': int(office_total),
        'meeting_total': int(meeting_total),
        'grand_total': int(grand_total),
        'grand_total_words': grand_total_words
    }

    # 5. Generation Logic
    def generate_docx():
        doc = DocxTemplate("template.docx")
        doc.render(context)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.markdown("---")
    st.subheader("⬇️ Step 3: Download")
    
    if st.button("Generate Monthly Word File"):
        if not grand_total_words:
            st.warning("⚠️ Please type the Gujarati words first.")
        else:
            file_buffer = generate_docx()
            st.download_button(
                label="⬇️ Download Final Payment Order (.docx)",
                data=file_buffer,
                file_name="SNA_SPARSH_Payment_Order.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Ensure your Google Sheet is shared with 'Anyone with the link' as a Viewer.")
