import streamlit as st
import jwt
from datetime import datetime, timedelta, UTC
import hashlib
import snowflake.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ----------------- Configuration -----------------
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

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
                password_hash STRING
            )
        """)

def add_user(username, password_hash):
    with get_snowflake_connection() as conn:
        cs = conn.cursor()
        try:
            cs.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
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

# ----------------- Auth Pages -----------------
def signup():
    st.subheader("Signup")
    new_user = st.text_input("Username", key="signup_user").strip()
    new_pass = st.text_input("Password", type="password", key="signup_pass")
    if st.button("Signup"):
        password_hash = hash_password(new_pass)
        success = add_user(new_user, password_hash)
        if success:
            st.success("User created. Please login.")
        else:
            st.error("Username already exists.")

def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user").strip()
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        stored_hash = get_user_password_hash(username)
        if stored_hash and stored_hash == hash_password(password):
            token = create_token(username)
            st.session_state["token"] = token
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def main_app(username):
    st.subheader(f"Welcome, {username}!")
    st.write("You are logged in.")
    if st.button("Logout"):
        st.session_state.pop("token", None)
        st.rerun()

# ----------------- Main App -----------------
def main():
    st.title("JWT Auth with Snowflake")

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
    else:
        tab1, tab2 = st.tabs(["Login", "Signup"])
        with tab1:
            login()
        with tab2:
            signup()

if __name__ == "__main__":
    main()
