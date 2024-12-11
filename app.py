import streamlit as st  #Libreria StreamLit
import pandas as pd #Libreria Pandas tablas 
import psycopg2 #Conectase a la dase de Datos
from sqlalchemy import create_engine
from datetime import date # TIempo Fechas
from passlib.context import CryptContext #Encriptacion de las contrasenas
from dotenv import load_dotenv # Para variables de entorno
import os #Sistema Operativo
import re #

# Load environment variables from .env file
load_dotenv()

# Database connection details from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Create SQLAlchemy engine
#engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Initialize Passlib's CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash a password
def hash_password(password):
    return pwd_context.hash(password)

# Function to verify a password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to execute SELECT queries and return a DataFrame
def run_query(query, params=None):
    try:
        # Use psycopg2 for executing SELECT queries
        with psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        ) as connection:
            with connection.cursor() as cursor:
                # Execute the query with parameters
                cursor.execute(query, params)
                # Fetch all results
                results = cursor.fetchall()
                # Get column names from cursor
                columns = [desc[0] for desc in cursor.description]
                # Return results as a Pandas DataFrame
                return pd.DataFrame(results, columns=columns)
    except Exception as e:
        # Streamlit error handling
        st.error(f"Query failed: {e}")
        print(pd.DataFrame())
        return pd.DataFrame()

# Function to execute INSERT/UPDATE/DELETE queries
def run_non_query(query, params=None):
    try:
        # Using psycopg2 connection directly
        with psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
    except Exception as e:
        st.error(f"Database error: {e}")



# Function to verify user credentials
def verify_user(email, password):
    query = "SELECT id, password_hash FROM users WHERE email=%s"
    df = run_query(query, (email,))
    if df.empty:
        return None
    user_id = df['id'][0]
    stored_password_hash = df['password_hash'][0]
    if verify_password(password, stored_password_hash):
        return user_id
    return None

# Function to check password strength
def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# Function to register a new user
def register_user(name, email, password):
    # Check if email already exists
    check_query = "SELECT id FROM users WHERE email=%s"
    existing_user = run_query(check_query, (email,))
    if not existing_user.empty:
        st.error("Email already registered. Please use a different email or login.")
        return False

    # Hash the password using Passlib
    password_hash = hash_password(password)

    # Insert the new user into the database
    insert_query = """
        INSERT INTO users (name, email, password_hash)
        VALUES (%s, %s, %s)
    """
    try:
        run_non_query(insert_query, ( name, email,password_hash))
        print("HOla")
        st.success("Registration successful! You can now log in.")
        return True
    except Exception as e:
        st.error(f"An error occurred during registration: {e}")
        return False

# Initialize Streamlit session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.page = 'login'  # Possible values: 'login', 'register', 'dashboard'

