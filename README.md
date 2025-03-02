# 🚀 Data Whisperer: AI-Powered Data Analysis & Insights

[![Streamlit](https://img.shields.io/badge/Streamlit-0E1117?logo=streamlit)](https://streamlit.io)
[![GitHub Stars](https://img.shields.io/github/stars/satti-hari-krishna-reddy/Data-Whisperer?style=social)](https://github.com/satti-hari-krishna-reddy/Data-Whisperer)

**Data Whisperer** is an AI-driven tool that automates exploratory data analysis (EDA), generates actionable insights, and enables natural language querying of datasets. Built for the **Deepnote x Streamlit Hackathon**, it combines the power of AI (Google Gemini) with interactive visualizations and professional reporting.

---

## 🌟 Why Did We Build This?
Traditional EDA tools require technical expertise and hours of manual work. Data Whisperer solves this by:

- **Democratizing Data Analysis**: Non-technical users can explore data with zero coding.
- **Speed**: Get insights and visualizations in seconds, not hours.
- **Actionability**: AI-generated recommendations and exportable reports.
- **Focus**: Query subsets of data for targeted analysis.

---

## 🛠️ Key Features

### 1. **Automated EDA**
- Instantly generates statistical summaries, histograms, correlations, and outlier detection.
- Handles missing values, duplicates, and data types automatically.

### 2. **AI-Powered Insights**
- **Precomputed Insights**: AI analyzes your dataset and highlights key patterns.
- **Conversational Chat**: Ask follow-up questions and get instant answers.
- **Dynamic Recommendations**: AI suggests next steps based on your data.

### 3. **🔍 DataPeek (Natural Language Querying)**
- Ask questions like *"Show students with grades above 90"* or *"Find customers from California with purchases > $500"*.
- AI converts your query into SQL-like syntax, extracts subsets, and runs EDA on them.
- Dedicated AI insights and visualizations for subsets.

### 4. **📊 Export to PowerPoint**
- Generate professional reports with:
  - AI-generated insights.
  - Visualizations (histograms, box plots, heatmaps).
  - Summary statistics and recommendations.
- Perfect for sharing with stakeholders.

### 5. **Modern UI/UX**
- Dark theme with gradient accents.
- Interactive Plotly visualizations.
- Collapsible sections and expandable insights.

---

## 📦 How It Works

### Workflow
1. **Upload Data**: CSV/Excel file + optional EDA JSON (for precomputed stats).
2. **Explore Visualizations**: Navigate tabs for numerical, categorical, and correlation analysis.
3. **Ask Questions**: Use the AI chat or DataPeek to analyze subsets.
4. **Export Results**: Generate PowerPoint reports with one click.

### Tech Stack
- **Frontend**: Streamlit (interactive UI/UX).
- **AI Engine**: Google Gemini (insights generation).
- **Visualizations**: Plotly Express.
- **Reporting**: Python-PPTX.
- **Data Processing**: Pandas, NumPy.

---

## 🚀 Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/satti-hari-krishna-reddy/Data-Whisperer
cd Data-Whisperer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Gemini API Key
Get your API key from Google AI Studio and export it as an environment variable:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the App
```bash
streamlit run dataviz.py
```

### 5. Access the Dashboard
Open your browser and go to:
```bash
http://localhost:8501
```

### 6. Use a Sample Dataset
Try the included `Students_Grading_Dataset.csv` or upload your own!

---

## 📊 Sample Data Analysis
The EDA JSON file reveals a dataset of 5,000 students with 23 columns, including:

- **Performance Metrics**: Grades, study hours, attendance.
- **Demographics**: Age, gender, department.
- **Behavioral Data**: Stress levels, sleep hours, extracurricular activities.

### Key Insights from AI:
- 59.8% of students scored "A" grades (potential grade inflation).
- Weak correlations between variables (suggests non-linear relationships).
- 10.3% of students lack internet access at home.

---

## 📈 DataPeek in Action

### Example Queries:
```text
"Show students in CS department with final_score > 90"
"Find students with stress_level > 7 and sleep_hours < 6"
"Analyze students without internet access"
```

### AI Response:
- Generates SQL-like query.
- Runs EDA on the subset.
- Provides insights + visualizations.

---

## 📝 Export to PowerPoint
Generate an AI-powered PowerPoint report with insights and charts.

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
