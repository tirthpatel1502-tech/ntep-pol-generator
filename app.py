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
    
    # This creates a text box on your dashboard for the Gujarati words
    grand_total_words = st.text_input(
        f"Type the Gujarati words for {int(grand_total)} here:", 
        placeholder="e.g., એકસ
