import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
import io
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="NTEP Automation", layout="wide")
st.title("📄 NTEP Monthly POL Document Generator")

# 1. Connect to your live Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lvBqt_rLHPChNZyWDe-v951ilFBOgStZWhIDVClBtE0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, header=1) 
    
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

    # --- UI FOR GUJARATI WORDS ---
    st.markdown("### 📝 Step 2: Enter Gujarati Words")
    st.info(f"**Calculated Grand Total is: ₹{int(grand_total)}**")
    
    grand_total_words = st.text_input(
        f"Type the Gujarati words for {int(grand_total)} here:", 
        placeholder="e.g. Type Gujarati words here"
    )

    # Prepare Data for Word
    employees_list = []
    for index, row in df.iterrows():
        employees_list.append({
            'sr_no': int(row['Sr. No.']),
            'name': row['Name of Employee'],
            'account': str(row['Bank  A/c No.']), 
            'ifsc': row['IFSC Code'],
            'designation': row['Designation'],
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
    st.subheader("⬇️ Step 3: Generate & Download")
    
    if st.button("Generate Monthly Word File"):
        if not grand_total_words:
            st.warning("⚠️ Please type the Gujarati words for the total amount before generating.")
        else:
            file_buffer = generate_docx()
            st.download_button(
                label="⬇️ Download Final Payment Order (.docx)",
                data=file_buffer,
                file_name="SNA_SPARSH_Payment_Order.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

except Exception as e:
    st.error(f"Could not connect or process data: {e}")
