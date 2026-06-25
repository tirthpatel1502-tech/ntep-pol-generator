import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
import io
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NTEP Automation", layout="wide")
st.title("📄 NTEP Monthly POL Document Generator")

# The EXACT URL with the gid so it reads the correct tab every time
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lvBqt_rLHPChNZyWDe-v951iIFBOgStZWHiDVClBtE0/edit?gid=57196367#gid=57196367"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # ttl=0 forces it to get the freshest data immediately
    df = conn.read(spreadsheet=SHEET_URL, header=1, ttl=0) 
    
    # --- DATA CLEANING ---
    df.columns = df.columns.str.strip()
    df = df.iloc[:, :14]
    df.columns = ['Sr. No.', 'Name of Employee', 'Bank  A/c No.', 'IFSC Code', 'Designation', 
                  'Vehicle No.', 'V.P', 'V.M', 'Mis', 'Training', 'SM', 'L.M', 
                  'Tb harega desh jitega', 'Total']
    
    df = df.dropna(subset=['Name of Employee'])
    
    # --- CLEAN COMMAS AND NUMBERS ---
    cols_to_clean = ['V.P', 'V.M', 'Mis', 'Tb harega desh jitega', 'Total']
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.replace(',', '', regex=True).str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
    
    # Only keep rows where Total > 0
    df = df[df['Total'] > 0] 

    st.success("✅ Connected to Google Sheets!")
    
    # This will prove it is reading the correct tab!
    st.write(f"📊 Processed {len(df)} employees with a valid total.")
    if len(df) == 0:
        st.error("⚠️ 0 employees found! Please verify the 'header=1' setting matches your sheet layout.")

    # --- CALCULATIONS ---
    vehicle_total = int(df['V.P'].sum() + df['V.M'].sum())
    office_total = int(df['Mis'].sum())
    meeting_total = int(df['Tb harega desh jitega'].sum())
    grand_total = int(df['Total'].sum())

    st.markdown("### 📝 Step 2: Finalize Details")
    st.info(f"**Calculated Grand Total: ₹{grand_total}**")
    
    grand_total_words = st.text_input("Type the Gujarati words for the total amount:", placeholder="e.g. એકસઠ હજાર છસો નેવું")

    # --- PREPARE DATA ---
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
        'vehicle_total': vehicle_total,
        'office_total': office_total,
        'meeting_total': meeting_total,
        'grand_total': grand_total,
        'grand_total_words': str(grand_total_words)
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
    st.error(f"Error: {str(e)}")
