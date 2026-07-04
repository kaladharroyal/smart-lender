import os
import mysql.connector
import pickle
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Paths to ML artifacts
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scale1.pkl')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'rdf.pkl')

# Load the scaler and model
scaler = None
model = None

if os.path.exists(SCALER_PATH):
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

# Helper function to get database connection
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="Kaladhar*011",
        database="smart_lender"
    )

# Initialize database matching smart_lender_erd.png
def init_db():
    # Connect to MySQL server first without selecting a database
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="Kaladhar*011"
    )
    cursor = conn.cursor()
    
    # Create database if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS smart_lender")
    cursor.execute("USE smart_lender")
    
    # 1. USER table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS USER (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            role VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 2. APPLICANT_PROFILE table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS APPLICANT_PROFILE (
            applicant_id INT AUTO_INCREMENT PRIMARY KEY,
            gender VARCHAR(50) NOT NULL,
            married VARCHAR(50) NOT NULL,
            education VARCHAR(100) NOT NULL,
            self_employed VARCHAR(50) NOT NULL,
            dependents INT NOT NULL,
            property_area VARCHAR(100) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 3. CREDIT_HISTORY table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CREDIT_HISTORY (
            credit_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT NOT NULL,
            credit_score DOUBLE NOT NULL,
            credit_history_status INT NOT NULL,
            FOREIGN KEY (applicant_id) REFERENCES APPLICANT_PROFILE(applicant_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 4. LOAN_APPLICATION table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS LOAN_APPLICATION (
            loan_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT NOT NULL,
            income DOUBLE NOT NULL,
            coapplicant_income DOUBLE NOT NULL,
            loan_amount DOUBLE NOT NULL,
            loan_term INT NOT NULL,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (applicant_id) REFERENCES APPLICANT_PROFILE(applicant_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 5. MODEL table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MODEL (
            model_id INT AUTO_INCREMENT PRIMARY KEY,
            model_name VARCHAR(100) NOT NULL,
            algorithm VARCHAR(100) NOT NULL,
            training_accuracy DOUBLE NOT NULL,
            testing_accuracy DOUBLE NOT NULL,
            file_path VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # 6. PREDICTION_RESULT table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PREDICTION_RESULT (
            prediction_id INT AUTO_INCREMENT PRIMARY KEY,
            loan_id INT NOT NULL,
            model_id INT NOT NULL,
            prediction_status VARCHAR(50) NOT NULL,
            probability_score DOUBLE NOT NULL,
            prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES LOAN_APPLICATION(loan_id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES MODEL(model_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    ''')
    
    # Insert default model if not exists
    cursor.execute("SELECT COUNT(*) FROM MODEL WHERE model_id = 1")
    row = cursor.fetchone()
    if row:
        count = row.get('COUNT(*)') if isinstance(row, dict) else row[0]
        if count == 0:
            cursor.execute('''
                INSERT INTO MODEL (model_id, model_name, algorithm, training_accuracy, testing_accuracy, file_path)
                VALUES (1, 'Random Forest', 'RandomForestClassifier', 0.8402, 0.8402, 'scale1.pkl & rdf.pkl')
            ''')
        
    conn.commit()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Error initializing MySQL database: {e}")

@app.route('/')
def index():
    try:
        # Load past predictions by joining normalized tables
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                l.loan_id, 
                a.gender, 
                a.married, 
                CASE WHEN a.dependents = 3 THEN '3+' ELSE CAST(a.dependents AS CHAR) END as dependents, 
                a.education, 
                a.self_employed, 
                CAST(l.income AS SIGNED) as income, 
                CAST(l.coapplicant_income AS SIGNED) as coapplicant_income, 
                l.loan_amount, 
                l.loan_term, 
                CASE WHEN c.credit_history_status = 1 THEN 'Good' ELSE 'Bad' END as credit_history, 
                a.property_area, 
                p.prediction_status, 
                DATE_FORMAT(p.prediction_time, '%Y-%m-%d %H:%i:%s') as prediction_time,
                ROUND(p.probability_score * 100, 1) as probability_score
            FROM LOAN_APPLICATION l
            JOIN APPLICANT_PROFILE a ON l.applicant_id = a.applicant_id
            JOIN CREDIT_HISTORY c ON a.applicant_id = c.applicant_id
            JOIN PREDICTION_RESULT p ON l.loan_id = p.loan_id
            ORDER BY l.loan_id DESC
        ''')
        history = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Error reading history from MySQL: {e}")
        history = []
        
    return render_template('index.html', history=history)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if ML models are properly loaded
        if scaler is None or model is None:
            return "Error: Machine Learning models are not loaded.", 500

        # Get raw form data for DB storage and visualization
        gender_raw = request.form.get('gender')
        married_raw = request.form.get('married')
        dependents_raw = request.form.get('dependents')
        education_raw = request.form.get('education')
        self_employed_raw = request.form.get('self_employed')
        applicant_income_raw = request.form.get('applicant_income')
        coapplicant_income_raw = request.form.get('coapplicant_income')
        loan_amount_raw = request.form.get('loan_amount')
        loan_amount_term_raw = request.form.get('loan_amount_term')
        credit_history_raw = request.form.get('credit_history')
        property_area_raw = request.form.get('property_area')

        # Basic input validation to narrow None types for compiler/linter
        if (gender_raw is None or married_raw is None or dependents_raw is None or 
            education_raw is None or self_employed_raw is None or applicant_income_raw is None or 
            coapplicant_income_raw is None or loan_amount_raw is None or loan_amount_term_raw is None or 
            credit_history_raw is None or property_area_raw is None):
            return "Error: Missing input fields.", 400

        # Parse inputs
        applicant_income = int(applicant_income_raw)
        coapplicant_income = int(coapplicant_income_raw)
        loan_amount = float(loan_amount_raw)
        loan_amount_term = int(loan_amount_term_raw)

        # Map features according to the training schema
        gender_val = 1 if gender_raw == 'Female' else 0
        married_val = 1 if married_raw == 'Yes' else 0
        dependents_val = int(dependents_raw) if dependents_raw != '3+' else 3
        education_val = 1 if education_raw == 'Graduate' else 0
        self_employed_val = 1 if self_employed_raw == 'Yes' else 0
        credit_history_val = 1 if credit_history_raw == 'Good' else 0
        property_area_map = {'Urban': 2, 'Semiurban': 1, 'Rural': 0}
        property_area_val = property_area_map.get(property_area_raw, 0)

        # Assemble features DataFrame
        feature_names = ['Gender', 'Married', 'Dependents', 'Education', 'Self_Employed', 
                         'ApplicantIncome', 'CoapplicantIncome', 'LoanAmount', 
                         'Loan_Amount_Term', 'Credit_History', 'Property_Area']
        features_df = pd.DataFrame([[
            gender_val,
            married_val,
            dependents_val,
            education_val,
            self_employed_val,
            applicant_income,
            coapplicant_income,
            loan_amount,
            loan_amount_term,
            credit_history_val,
            property_area_val
        ]], columns=feature_names, dtype=float)

        # Scale features using the StandardScaler
        scaled_features = scaler.transform(features_df)
        scaled_features_df = pd.DataFrame(scaled_features, columns=feature_names)

        # Run prediction and probability score
        prediction = model.predict(scaled_features_df)[0]
        probability = model.predict_proba(scaled_features_df)[0][1]
        status = "Approved" if prediction == 1 else "Rejected"

        # Save to MySQL database according to the ERD normalized schema
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insert applicant profile
        cursor.execute('''
            INSERT INTO APPLICANT_PROFILE (gender, married, education, self_employed, dependents, property_area)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (gender_raw, married_raw, education_raw, self_employed_raw, dependents_val, property_area_raw))
        applicant_id = cursor.lastrowid
        
        # 2. Insert credit history
        credit_score = 800.0 if credit_history_raw == 'Good' else 400.0
        cursor.execute('''
            INSERT INTO CREDIT_HISTORY (applicant_id, credit_score, credit_history_status)
            VALUES (%s, %s, %s)
        ''', (applicant_id, credit_score, credit_history_val))
        
        # 3. Insert loan application
        cursor.execute('''
            INSERT INTO LOAN_APPLICATION (applicant_id, income, coapplicant_income, loan_amount, loan_term)
            VALUES (%s, %s, %s, %s, %s)
        ''', (applicant_id, applicant_income, coapplicant_income, loan_amount, loan_amount_term))
        loan_id = cursor.lastrowid
        
        # 4. Insert prediction result
        cursor.execute('''
            INSERT INTO PREDICTION_RESULT (loan_id, model_id, prediction_status, probability_score)
            VALUES (%s, 1, %s, %s)
        ''', (loan_id, status, float(probability)))
        
        conn.commit()
        conn.close()

        # Render result page
        return render_template('result.html', 
                               status=status,
                               probability=f"{probability * 100:.1f}%",
                               applicant={
                                   'gender': gender_raw,
                                   'married': married_raw,
                                   'dependents': dependents_raw,
                                   'education': education_raw,
                                   'self_employed': self_employed_raw,
                                   'applicant_income': applicant_income,
                                   'coapplicant_income': coapplicant_income,
                                   'loan_amount': loan_amount,
                                   'loan_amount_term': loan_amount_term,
                                   'credit_history': credit_history_raw,
                                   'property_area': property_area_raw
                               })
    except Exception as e:
        return f"Error during prediction: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
