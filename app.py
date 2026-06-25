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
    # Read the sheet, skipping the first row (the title row)
    df = conn.read(spreadsheet=SHEET_URL, header=1) 
    
    # Debug: Show the actual columns found so we can see why it fails
    st.write("Columns found:", df.columns.tolist())
    
    # Rename columns based on their position (0=SrNo, 1=Name, 2=Bank, 3=IFSC, 4=Designation, 13=Total)
    df.columns = ['Sr. No.', 'Name of Employee', 'Bank  A/c No.', 'IFSC Code', 'Designation', 'Vehicle No.', 'V.P', 'V.M', 'Mis', 'Training', 'SM', 'L.M', 'Tb harega desh jitega', 'Total']
    
    # Clean the data
    df = df.dropna(subset=['Name of Employee'])
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    df = df[df['Total'] > 0] 

    st.success("✅ Connected to Google Sheets!")
    
    # Calculate Totals
    vehicle_total = df['V.P'].fillna(0).sum() + df['V.M'].fillna(0).sum()
    office_total = df['Mis'].fillna(0).sum()
    meeting_total = df['Tb harega desh jitega'].fillna(0).sum()
    grand_total = df['Total'].fillna(0).sum()

    st.markdown("### 📝 Step 2: Enter Gujarati Words")
    grand_total_words = st.text_input("Type the Gujarati words for the total amount:", placeholder="e.g. એકસઠ હજાર છસો નેવું")

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
