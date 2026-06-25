import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
import io
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NTEP Automation", layout="wide")
st.title("📄 NTEP Monthly POL Document Generator")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1lvBqt_rLHPChNZyWDe-v951iIFBOgStZWHiDVClBtE0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Read the sheet (header=1 means the second row is the header)
    df = conn.read(spreadsheet=SHEET_URL, header=1) 
    
    # --- HARD FIX FOR COLUMN NAMES ---
    # 1. Strip whitespace from all column names (fixes the "hidden space" error)
    df.columns = df.columns.str.strip()
    
    # 2. Force the column names to a known set based on your sheet structure
    # This ignores whatever is currently written in the sheet and maps them by order
    expected_cols = ['Sr. No.', 'Name of Employee', 'Bank  A/c No.', 'IFSC Code', 'Designation', 
                     'Vehicle No.', 'V.P', 'V.M', 'Mis', 'Training', 'SM', 'L.M', 
                     'Tb harega desh jitega', 'Total']
    
    # Ensure we only take the first 14 columns and rename them
    df = df.iloc[:, :14]
    df.columns = expected_cols
    
    # --- DATA CLEANING ---
    df = df.dropna(subset=['Name of Employee'])
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df = df[df['Total'] > 0] 

    st.success("✅ Connected to Google Sheets!")
    
    # --- CALCULATIONS ---
    vehicle_total = df['V.P'].fillna(0).sum() + df['V.M'].fillna(0).sum()
    office_total = df['Mis'].fillna(0).sum()
    meeting_total = df['Tb harega desh jitega'].fillna(0).sum()
    grand_total = df['Total'].fillna(0).sum()

    st.markdown("### 📝 Step 2: Finalize Details")
    st.info(f"**Calculated Grand Total: ₹{int(grand_total)}**")
    
    grand_total_words = st.text_input("Type the Gujarati words for the total amount:", placeholder="e.g. એકસઠ હજાર છસો નેવું")

    # --- WORD GEN SETUP ---
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

    def generate_docx():
        doc = DocxTemplate("template.docx")
        doc.render(context)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    st.markdown("---")
    if st.button("Generate Monthly Word File"):
        if not grand_total_words:
            st.warning("⚠️ Please type the Gujarati words first.")
        else:
            file_buffer = generate_docx()
            st.download_button("⬇️ Download Final Payment Order (.docx)", file_buffer, "SNA_SPARSH_Payment_Order.docx")

except Exception as e:
    st.error(f"Error: {e}")
