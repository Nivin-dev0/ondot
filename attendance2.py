import streamlit as st
import requests
import json
import time

# Login to the ERP system
def login(username, password):
    username = username.upper()
    # Sends authentication request to the ERP system
    url = "https://erp.vidyaacademy.ac.in/web/session/authenticate"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": "liveone",
            "login": username,
            "password": password,
            "base_location": "https://erp.vidyaacademy.ac.in",
            "context": {},
        },
        "id": "r7",
    }
    r = requests.post(url, data=json.dumps(payload))
    result = r.json()

    if result['result']['uid'] is False:
        return 'wrong'
    else:
        sid = r.cookies.get_dict()["sid"]
        session_id = result["result"]["session_id"]
        return sid, session_id

# Retrieve attendance details from ERP system
def retrieve_attendance(sid, session_id):
    # First step: get args
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_kw"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "create", "args": [{}], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    args = r.json()["result"]
    
    # Next step: call button_check_status
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_button"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "button_check_status", "domain_id": "null", "context_id": 1, "args": [[args], {}], "session_id": session_id}, "id": "r54"}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    
    # Final step: read attendance data
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_kw"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "read", "args": [[args], ["atten_status"]], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    subs = r.json()["result"][0]["atten_status"]
    
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status.lines", "method": "read", "args": [subs, ["course", "course_percentage"]], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    
    attendance = {}
    for i in r.json()["result"]:
        attendance[i["course"][1]] = i["course_percentage"]
    
    return attendance

# Streamlit App
def main():
    st.set_page_config(
    page_title="OnDot Web",
    page_icon="✨",
    layout="wide",  
)
    st.title("On-Dot")
    st.write("Web App Back-End Test -Experimental-")
    
    # Input fields for username and password
    username = st.text_input("Enter TL Number:").strip()
    password = st.text_input("Enter your password:", type="password").strip()
    
    if st.button("Fetch Attendance"):
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                st.write("Logging in...")
                
                erplogin = login(username, password)
                
                if erplogin == 'wrong':
                    st.error("Error: Incorrect username or password.")
                else:
                    sid, session_id = erplogin
                    st.success("Login successful! Fetching attendance data...")
                    attendance = retrieve_attendance(sid, session_id)
                    
                    # Display attendance details with progress bars
                    st.write("\n--- Attendance Details ---")
                    for course, percentage in attendance.items():
                        st.markdown(f"<p style='font-weight:bold; font-size:16px;'>{course}: {percentage}%</p>", unsafe_allow_html=True)
                        st.progress(percentage / 100)
                        bunkable_classes = max(0, (percentage - 75) / 100 * 40)  # Assuming 40 total classes
                        st.write(f"You can cut {int(bunkable_classes)} more classes")
                        #st.write("\n")  # Add line break
                        st.write("---------------------------")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
