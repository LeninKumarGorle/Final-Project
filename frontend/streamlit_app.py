import streamlit as st
import jwt
from datetime import datetime, timedelta, UTC
import hashlib
import snowflake.connector
from dotenv import load_dotenv
import os
import re
from scripts.trigger_dag import unpause_and_trigger_dag
import requests
from scripts.pdf_helper import create_pdf
import markdown
import html
from streamlit_ace import st_ace

# Load environment variables
load_dotenv()

# ----------------- Configuration -----------------
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
MAX_QUESTIONS = 3

# Snowflake credentials from .env
SNOWFLAKE_CONFIG = {
    "user": os.getenv('SNOWFLAKE_USER'),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA")
}

ROLES = ["Data Analyst", "Data Engineer", "Software Engineer", "Machine Learning Engineer", "Data Scientist", "AI Engineer"]
COMPANIES = ["Meta", "Apple", "Amazon", "Netflix", "Google"]
PAGES = ["Home","Prepare for Interview", "Mock Interview", "Q and A"]

FASTAPI_URL = "http://localhost:8000"

# ----------------- Helpers -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(username):
    payload = {
        "username": username,
        "exp": datetime.now(UTC) + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_snowflake_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def create_users_table():
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        cs.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username STRING PRIMARY KEY,
                password_hash STRING,
                email STRING,
                full_name STRING
            )
        """)

def add_user(username, password_hash,email,full_name):
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        try:
            cs.execute(
                "INSERT INTO users (username, password_hash,email,full_name) VALUES (%s, %s, %s, %s)",
                (username, password_hash,email,full_name)
            )
            return True
        except snowflake.connector.errors.IntegrityError:
            return False

def get_user_password_hash(username):
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        cs.execute(
            "SELECT password_hash FROM users WHERE username = %s",
            (username,)
        )
        result = cs.fetchone()
        return result[0] if result else None

def get_user_email(username):
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        cs.execute("SELECT email FROM users WHERE username = %s", (username,))
        result = cs.fetchone()
        return result[0] if result else None

def update_user_password(username, password_hash):
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        cs.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))

def is_valid_email(email):
    return re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", email) is not None

def reset_session():
    st.session_state.pop("recommendations", None)
    st.session_state.pop("upload_status", None)

def call_upload_api(uploaded_file,job_description, location):
    try:
        files = {"file": uploaded_file.getvalue()}
        data = {"job_description": job_description, "location": location}
        response = requests.post(f"{FASTAPI_URL}/analyze-resume/", files=files,data=data)
        return response.json()
    except Exception as e:
        return f"Error: {e}"

def call_recommendation_api():
    try:
        response = requests.get(f"{FASTAPI_URL}/get_recommendations")
        return response.text
    except Exception as e:
        return f"Error: {e}"

def call_chat_api(question):
    try:
        payload = {"query": question}
        response = requests.post(f"{FASTAPI_URL}/get-answer", json=payload)
        return response.json().get("response", "No response")
    except Exception as e:
        return f"Error: {e}"

def render_evaluation_box(markdown_text: str):
    formatted_text = re.sub(r'(?<=\S)(\n)?(\d+\.\s)', r'\n\n\2', markdown_text)
    html = markdown.markdown(formatted_text)

    st.markdown(
        """
        <style>
        .scrollable-box {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 10px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 0.9rem;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="scrollable-box">{html}</div>', unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

def format_message(text):
    """
    This function is used to format the messages in the chatbot UI.

    Parameters:
    text (str): The text to be formatted.
    """
    text_blocks = re.split(r"```[\s\S]*?```", text)
    code_blocks = re.findall(r"```([\s\S]*?)```", text)

    text_blocks = [html.escape(block) for block in text_blocks]

    formatted_text = ""
    for i in range(len(text_blocks)):
        formatted_text += text_blocks[i].replace("\n", "<br>")
        if i < len(code_blocks):
            formatted_text += f'<pre style="white-space: pre-wrap; word-wrap: break-word;"><code>{html.escape(code_blocks[i])}</code></pre>'

    return formatted_text

def message_func(text, is_user=False):
    """
    This function is used to display the messages in the chatbot UI.

    Parameters:
    text (str): The text to be displayed.
    is_user (bool): Whether the message is from the user or not.
    is_df (bool): Whether the message is a dataframe or not.
    """
    if is_user:
        avatar_url = "https://avataaars.io/?avatarStyle=Transparent&topType=LongHairStraight&accessoriesType=Prescription02&hairColor=Black&facialHairType=Blank&clotheType=Hoodie&clotheColor=Red&eyeType=Default&eyebrowType=Default&mouthType=Smile&skinColor=Light"
        message_alignment = "flex-end"
        message_bg_color = "linear-gradient(135deg, #00B2FF 0%, #006AFF 100%)"
        avatar_class = "user-avatar"
        st.write(
            f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: 14px;">
                        {text} \n </div>
                    <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
        avatar_url = "https://avataaars.io/?avatarStyle=Transparent&topType=Hat&accessoriesType=Prescription02&facialHairType=BeardLight&facialHairColor=Black&clotheType=BlazerSweater&eyeType=Happy&eyebrowType=DefaultNatural&mouthType=Default&skinColor=Light"
        message_alignment = "flex-start"
        message_bg_color = "#71797E"
        avatar_class = "bot-avatar"

        text = format_message(text)

        st.markdown(
            f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: 14px;">
                        {text} \n </div>
                </div>
                """,
            unsafe_allow_html=True,
            )



# ----------------- Auth Pages -----------------
def signup():
    st.subheader("Signup")
    full_name = st.text_input("Full Name", key="signup_fullname")
    email = st.text_input("Email", key="signup_email").strip()
    new_user = st.text_input("Username", key="signup_user").strip()
    new_pass = st.text_input("Password", type="password", key="signup_pass")
    if st.button("Signup"):
        if len(new_user) < 5:
            st.error("Username must be at least 5 characters long.")
            return
        if len(new_pass) < 8:
            st.error("Password must be at least 8 characters long.")
            return
        if not is_valid_email(email):
            st.error("Invalid email format.")
            return
        password_hash = hash_password(new_pass)
        success = add_user(new_user, password_hash, email, full_name)
        if success:
            st.success("User created. Please login.")
        else:
            st.error("Username already exists.")

def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user").strip()
    password = st.text_input("Password", type="password", key="login_pass")

    login_attempt = st.button("Login")

    if login_attempt:
        stored_hash = get_user_password_hash(username)
        if stored_hash and stored_hash == hash_password(password):
            token = create_token(username)
            st.session_state["token"] = token
            st.success("Login successful!")
            st.rerun()
        else:
            st.warning("Incorrect username or password. If you've forgotten your password, you can reset it below.")
            st.session_state["login_failed"] = True

    if st.session_state.get("login_failed"):
        if st.button("Reset your password?"):
            st.session_state["show_reset"] = True
            st.session_state.pop("login_failed", None)
            st.rerun()



def forgot_password():
    st.subheader("Reset Password")
    username = st.text_input("Username", key="reset_user").strip()
    email = st.text_input("Registered Email", key="reset_email").strip()
    new_pass = st.text_input("New Password", type="password", key="new_pass")

    if st.button("Update Password"):
        if len(new_pass) < 8:
            st.error("Password must be at least 8 characters long.")
            return

        registered_email = get_user_email(username)
        current_hash = get_user_password_hash(username)
        new_hash = hash_password(new_pass)

        if registered_email and registered_email.lower() == email.lower():
            if new_hash == current_hash:
                st.warning("New password cannot be the same as the old password.")
                return
            update_user_password(username, new_hash)
            st.success("Password updated. Please login.")
            st.session_state.pop("show_reset", None)
            st.rerun()
        else:
            st.error("Username and email do not match.")

def main_app(username):
    st.sidebar.title("Main Menu")

    if "selected_role" not in st.session_state:
        st.session_state.selected_role = ""
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = ""
    if "active_page" not in st.session_state or st.session_state.active_page not in PAGES:
        st.session_state.active_page = "Home"
    if "selections_confirmed" not in st.session_state:
        st.session_state.selections_confirmed = False

    st.subheader(f"Welcome, {username}!")

    # Always evaluate selections after rendering selectboxes
    if st.session_state.active_page == "Home":
        prev_role = st.session_state.selected_role
        prev_company = st.session_state.selected_company

        st.session_state.selected_role = st.selectbox("Select your role", ["Select a role"] + ROLES)
        st.session_state.selected_company = st.selectbox("Select your dream company", ["Select a company"] + COMPANIES)

        selections_made = (
            st.session_state.selected_role in ROLES and 
            st.session_state.selected_company in COMPANIES
        )

        if selections_made and (st.session_state.selected_role != prev_role or st.session_state.selected_company != prev_company):
            st.session_state.selections_confirmed = True

        if "show_success" not in st.session_state:
            st.session_state.show_success = False

        if selections_made and (st.session_state.selected_role != prev_role or st.session_state.selected_company != prev_company):
            st.session_state.selections_confirmed = True
            st.session_state.show_success = True

        if st.session_state.show_success:
            st.success("Selections saved. Use the sidebar to navigate to other pages.")
            st.session_state.show_success = False
    else:
        selections_made = (
            st.session_state.selected_role in ROLES and 
            st.session_state.selected_company in COMPANIES
        )

    # Sidebar navigation buttons
    for page in PAGES:
        is_current = page == st.session_state.active_page
        button_type = "primary" if is_current else "secondary"
        disabled = page != "Home" and not selections_made

        if st.sidebar.button(page, use_container_width=True, key=f"nav_{page}", type=button_type, disabled=disabled):
            st.session_state.active_page = page

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # Page-specific logic
    if selections_made and st.session_state.active_page != "Home":
        role = st.session_state.selected_role
        company = st.session_state.selected_company
        # st.markdown(f"**Selected Role:** {st.session_state.selected_role}")
        # st.markdown(f"**Selected Company:** {st.session_state.selected_company}")
    if "last_active_page" not in st.session_state:
        st.session_state.last_active_page = None
    if st.session_state.active_page != st.session_state.last_active_page:
        if st.session_state.active_page == "Prepare for Interview":
            st.session_state.summary = None
            st.session_state.pdf_bytes = None
        st.session_state.last_active_page = st.session_state.active_page

    if selections_made:
        if st.session_state.active_page == "Prepare for Interview":
            #st.set_page_config(page_title="AI Career Recommender", layout="centered")
            if "summary" not in st.session_state:
                st.session_state.summary = None
            if "pdf_bytes" not in st.session_state:
                st.session_state.pdf_bytes = None
            uploaded_file = st.file_uploader("Upload your resume", type=["pdf"], key="pdf_upload", on_change=reset_session)
            job_description = st.text_area("Paste Target Job Description")
            location = st.text_input("Preferred Job Location", value="")
            if st.button("🚀 Get Analysis") and uploaded_file and job_description:
                with st.spinner("Analyzing your resume..."):
                    data = call_upload_api(uploaded_file, job_description, location)
                    st.session_state.summary = data.get("summary")
                    st.session_state.pdf_bytes = data["pdf_base64"].encode("latin1")
            if st.session_state.summary:
                st.subheader("Summary")
                st.success(st.session_state.summary)
            
            if st.session_state.pdf_bytes:
                st.download_button(
                label="Download Full Report (PDF)",
                data=st.session_state.pdf_bytes,
                file_name="career_recommendation_report.pdf",
                mime="application/pdf"
                )
            

        elif st.session_state.active_page =="Mock Interview":
            
            for key in ["interview_mode", "interview_transcript", "interview_started", "interview_done", "last_question", "evaluation_result", "oa_state_initialized"]:
                if key not in st.session_state:
                    st.session_state[key] = (None if key == "interview_mode" else
                                             [] if key == "interview_transcript" else
                                             False if key in ["interview_started", "interview_done", "oa_state_initialized"] else "")

            resume_s3_path = "s3://team6-final-project/resumes/markdown/FILE_resume.md"
            if not st.session_state.interview_started:
                st.session_state.interview_mode = st.selectbox("Choose Interview Mode", ["Behavioral", "Resume", "Practice OA"], key="mode_selector")
                st.markdown(f"### You are now starting a **{st.session_state.interview_mode}** interview.")
                if st.button("Start Interview"):
                    if st.session_state.interview_mode == "Practice OA":
                        for key in ["topic_selected", "oa_session_state", "response", "feedback", "code", "started"]:
                            st.session_state[key] = "array" if key == "topic_selected" else {} if key == "oa_session_state" else "" if key in ["response", "feedback", "code"] else False
                        st.session_state.oa_state_initialized = True
                        st.session_state.interview_started = True
                        st.rerun()
                    else:
                        with st.spinner("Initializing interview..."):
                            payload = {
                                "mode": st.session_state.interview_mode,
                                "role": role,
                                "previous_question": "start",
                                "user_answer": "",
                                "resume_s3_path": resume_s3_path
                            }
                            if st.session_state.interview_mode == "Behavioral":
                                st.session_state.last_question = "Hi there! Let's begin your behavioral interview. Can you tell me about yourself?"
                            elif st.session_state.interview_mode == "Resume":
                                st.session_state.last_question = "Welcome to the resume-based interview. Walk me through your most recent project and your role in it."
                            else:
                                response = requests.post(f"{FASTAPI_URL}/generates_next_question/", json=payload)
                                print(response.json())
                                st.session_state.last_question = response.json()["next_question"]
                            st.session_state.interview_transcript = []
                            st.session_state.interview_started = True
                            st.session_state.interview_done = False
                            st.rerun()
            if st.session_state.interview_started:
                    if st.session_state.interview_mode == "Practice OA":
                        
                        TOPICS = ["array", "string", "hash-table", "dynamic-programming", "greedy", "tree", "two-pointers", "sliding-window", "graph", "linked-list", "stack", "queue"]
                        topic = st.selectbox("Select a topic", TOPICS, index=TOPICS.index(st.session_state.topic_selected))
                        if topic != st.session_state.topic_selected:
                            st.session_state.topic_selected = topic
                            st.session_state.response = ""
                            st.session_state.feedback = ""
                            st.session_state.code = ""
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Start Topic"):
                                st.session_state.started = True
                                st.session_state.oa_session_state = {
                                    "topic": topic,
                                    "index": 0,
                                    "state": "waiting_for_code",
                                    "skipped": []
                                }
                                st.session_state.response = ""
                                st.session_state.feedback = ""
                                st.session_state.code = ""
                                res = requests.post(f"{FASTAPI_URL}/oa-session/", json={
                                    "user_input": topic,
                                    "session_state": st.session_state.oa_session_state
                                })
                                data = res.json()
                                print(data)
                                st.session_state.response = data.get("question_text", "")
                                if isinstance(st.session_state.response, dict):
                                    st.session_state.response = st.session_state.response.get("question_text", "")
                                st.session_state.code = data.get("code_stub", "# Write your solution here")
                                st.session_state.oa_session_state = data.get("session_state", {})
                                st.rerun()
                        with col2:
                            if st.button("Next Question", disabled=not st.session_state.get("started", False)):
                                st.session_state.feedback = ""
                                res = requests.post(f"{FASTAPI_URL}/oa-session/", json={
                                "user_input": "next",
                                "session_state": st.session_state.oa_session_state
                                })
                                data = res.json()
                                st.session_state.response = data.get("question_text", "")
                                if isinstance(st.session_state.response, dict):
                                    st.session_state.response = st.session_state.response.get("question_text", "")
                                st.session_state.code = data.get("code_stub", "")
                                st.session_state.oa_session_state = data.get("session_state", {})
                                st.rerun()
                        
                        if isinstance(st.session_state.response, str) and st.session_state.response.strip():
                            st.markdown("### Question")
                            st.markdown(st.session_state.response)
                            code = st_ace(
                            value=st.session_state.code or "# Write your solution here",
                            language="python",
                            theme="monokai",
                            height=500,
                            key=f"editor-{st.session_state.oa_session_state.get('index', 0)}",
                            auto_update=True
                            )
                            if st.button("Submit Solution"):
                                if not code.strip():
                                    st.warning("Your code is empty. Please write something before submitting.")
                                else:
                                    st.session_state.code = code
                                    if st.session_state.oa_session_state.get("state") == "waiting_for_code":
                                        st.session_state.oa_session_state["state"] = "waiting_for_next"
                                    res = requests.post(f"{FASTAPI_URL}/oa-session/", json={
                                            "user_input": "",
                                            "code": code,
                                            "problem": st.session_state.response,
                                            "session_state": st.session_state.oa_session_state
                                        })
                                    data = res.json()
                                    feedback = data.get("question_text", "")
                                    if isinstance(feedback, dict):
                                        feedback = feedback.get("question_text", "")

                                    if "Type 'next'" in feedback:
                                        st.session_state.feedback = feedback
                                    else:
                                        st.session_state.response = feedback
                                        st.session_state.feedback = ""
                                    st.session_state.oa_session_state = data.get("session_state", {})
                                    st.rerun()
                            if st.session_state.feedback:
                                st.markdown("### Feedback")
                                st.markdown(st.session_state.feedback)
                        else:
                            st.warning("No question loaded yet. Please click 'Start Topic' or 'Next Question'.")
                    else:   
                        st.markdown("### Interview Chat")
                        for i, (q, a) in enumerate(st.session_state.interview_transcript):
                            message_func(f"Q{i+1}:  {q}", is_user=False)
                            #cleaned_ans = unicodedata.normalize("NFKD", a.strip())
                            message_func(a.strip(), is_user=True)

                        if not st.session_state.interview_done:
                            message_func(f"Q{len(st.session_state.interview_transcript)+1}: {st.session_state.last_question}", is_user=False)
                            # with st.chat_message("assistant"):
                            #     st.markdown(f"**Q{len(st.session_state.interview_transcript)+1}:** {st.session_state.last_question}")

                            user_input = st.chat_input("Your answer...")
                            if user_input:

                                #cleaned_input = unicodedata.normalize("NFKD", user_input.strip())
                                st.session_state.interview_transcript.append((st.session_state.last_question, user_input.strip()))

                                if len(st.session_state.interview_transcript) >= MAX_QUESTIONS:
                                    st.session_state.interview_done = True
                                    st.rerun()
                                else:
                                    payload = {
                                        "mode": st.session_state.interview_mode,
                                        "role": role,
                                        "company": company,
                                        "previous_question": st.session_state.last_question,
                                        "user_answer": user_input.strip(),
                                        "resume_s3_path": resume_s3_path
                                    }
                                    response = requests.post(f"{FASTAPI_URL}/generates_next_question/", json=payload)
                                    print(response.json())
                                    print("printing response")
                                    st.session_state.last_question = response.json()["next_question"]
                                    st.rerun()
                        if st.session_state.interview_done and not st.session_state.evaluation_result:
                            st.success("✅ Interview complete! Click below to get your evaluation.")
                            if st.button("Evaluate Interview"):
                                with st.spinner("Evaluating your responses..."):
                                    payload = {
                                        "transcript": st.session_state.interview_transcript,
                                        "role": role,
                                        "mode": st.session_state.interview_mode
                                    }
                                    print(f"payload is {payload}")
                                    print(f"transcript is {payload['transcript']}")

                                    result = requests.post(f"{FASTAPI_URL}/evaluates_interview/", json=payload)
                                    st.session_state.evaluation_result = result.json()["evaluation_report"]
                                    st.rerun()
                    if st.session_state.evaluation_result:
                        st.markdown("### Evaluation Report")
                        #st.text_area("Evaluation Report", st.session_state.evaluation_result, height=300)
                        render_evaluation_box(st.session_state.evaluation_result)
                        pdf_bytes = create_pdf(st.session_state.evaluation_result)
                        st.download_button(
                            label="Download Evaluation Report",
                            data=pdf_bytes,
                            file_name="evaluation_report.pdf",
                            mime="application/pdf"
                        )
                        if st.button("Start New Interview"):
                            for key in ["interview_mode", "interview_transcript", "interview_started", "interview_done", "last_question", "evaluation_result"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
        
        elif st.session_state.active_page == "Q and A":
            if "qa_query" not in st.session_state:
                st.session_state.qa_query = ""
            if "qa_result" not in st.session_state:
                st.session_state.qa_result = None
            st.session_state.qa_query = st.text_area("Type your interview-related question", value=st.session_state.qa_query, key="qa_input")
            if st.button("Ask", key="qa_button"):
                with st.spinner("Fetching answer..."):
                    try:
                        res = requests.post(
                            f"{FASTAPI_URL}/faq/",
                            json={
                                "query": st.session_state.qa_query,
                                "role": role,
                                "company": company
                            })
                        if res.status_code == 200:
                            st.session_state.qa_result = res.json()["data"]
                        elif res.status_code == 400:
                            st.warning(f"{res.json().get('detail', 'Your question was not relevant.')}")
                        else:
                            st.error(f"Server Error: {res.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Request failed: {str(e)}")
            if st.session_state.qa_result:
                result = st.session_state.qa_result
                st.success("Answer fetched!")
                st.markdown(f"### Query\n{result['faq_query']}")
                st.markdown("### FAQ Answer")
                st.markdown(result["faq_response"]["tasks_output"][0]["raw"])

                if "summary" in result:
                    st.markdown("### Summary")
                    st.markdown(result["summary"])

    elif st.session_state.active_page != "Home":
        st.warning("Please go to the Home page and select your role and dream company first.")


# ----------------- Main App -----------------
def main():
    st.title("Interview Preparation App")

    # Create user table if it doesn't exist
    create_users_table()

    token = st.session_state.get("token")

    if token:
        payload = decode_token(token)
        if payload:
            main_app(payload["username"])
        else:
            st.error("Session expired.")
            st.session_state.pop("token", None)
            st.rerun()
    elif st.session_state.get("show_reset"):
        forgot_password()
    else:
        tab1, tab2 = st.tabs(["Login", "Signup"])
        with tab1:
            login()
        with tab2:
            signup()

if __name__ == "__main__":
    main()
