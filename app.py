import streamlit as st
import mysql.connector
from datetime import datetime
import hashlib
import pandas as pd

# --- Database Connection ---
def get_connection():
    """Establishes connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="anand", 
            database="query_system"
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        st.stop()

# --- Security & User Management ---
def hash_password(password):
    """Converts a plain password into a secure hash."""
    return hashlib.sha256(str(password).encode()).hexdigest()

def authenticate_user(username, password, role):
    """Authenticates a user by checking username, hashed password, AND role."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE username = %s AND role = %s", (username, role))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_data and hash_password(password) == user_data['hashed_password']:
        return user_data
    return None

# --- Query Management Functions ---
def add_query(username, email, mobile, heading, description):
    """Adds a new query to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    current_time = datetime.now()
    cursor.execute("""
        INSERT INTO queries (username, email_id, mobile_number, query_heading, query_description, status, query_created_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (username, email, mobile, heading, description, "Open", current_time))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_queries_as_dataframe(status_filter):
    """Fetches queries with additional columns for the support dashboard."""
    conn = get_connection()
    
    query = f"""
        SELECT
            query_id,
            username AS client_username,
            email_id AS client_email,
            mobile_number AS client_mobile,
            query_heading,
            status,
            query_created_time AS date_raised,
            query_closed_time AS date_closed
        FROM queries
        WHERE status = '{status_filter}'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # query_closed_time column
    if 'date_closed' in df.columns:
        df['date_closed'] = df['date_closed'].apply(lambda x: '' if pd.isna(x) else x.strftime('%Y-%m-%d %H:%M:%S'))
        
    return df

def close_query(query_id):
    """Updates a query's status to 'Closed'."""
    conn = get_connection()
    cursor = conn.cursor()
    closed_time = datetime.now()
    cursor.execute("UPDATE queries SET status = 'Closed', query_closed_time = %s WHERE query_id = %s", (closed_time, query_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True

# --- UI Pages ---

def show_login_page():
    """Displays the login page with role selection."""
    st.title("Client Query Management System")
    st.subheader("Login to Your Account")
    
    
    role = st.selectbox("Select your role:", ["Client", "Support"])
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
       
        user_data = authenticate_user(username, password, role)
        
        if user_data:
            st.session_state['user_data'] = user_data
            st.rerun()
        else:
            st.error("Incorrect username, password, or role selected.")

def show_client_dashboard():
    """Displays the dashboard for the client."""
    st.header(f"Client Dashboard")
    st.write(f"Welcome, {st.session_state.user_data['username']}!")
    
    st.subheader("Submit a New Query")
    with st.form("client_query_form", clear_on_submit=True):
        email = st.text_input("Your Email ID")
        mobile = st.text_input("Your Mobile Number")
        heading = st.text_input("Query Heading")
        description = st.text_area("Describe your query")
        
        submitted = st.form_submit_button("Submit Query")
        if submitted:
            if add_query(st.session_state.user_data['username'], email, mobile, heading, description):
                st.success("Your query has been submitted successfully!")

def show_support_dashboard():
    """Displays the dashboard for the support team."""
    st.header(f"Support Dashboard")
    st.write(f"Welcome, {st.session_state.user_data['username']}!")
    
    st.subheader("Manage Client Queries")
    status_filter = st.radio("Filter queries by status:", ('Open', 'Closed'))

    queries_df = get_queries_as_dataframe(status_filter)

    if queries_df.empty:
        st.info(f"No {status_filter.lower()} queries found.")
    else:
        st.dataframe(queries_df, use_container_width=True)

        if status_filter == 'Open':
            st.subheader("Close an Open Query")
            open_query_options = {f"{row['query_id']} - {row['query_heading']}": row['query_id'] for index, row in queries_df.iterrows()}
            if open_query_options:
                selected_query_display = st.selectbox("Select a query to close:", open_query_options.keys())
                if st.button("Close Selected Query"):
                    query_id_to_close = open_query_options[selected_query_display]
                    if close_query(query_id_to_close):
                        st.success(f"Query ID {query_id_to_close} has been closed.")
                        st.rerun() 
            else:
                st.write("All open queries are displayed above.")



# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# Check if user is logged in
if st.session_state.user_data:
    st.sidebar.write(f"Logged in as: {st.session_state.user_data['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user_data = None
        st.rerun() 
        
   
    if st.session_state.user_data['role'] == 'Client':
        show_client_dashboard()
    elif st.session_state.user_data['role'] == 'Support':
        show_support_dashboard()
else:
    
    show_login_page()