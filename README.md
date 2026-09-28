# 📞 MicroSIP Call Analytics Dashboard

A cloud-based, interactive web application built with **Python** and **Streamlit** to automate the analysis of agent call logs from MicroSIP. This project transforms raw, unreadable CSV log files into actionable business intelligence metrics and visual insights in just one click.

🚀 **Live Demo:** [Insert your Streamlit Share Link Here]

---

## 🌟 Key Features

- **Instant Zero-Config Upload**: Simply drag and drop the raw `Log.csv` or `Calls.csv` exported from MicroSIP.
- **Smart Data Parsing**: Auto-detects column names for dates, call status, and durations dynamically—preventing app crashes from different MicroSIP versions.
- **Dynamic Date Filtering**: Filter analysis instantly for **"Today Only"** or a **"Custom Date Range"** to monitor real-time daily targets (e.g., tracking 400–500 calls/day).
- **Executive KPI Cards**: Displays high-level metrics including *Total Call Volume*, *Total Talk Time* (formatted in Hours/Minutes), and *Average Call Duration*.
- **Peak Hours Analysis**: Line chart visualization that identifies high-traffic calling hours to optimize agent shifting and rest breaks.
- **Interactive Data Explorer & Search**: Search specific phone numbers or contacts instantly with automatic duration formatting (`MM:SS`).
- **One-Click Report Export**: Download the filtered and cleaned dataset instantly back to a clean `.CSV` format.

---

## 🛠️ Tech Stack

- **Core Language:** Python 3.x
- **Data Manipulation:** Pandas
- **Web Framework & UI:** Streamlit
- **Deployment Platform:** Streamlit Community Cloud & GitHub

---

## 📁 Repository Structure

```text
microsip-call-counter/
├── app.py              # Main Streamlit application source code
├── requirements.txt    # Required python libraries for production deployment
└── README.md           # Project documentation and presentation guide
```

---

## 💻 Local Installation & Setup

If you want to run this project locally on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd microsip-call-counter
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```
   *The app will automatically open in your default browser at `http://localhost:8501`.*

---

## 💡 Business Impact & Value (For Presentation)

In a fast-paced Call Center or Telemarketing environment, supervisors waste hours manually parsing raw CSV files in Excel to calculate daily agent performance. 

This dashboard solves that exact problem by providing **Descriptive Analytics** instantly. The **Peak Hours Analysis** feature empowers operations management to make data-driven decisions—ensuring maximum agent availability during high-traffic windows, minimizing missed customer calls, and directly driving revenue.

---
*Developed as a Final Project showcase for the Hacktiv8 "Maju Bersama AI" Program.*
