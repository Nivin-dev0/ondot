import streamlit as st
import requests
import json
import time

st.set_page_config(
    page_title="OnDot Lite", 
    page_icon="✨",
)

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
        uid = result["result"]["uid"]
        session_id = result["result"]["session_id"]
        return sid, session_id, uid

# Retrieve User Name
def user_name(uid,session_id,sid):
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_kw"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "res.users",
            "method": "read",
            "args": [
            uid,
            [
                "name",
                "company_id"
            ]
            ],
            "kwargs": {},
            "session_id": session_id,
            "context": {
            "lang": "en_GB",
            "tz": "Asia/Kolkata",
            "uid": uid
            }
        },
        "id": "r6",
    }
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    result = r.json()
    name = result["result"]["name"]
    return name

# Retrieve attendance details from ERP system
def retrieve_attendance(sid, session_id):
    # First step: get args
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_kw"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "create", "args": [{}], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    args = r.json()["result"]
    #st.write(r.json())
    
    # Next step: call button_check_status
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_button"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "button_check_status", "domain_id": "null", "context_id": 1, "args": [[args], {}], "session_id": session_id}, "id": "r54"}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    
    # Final step: read attendance data
    url = "https://erp.vidyaacademy.ac.in/web/dataset/call_kw"
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status", "method": "read", "args": [[args], ["atten_status"]], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    subs = r.json()["result"][0]["atten_status"]
    #st.write(r.json())
    
    payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "vict.academics.duty.leave.status.lines", "method": "read", "args": [subs, ["course", "course_percentage"]], "kwargs": {"context": {}}, "session_id": session_id, "context": {}}}
    r = requests.post(url, data=json.dumps(payload), cookies={"sid": sid})
    
    attendance = {}
    for i in r.json()["result"]:
        attendance[i["course"][1]] = i["course_percentage"]
    
    return attendance

# Streamlit App
def main():
    st.title(":blue[OnDot] Lite")
    st.write("*Attendance Tracking Made Easy* :sunglasses:")
    
    # Input fields for username and password
    username = st.text_input("Enter TL Number:").strip()
    password = st.text_input("Enter your password:", type="password").strip()
    
    if st.button("Fetch Attendance"):
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                erplogin = login(username, password)
                
                if erplogin == 'wrong':
                    st.error("Error: Incorrect username or password.")
                else:
                    sid, session_id, uid = erplogin
                    name = user_name(uid,session_id, sid)
                    message = "Welcome, "+name
                    st.subheader(message, divider="gray")
                    attendance = retrieve_attendance(sid, session_id)
                    st.write("\n")
                    # Display attendance details with progress bars
                    for course, percentage in attendance.items():
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            col1.markdown(f"<p style='font-weight:bold; font-size:16px;'>{course}</p>", unsafe_allow_html=True)
                            col2.write("\n")
                            #col2.subheader(str(percentage)+"%")
                            col1.progress(percentage / 100)
                            bunkable_classes = max(0, (percentage - 75) / 100 * 40)  # Assuming 40 total classes
                            if (percentage == 100):
                                col1.write("Woww, you are a legend")
                                col2.subheader(str(percentage)+"%")
                                #col2.metric(label="Attendance", value=str(percentage)+" %", delta=" ")
                            elif (percentage == 75):
                                col2.subheader(str(percentage)+"%")
                                #col2.metric(label="Attendance", value=str(percentage)+" %", delta="0")
                            elif (percentage > 75):
                                col1.write(f"You are ahead of {int(bunkable_classes)} classes")
                                col2.subheader(str(percentage)+"%")
                                #col2.metric(label="Attendance", value=str(percentage)+" %", delta=str(int(bunkable_classes)))
                            else:
                                col1.write("Oops, you need to attend more classes")
                                col2.subheader(":red["+str(percentage)+"%]")
                                #col2.metric(label="Attendance", value=str(percentage)+" %", delta="-")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
