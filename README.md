# 🛡️ FraudShield AI
### Intelligent Financial Fraud Detection & Risk Scoring Platform

> An industry-grade end-to-end Machine Learning platform for detecting fraudulent financial transactions using supervised learning, anomaly detection, explainable AI, and real-time risk scoring.

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-orange?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Container-blue?style=for-the-badge&logo=docker)
![MLflow](https://img.shields.io/badge/MLflow-MLOps-purple?style=for-the-badge)

</p>

---

## 📌 Overview

FraudShield AI is an enterprise-inspired fraud detection platform designed to simulate how banks and fintech companies identify suspicious financial transactions.

The system combines multiple Machine Learning models, anomaly detection algorithms, explainable AI, and a real-time prediction API to accurately classify fraudulent transactions while providing interpretable predictions.

Unlike traditional academic projects, FraudShield AI follows a production-style workflow that includes:

- Data Engineering
- Feature Engineering
- Machine Learning Pipeline
- Explainable AI
- REST API
- Interactive Dashboard
- MLOps

---

## 🚀 Key Features

✅ End-to-End Fraud Detection Pipeline

✅ Advanced Feature Engineering

✅ Multiple Machine Learning Models

✅ Hyperparameter Optimization

✅ Fraud Risk Scoring Engine

✅ Explainable AI (SHAP)

✅ Unsupervised Anomaly Detection

✅ FastAPI Prediction Service

✅ Streamlit Analytics Dashboard

✅ MLflow Experiment Tracking

✅ Dockerized Deployment

---

# 🏗️ System Architecture

<p align="center">

<img src="images/architecture.png" width="900">

</p>

```
            Transaction Data
                    │
                    ▼
        Data Validation & Cleaning
                    │
                    ▼
          Feature Engineering
                    │
                    ▼
         Fraud Detection Models
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 Risk Scoring           SHAP Explainability
        │
        ▼
 FastAPI Prediction API
        │
        ▼
 Streamlit Dashboard
```

---

# 📊 Dataset

The project combines **two financial datasets**.

### Dataset 1

Transaction-level information

- Transaction Amount
- Merchant ID
- Transaction Type
- Transaction Date
- Location
- Fraud Label

---

### Dataset 2

Customer Behaviour

- Customer ID
- Payment Method
- Device Type
- Merchant Category
- Average Spend
- Previous Transactions
- Account Age
- International Transaction
- Fraud Label

---

# 🧠 Machine Learning Pipeline

### Data Preprocessing

- Missing Value Handling
- Outlier Detection
- Encoding
- Scaling
- Date-Time Processing

---

### Feature Engineering

The model generates several domain-inspired features including:

- Transaction Velocity
- Merchant Risk Score
- Customer Spending Deviation
- Location Risk Score
- High Value Transaction Flag
- International Transaction Flag
- Payment Method Risk
- Customer Behaviour Features

---

### Models Compared

| Model | Status |
|---------|---------|
| Logistic Regression | ✅ |
| Decision Tree | ✅ |
| Random Forest | ✅ |
| XGBoost | ✅ |
| LightGBM | ✅ |
| CatBoost | ✅ |
| Extra Trees | ✅ |

---

### Anomaly Detection

- Isolation Forest
- Local Outlier Factor
- One-Class SVM *(Optional)*

---

# 📈 Dashboard

The Streamlit dashboard provides:

- 📊 Fraud Analytics
- 🌍 Fraud by Location
- 💳 Fraud by Merchant
- 📈 Transaction Trends
- 📉 Model Performance
- 🎯 Live Prediction
- 🧠 SHAP Explanations
- ⚠️ High Risk Alerts

---

# 🌐 API

Example Request

```http
POST /predict
```

```json
{
    "amount": 7500,
    "payment_method": "Credit Card",
    "merchant": "Amazon",
    "international": true
}
```

Example Response

```json
{
    "prediction": "Fraud",
    "fraud_probability": 0.94,
    "risk_score": 91,
    "risk_level": "HIGH"
}
```

---

# 📊 Model Performance

| Model | Accuracy | Precision | Recall | ROC-AUC |
|---------|-----------|-----------|----------|-----------|
| Logistic Regression | -- | -- | -- | -- |
| Random Forest | -- | -- | -- | -- |
| XGBoost | -- | -- | -- | -- |
| LightGBM | -- | -- | -- | -- |

*(Update after training the models.)*

---

# 📷 Screenshots

## Dashboard

![Dashboard](images/dashboard.png)

---

## Live Prediction

![Prediction](images/prediction.png)

---

## SHAP Explanation

![SHAP](images/shap.png)

---

## Confusion Matrix

![Confusion Matrix](images/confusion_matrix.png)

---

## ROC Curve

![ROC Curve](images/roc.png)

---

# 🛠️ Technology Stack

| Category | Technologies |
|------------|----------------|
| Language | Python |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Machine Learning | Scikit-learn, XGBoost, LightGBM, CatBoost |
| Explainability | SHAP |
| Backend | FastAPI |
| Dashboard | Streamlit |
| Experiment Tracking | MLflow |
| Containerization | Docker |
| Version Control | Git & GitHub |

---

# 📂 Project Structure

```
FraudShield-AI/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_EDA.ipynb
│   ├── 02_Feature_Engineering.ipynb
│   ├── 03_Model_Training.ipynb
│
├── src/
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── train.py
│   ├── evaluate.py
│   ├── explain.py
│   ├── anomaly_detection.py
│   └── predict.py
│
├── api/
│   └── app.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── models/
│
├── reports/
│
├── images/
│
├── tests/
│
├── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/FraudShield-AI.git
```

Navigate to the project

```bash
cd FraudShield-AI
```

Install dependencies

```bash
pip install -r requirements.txt
```

Launch the dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Start the API

```bash
uvicorn api.app:app --reload
```

---

# 🎯 Future Improvements

- Graph Neural Networks for Fraud Rings
- Real-Time Kafka Streaming
- Cloud Deployment (AWS/GCP/Azure)
- Drift Detection
- Continuous Model Retraining
- Email & SMS Fraud Alerts
- LLM-Powered Fraud Explanations

---

# 📌 Skills Demonstrated

- Machine Learning
- Fraud Analytics
- Feature Engineering
- Explainable AI (SHAP)
- FastAPI
- Streamlit
- Data Engineering
- Model Evaluation
- MLOps
- Docker
- GitHub Actions

---

# 👨‍💻 Author

Harsh Bajania

Machine Learning Engineer | Data Scientist

📧 harsh.bajania2@gmail.com

🔗 LinkedIn: https://www.linkedin.com/in/harsh-bajania-8565b1327/


---

## ⭐ If you found this project useful, consider giving it a star!