# Function to display Login Form
def login():
    st.title("Nurses App - Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            user_id = verify_user(email, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.page = 'dashboard'
                st.success("Logged in successfully!")
            else:
                st.error("Invalid email or password.")

    st.markdown("---")
    if st.button("Register"):
        st.session_state.page = 'register'

# Function to display Registration Form
def register():
    st.title("Nurses App - Register")
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
    if submit:
        if not name or not email or not password or not confirm_password:
            st.error("Please fill in all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif not is_strong_password(password):
            st.error("Password must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters.")
        else:
            success = register_user(name, email, password)
            if success:
                st.session_state.page = 'login'

    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state.page = 'login'

# Function to display Patients
def show_patients():
    st.subheader("Your Patients")
    patients_df = run_query("SELECT id, first_name, last_name, dob FROM patients WHERE user_id=%s", (int(st.session_state.user_id),))
    if not patients_df.empty:
        st.dataframe(patients_df)
    else:
        st.info("No patients found. Add a new patient below.")

    with st.form("add_patient_form"):
        st.write("Add a New Patient")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        dob = st.date_input("Date of Birth", date.today())
        if st.form_submit_button("Add Patient"):
            if not first_name or not last_name:
                st.error("First name and Last name are required.")
            else:
                insert_query = """
                    INSERT INTO patients (user_id, first_name, last_name, dob)
                    VALUES (%s, %s, %s, %s)
                """
                run_non_query(insert_query, (int(st.session_state.user_id), first_name, last_name, dob))
                st.success("Patient added successfully!")
                st.session_state.page = 'dashboard'

# Function to display Medicines
def show_medicines():
    st.subheader("Medicines")
    meds_df = run_query("SELECT id, name, description FROM medicines")
    if not meds_df.empty:
        st.dataframe(meds_df)
    else:
        st.info("No medicines found. Add a new medicine below.")

    with st.form("add_medicine_form"):
        st.write("Add a New Medicine")
        name = st.text_input("Medicine Name")
        description = st.text_area("Description")
        if st.form_submit_button("Add Medicine"):
            if not name:
                st.error("Medicine name is required.")
            else:
                insert_query = """
                    INSERT INTO medicines (name, description)
                    VALUES (%s, %s)
                """
                run_non_query(insert_query, (name, description))
                st.success("Medicine added successfully!")
                st.session_state.page = 'dashboard'

# Function to display Frequencies
def show_frequencies():
    st.subheader("Frequencies (in Spanish)")
    freq_df = run_query("SELECT id, nombre, descripcion FROM frequencies")
    if not freq_df.empty:
        st.dataframe(freq_df)
    else:
        st.info("No frequencies found. Please populate the frequencies table.")

# Function to assign Medicine to Patient
def assign_medicine_to_patient():
    st.subheader("Assign Medicine to Patient")
    
    # Fetch patients, medicines, and frequencies
    patients_df = run_query("SELECT id, first_name, last_name FROM patients WHERE user_id=%s", (int(st.session_state.user_id),))
    meds_df = run_query("SELECT id, name FROM medicines")
    freq_df = run_query("SELECT id, nombre FROM frequencies")

    if patients_df.empty:
        st.warning("No patients found. Please add a patient first.")
        return
    if meds_df.empty:
        st.warning("No medicines found. Please add a medicine first.")
        return
    if freq_df.empty:
        st.warning("No frequencies found. Please add frequencies first.")
        return

    # Create selection options
    patient_options = {f"{row['first_name']} {row['last_name']}": row['id'] for _, row in patients_df.iterrows()}
    medicine_options = {row['name']: row['id'] for _, row in meds_df.iterrows()}
    frequency_options = {row['nombre']: row['id'] for _, row in freq_df.iterrows()}

    with st.form("assign_medicine_form"):
        selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
        selected_medicine = st.selectbox("Select Medicine", list(medicine_options.keys()))
        selected_frequency = st.selectbox("Select Frequency", list(frequency_options.keys()))
        start_date = st.date_input("Start Date", date.today())
        end_date = st.date_input("End Date", date.today())
        if st.form_submit_button("Assign Medicine"):
            insert_query = """
                INSERT INTO patient_medicines (patient_id, medicine_id, frequency_id, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s)
            """
            run_non_query(insert_query, (
                patient_options[selected_patient],
                medicine_options[selected_medicine],
                frequency_options[selected_frequency],
                start_date,
                end_date
            ))
            st.success("Medicine assigned to patient successfully!")
            st.session_state.page = 'dashboard'

# Function to display Dashboard with Navigation
def dashboard():
    st.title("Welcome to the Nurses App")
    
    # Sidebar with Logout and Navigation
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.page = 'login'
        return  # Exit the dashboard function to refresh the main script

    # Navigation Options
    nav = st.sidebar.radio("Go to", ["Patients", "Medicines", "Frequencies", "Assign Medicine", "Patient Medications"])

    if nav == "Patients":
        show_patients()
    elif nav == "Medicines":
        show_medicines()
    elif nav == "Frequencies":
        show_frequencies()
    elif nav == "Assign Medicine":
        assign_medicine_to_patient()
    elif nav == "Patient Medications":
        show_patient_medications()
        

# Main Application Logic
def main():
    if not st.session_state.logged_in:
        if st.session_state.page == 'login':
            login()
        elif st.session_state.page == 'register':
            register()
    else:
        dashboard()

# Function to display a patient's medications
def show_patient_medications():
    st.subheader("Patient Medications")
    
    # Fetch patients associated with the logged-in user
    patients_df = run_query("SELECT id, first_name, last_name FROM patients WHERE user_id=%s", (int(st.session_state.user_id),))
    
    if patients_df.empty:
        st.info("No patients found. Please add a patient first.")
        return
    
    # Create a selection dictionary for patients
    patient_options = {f"{row['first_name']} {row['last_name']}": row['id'] for _, row in patients_df.iterrows()}
    
    # Select a patient
    selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
    
    if selected_patient:
        patient_id = patient_options[selected_patient]
        
        # Query to fetch medications for the selected patient
        query = """
            SELECT 
                pm.id,
                m.name AS medicine_name,
                m.description AS medicine_description,
                f.nombre AS frequency,
                pm.start_date,
                pm.end_date
            FROM 
                patient_medicines pm
            JOIN 
                medicines m ON pm.medicine_id = m.id
            JOIN 
                frequencies f ON pm.frequency_id = f.id
            WHERE 
                pm.patient_id = %s
            ORDER BY 
                pm.start_date DESC
        """
        
        meds_df = run_query(query, (patient_id,))
        
        if not meds_df.empty:
            # Display medications in a table
            st.dataframe(meds_df.rename(columns={
                "medicine_name": "Medicine Name",
                "medicine_description": "Description",
                "frequency": "Frequency",
                "start_date": "Start Date",
                "end_date": "End Date"
            }))
        else:
            st.info("No medications assigned to this patient.")


if __name__ == "__main__":
    main()
