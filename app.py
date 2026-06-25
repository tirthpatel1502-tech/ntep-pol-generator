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
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Read the sheet, treating the second row as headers
    df = conn.read(spreadsheet=SHEET_URL, header=1) 
    
    # 1. CLEANING: Remove all columns that are blank/Unnamed
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Debug: Check what columns are left after cleaning
    # st.write("Columns found:", df.columns.tolist())
    
    # 2. CLEANING: Drop rows that don't look like valid employee data
    # (We look for valid rows where 'Name of Employee' exists)
    df = df.dropna(subset=['Name of Employee'])
    
    # Clean the numbers
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df = df[df['Total'] > 0] 

    st.success("✅ Connected to Google Sheets!")

    # 3. Perform Calculations
    vehicle_total = df['V.P'].fillna(0).sum() + df['V.M'].fillna(0).sum()
    office_total = df['Mis'].fillna(0).sum()
    meeting_total = df['Tb harega desh jitega'].fillna(0).sum()
    grand_total = df['Total'].fillna(0).sum()

    st.markdown("### 📝 Step 2: Finalize Details")
    st.info(f"**Calculated Grand Total: ₹{int(grand_total)}**")
    
    grand_total_words = st.text_input("Type the Gujarati words for the total amount:", placeholder="e.g. એકસઠ હજાર છસો નેવું")

    # 4. Prepare Data
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

    # 5. Download Generation
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
