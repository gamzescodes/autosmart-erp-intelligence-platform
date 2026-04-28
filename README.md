## 🏎️ AutoSmart ERP Intelligence Platform
An AI-supported ERP simulation platform designed specifically for automotive after-sales spare parts and logistics operations. 
This project demonstrates the transformation of traditional, transaction-based ERPs into data-driven, insight-oriented decision support systems.

## 📌 Project Overview
AutoSmart ERP is a conceptual prototype that bridges the gap between operational data and strategic decision-making. 
By integrating Large Language Models (LLMs) with relational database management, the system provides real-time risk assessment, inventory optimization, and automated executive reporting.

Key Vision: Moving beyond simple data entry towards an "Intelligent ERP" that interprets business movements and suggests proactive measures.

## 🚀 Core Functionalities

Order & Warehouse Management

Real-time Validation: Automated inventory checks during dealer-based order entry.
Stock Dynamics: Automatic stock updates and detailed warehouse movement logging.
Operational Risk: Real-time risk scoring for each transaction based on lead times and stock availability.

🧠 Decision Support System (DSS)
AI-Generated Insights: Context-aware management reports using the OpenAI API.

Automated Evaluation: Structured outputs covering operational assessments, risk evaluations, and recommended actions.

Fallback Logic: A robust Rule-Based Engine that ensures system continuity and consistent decision logic even if the AI service is unavailable.

📊 Executive Dashboard & Analytics

Performance Indicators: Live tracking of revenue, order status, and dealer performance.
Demand Segmentation: Deep-dive analysis by category, region, and automotive brand.
Risk Distribution: Visual overview of delayed or rejected orders.

## Data Explorer
Direct transparency into the relational structure:

Products & Suppliers
Dealer Transactions
Warehouse Movements
AI Decision Logs

## System Architecture
The platform is built on a modular, layered architecture to ensure scalability and reliability:

Data Layer: SQLite Relational Database for structured storage.
Business Logic Layer: Python-based ERP workflows and transaction management.
Application Layer: Interactive web interface powered by Streamlit.
Decision Layer: Hybrid engine (OpenAI GPT-4 + Deterministic Rule-based Logic).

## Technology Stack

Language: Python
Frontend: Streamlit
Database: SQLite / Pandas
AI Integration: OpenAI API
Deployment: Streamlit Community Cloud

## 🚦 Getting Started
Prerequisites
Python 3.9+
OpenAI API Key (optional, rule-based fallback will trigger otherwise)

## Installation
1. Clone the repository:
git clone https://github.com/yourusername/autosmart-erp.git
cd autosmart-erp

2. Install dependencies:
pip install -r requirements.txt

3. Configure Secrets:
OPENAI_API_KEY = "your_api_key_here"

5. Run the application:
streamlit run app.py


## Security & Reliability
API Management: Sensitive credentials are managed via environment variables and excluded from version control.

System Continuity: The fallback engine guarantees that decision support remains functional under all conditions.

## Author
Gamze Doyran, Industrial Engineering Student Focusing on Data Analytics, ERP System Design, and AI Integration in Supply Chain.

## License
This project is developed for educational and conceptual demonstration purposes.
