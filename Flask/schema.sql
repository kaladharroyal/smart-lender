-- MySQL Database Schema for Smart Lender
-- Matches smart_lender_erd.png

CREATE DATABASE IF NOT EXISTS smart_lender;
USE smart_lender;

-- 1. USER TABLE
CREATE TABLE IF NOT EXISTS USER (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. APPLICANT_PROFILE TABLE
CREATE TABLE IF NOT EXISTS APPLICANT_PROFILE (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    gender VARCHAR(50) NOT NULL,
    married VARCHAR(50) NOT NULL,
    education VARCHAR(100) NOT NULL,
    self_employed VARCHAR(50) NOT NULL,
    dependents INT NOT NULL,
    property_area VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. CREDIT_HISTORY TABLE
CREATE TABLE IF NOT EXISTS CREDIT_HISTORY (
    credit_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    credit_score DOUBLE NOT NULL,
    credit_history_status INT NOT NULL,
    FOREIGN KEY (applicant_id) REFERENCES APPLICANT_PROFILE(applicant_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. LOAN_APPLICATION TABLE
CREATE TABLE IF NOT EXISTS LOAN_APPLICATION (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    income DOUBLE NOT NULL,
    coapplicant_income DOUBLE NOT NULL,
    loan_amount DOUBLE NOT NULL,
    loan_term INT NOT NULL,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES APPLICANT_PROFILE(applicant_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. MODEL TABLE
CREATE TABLE IF NOT EXISTS MODEL (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    training_accuracy DOUBLE NOT NULL,
    testing_accuracy DOUBLE NOT NULL,
    file_path VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. PREDICTION_RESULT TABLE
CREATE TABLE IF NOT EXISTS PREDICTION_RESULT (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    model_id INT NOT NULL,
    prediction_status VARCHAR(50) NOT NULL,
    probability_score DOUBLE NOT NULL,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES LOAN_APPLICATION(loan_id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES MODEL(model_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default model info on creation
INSERT INTO MODEL (model_id, model_name, algorithm, training_accuracy, testing_accuracy, file_path)
VALUES (1, 'Random Forest', 'RandomForestClassifier', 0.8402, 0.8402, 'scale1.pkl & rdf.pkl')
ON DUPLICATE KEY UPDATE model_name = VALUES(model_name);
