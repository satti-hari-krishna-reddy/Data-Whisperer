import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re

from smart_query import generate_sql_query, execute_sql_on_df
from generate_report import generate_eda_report_ppt
from clean_and_EDA_generate import enhanced_eda_json, clean_data, read_and_validate_file
from utils import get_gemini_response

# Set page configuration
st.set_page_config(
    page_title="Data Whisperer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

numeric_figs = []
categorical_figs = []
correlation_figs = []
time_series_figs = []
outlier_figs = []

# Custom CSS styling
st.markdown("""
    <style>
    /* Base styling */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #2B455C 0%, #1A2A3A 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        margin-bottom: 2rem;
    }
    
    /* Logo styling */
    .logo {
        width: 80px;
        height: 80px;
        background-image: url('https://via.placeholder.com/80x80/007BFF/FFFFFF?text=EDA+Pro');
        background-size: cover;
        border-radius: 12px;
        transition: transform 0.3s ease;
    }
    
    .logo:hover {
        transform: rotate(15deg) scale(1.05);
    }
    
    /* Navigation styling */
    .stTabs {
        margin-top: 1.5rem;
        border-bottom: 2px solid #2B455C;
    }
    
    .stTabs > div > button {
        color: #FAFAFA !important;
        background-color: #1A2A3A !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px 8px 0 0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs > div > button:hover {
        background-color: #2B455C !important;
    }
    
    /* Visualization container */
    .viz-container {
        background: #1A2A3A;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007BFF !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-2px);
    }
    
    /* Loading animation */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #007BFF;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    /* AI Insights styling */
    .ai-insights {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 18px;
        line-height: 1.6;
        color: #FAFAFA;
        padding: 15px;
        background-color: #1E1E2F;
        border-radius: 8px;
    }
    /* Chat UI styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        max-height: 500px;
        overflow-y: auto;
        padding: 15px;
        border: 1px solid #2B455C;
        border-radius: 8px;
        background-color: #12121D;
    }
    .chat-row {
        display: flex;
    }
    /* User messages on right; AI messages on left */
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.ai {
        justify-content: flex-start;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        max-width: 70%;
        word-wrap: break-word;
        margin-bottom: 5px;
    }
    .chat-user {
        background-color: #007BFF;
        color: #fff;
    }
    .chat-ai {
        background-color: #2B455C;
        color: #FAFAFA;
    }
    /* Pre-generated question buttons */
    .question-btn {
        background: #0056b3;
        border: none;
        color: #fff;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 5px;
        cursor: pointer;
        font-size: 16px;
    }
    .question-btn:hover {
        background: #007BFF;
    }
    /* Chat input styling */
    .chat-input {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .chat-input input[type="text"] {
        flex-grow: 1;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2B455C;
        background-color: #2B455C;
        color: #FAFAFA;
        font-size: 16px;
    }
    .chat-input input[type="text"]:focus {
        outline: none;
        box-shadow: 0 0 0 2px #007BFF;
    }
    .chat-input button {
        background: #007BFF;
        border: none;
        color: #fff;
        padding: 12px 20px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 16px;
    }
    .chat-input button:hover {
        background: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

def load_eda(file_obj):
    return json.load(file_obj)

def load_csv(file_obj):
    return pd.read_csv(file_obj)

def plot_numeric(col, details, df):
    with st.container():
        st.subheader(f":bar_chart: {col.capitalize()} Distribution")
        if "histogram" in details:
            bins = details["histogram"].get("bins", [])
            counts = details["histogram"].get("counts", [])
            if bins and counts:
                df_hist = pd.DataFrame({"Bin": bins[:-1], "Count": counts})
                fig = px.bar(df_hist, x="Bin", y="Count", 
                            title=f"{col.capitalize()} Distribution",
                            template="plotly_dark")
                fig.update_layout(
                    plot_bgcolor="#1A2A3A",
                    paper_bgcolor="#1A2A3A",
                    font_color="#FAFAFA"
                )
                st.session_state.numeric_figs.append(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.histogram(df, x=col, nbins=10, 
                                title=f"{col.capitalize()} Distribution",
                                template="plotly_dark")
        
                st.session_state.numeric_figs.append(fig)
                st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.histogram(df, x=col, nbins=10, 
                            title=f"{col.capitalize()} Distribution",
                            template="plotly_dark")
            st.session_state.numeric_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)
        
        if details.get("outlier_count", 0) > 0:
            fig = px.box(df, y=col, 
                        title=f"{col.capitalize()} Outliers",
                        template="plotly_dark")
            outlier_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)

def plot_categorical(col, details, df):
    with st.container():
        st.subheader(f":pie_chart: {col.capitalize()} Distribution")
        if "top_categories" in details:
            data = details["top_categories"]
            df_bar = pd.DataFrame(list(data.items()), 
                                columns=["Category", "Count"])
            if len(data) <= 6:
                fig = px.pie(df_bar, names="Category", values="Count",
                            title=f"{col.capitalize()} Distribution",
                            template="plotly_dark",
                            hole=0.3)
            else:
                fig = px.bar(df_bar, x="Category", y="Count",
                            title=f"Top {col.capitalize()} Categories",
                            template="plotly_dark")
            st.session_state.categorical_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            uniq = df[col].value_counts().nlargest(10)
            df_bar = pd.DataFrame(uniq.items(), 
                                columns=["Category", "Count"])
            fig = px.bar(df_bar, x="Category", y="Count",
                        title=f"Top 10 {col.capitalize()} Categories",
                        template="plotly_dark")
            st.session_state.categorical_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)

def plot_correlations(df, eda):
    with st.container():
        st.subheader(":chart_with_upwards_trend: Correlation Analysis")
        num_cols = [col for col, det in eda["columns"].items() 
                    if "numeric_stats" in det]
        
        if len(num_cols) < 2:
            st.warning("⚠️ Not enough numeric columns for correlation analysis")
            return
        
        corr = df[num_cols].corr()
        threshold = 0.3
        
        # Scatter plots
        plotted = set()
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                c1, c2 = num_cols[i], num_cols[j]
                r = corr.loc[c1, c2]
                if abs(r) >= threshold:
                    key = f"{c1}_{c2}"
                    if key not in plotted:
                        fig = px.scatter(df, x=c1, y=c2, 
                                        trendline="ols",
                                        title=f"{c1.capitalize()} vs {c2.capitalize()} (r = {r:.2f})",
                                        template="plotly_dark")
                        fig.update_layout(
                            plot_bgcolor="#1A2A3A",
                            paper_bgcolor="#1A2A3A",
                            font_color="#FAFAFA"
                        )
                        st.session_state.categorical_figs.append(fig)
                        st.plotly_chart(fig, use_container_width=True)
                        plotted.add(key)
        
        # Heatmap
        fig = px.imshow(corr,
                      text_auto=True,
                      aspect="auto",
                      title="Correlation Heatmap",
                      template="plotly_dark")
        fig.update_layout(
            plot_bgcolor="#1A2A3A",
            paper_bgcolor="#1A2A3A",
            font_color="#FAFAFA"
        )
        st.session_state.correlation_figs.append(fig)
        st.plotly_chart(fig, use_container_width=True)

def plot_time_series(df):
    with st.container():
        st.subheader(":clock1: Time Series Analysis")
        date_cols = df.select_dtypes(include=["datetime", "datetime64[ns]"]).columns.tolist()
        
        for col in df.columns:
            if "date" in col.lower() and col not in date_cols:
                try:
                    df[col] = pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    continue
        
        if not date_cols:
            st.warning("⚠️ No valid date columns detected")
            return
        
        for date_col in date_cols:
            st.subheader(f":calendar: Trend Over {date_col.capitalize()}")
            df_sorted = df.sort_values(by=date_col)
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            
            for num_col in numeric_cols:
                fig = px.line(df_sorted, 
                            x=date_col, 
                            y=num_col,
                            title=f"{num_col.capitalize()} Over Time",
                            template="plotly_dark")
                fig.update_layout(
                    plot_bgcolor="#1A2A3A",
                    paper_bgcolor="#1A2A3A",
                    font_color="#FAFAFA"
                )
                st.session_state.time_series_figs.append(fig)
                st.plotly_chart(fig, use_container_width=True)

def generate_pre_questions(eda):
    prompt = (
        "Here is the dataset context: " + json.dumps(eda) + "\n"
        "Analyze the dataset and generate exactly 5 concise, meaningful questions strictly related to its contents. "
        "Ensure they are short, impactful, and directly related to the dataset's structure, variables, and insights. "
        "Output them in JSON format as a list of strings, like this:\n"
        '["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]'
    )

    result = get_gemini_response(prompt).strip()

    # Regex to find the first JSON array in the text: [ ... ]
    array_match = re.search(r'(\[\s*\".*?\])', result, re.DOTALL)
    if array_match:
        raw_json = array_match.group(1).strip()
        try:
            questions = json.loads(raw_json)
            # Validate it's exactly 5 strings
            if isinstance(questions, list) and len(questions) == 5 and all(isinstance(q, str) for q in questions):
                return questions
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # Fallback: Provide default questions if the response is unreliable
    return [
        "What are the key trends in this dataset?",
        "Do you notice any significant outliers?",
        "How do the variables correlate?",
        "What time-based patterns are present?",
        "Any suggestions for further analysis?"
    ]


def main():

    # Initialize session state
    if "numeric_figs" not in st.session_state:
        st.session_state.numeric_figs = []
    if "categorical_figs" not in st.session_state:
        st.session_state.categorical_figs = []
    if "correlation_figs" not in st.session_state:
        st.session_state.correlation_figs = []
    if "time_series_figs" not in st.session_state:
        st.session_state.time_series_figs = []
    if "outlier_figs" not in st.session_state:
        st.session_state.outlier_figs = []
    if "subset_eda" not in st.session_state:
        st.session_state.subset_eda = {}
    if "subset_df" not in st.session_state:
        st.session_state.subset_df = pd.DataFrame()


    if "data_peek_mode" not in st.session_state:
        st.session_state.data_peek_mode = False

    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('''
            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #6200EA, #3700B3); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);">
                <span style="color: white; font-size: 24px; font-weight: bold; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">DW</span>
            </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
            <h1 style="font-size: 36px; font-weight: bold; color: #6200EA; margin-bottom: 8px;">
                Data Whisperer: Your AI-Powered Data Companion
            </h1>
        ''', unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:18px;color:#888;'>⚡ Transform raw data into actionable insights with zero effort—powered by AI, designed for you.</p>", 
            unsafe_allow_html=True
        )

    # eda_file = st.file_uploader("Upload EDA JSON file", type=["json"])
    # csv_file = st.file_uploader("Upload CSV dataset", type=["csv"])

    uploaded_file = st.file_uploader("Upload a CSV or Excel (.xlsx) file", type=["csv", "xlsx"])
    data_set_name = "dataset.csv"

    if uploaded_file is not None:
        file_name = uploaded_file.name.lower()
        data_set_name = file_name

        df = None

        if file_name.endswith(".csv"):
            df = read_and_validate_file(uploaded_file)
            if df is not None:
                st.success("CSV file loaded successfully!")
            else:
                st.error("Failed to read the CSV file.")
        
        elif file_name.endswith(".xlsx"):
            # Let the user pick a sheet if multiple exist
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) > 1:
                st.info("Multiple sheets found. Please select one below.")
                selected_sheet = st.selectbox("Select a sheet", sheet_names)
            else:
                selected_sheet = sheet_names[0]
            
            df = read_and_validate_file(uploaded_file, sheet_name=selected_sheet)
            if df is not None:
                st.success(f"Excel file loaded successfully! Using sheet: {selected_sheet}")
            else:
                st.error("Failed to read the Excel file or invalid sheet selected.")

        eda = enhanced_eda_json(df)

        st.markdown("## :clipboard: Dataset Overview")
        col_rows, col_cols, col_explorer, col_ppt = st.columns([1,1,1,1])
        with col_rows:
            st.metric("Rows", f"{df.shape[0]:,}")
        with col_cols:
            st.metric("Columns", f"{df.shape[1]}")

        with col_explorer:
            if not st.session_state.data_peek_mode:
                if st.button("Open Subset Explorer", key="open_data_peek"):
                    st.session_state.data_peek_mode = True
                    st.rerun()
            else:
                # Red button for "Close Subset Explorer"
                st.markdown(
                    """<style>
                    .red-button {
                        background-color: #FF4B4B;
                        color: white;
                        border: none;
                        padding: 10px 16px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 15px;
                    }
                    .red-button:hover {
                        background-color: #ff1f1f;
                    }
                    </style>""",
                    unsafe_allow_html=True
                )
                if st.button("Close Subset Explorer", key="close_data_peek"):
                    st.session_state.data_peek_mode = False
                    st.rerun()

        with col_ppt:
            if st.button("Generate PPT Report", key="generate_ppt"):
                if not st.session_state.data_peek_mode:

                    ppt_buffer = generate_eda_report_ppt(
                        eda_metadata=eda,
                        df=df,
                        numeric_figs=st.session_state.numeric_figs,       
                        categorical_figs=st.session_state.categorical_figs,    
                        correlation_figs=st.session_state.correlation_figs,    
                        time_series_figs=st.session_state.time_series_figs,      
                        outlier_figs=st.session_state.outlier_figs,         
                        dataset_name=data_set_name
                    )
                    st.download_button(
                        label="Download PPT",
                        data=ppt_buffer,
                        file_name="EDA_Full_Report.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
                else:

                    ppt_buffer = generate_eda_report_ppt(
                        eda_metadata=st.session_state.subset_eda,
                        df=st.session_state.subset_df,
                        numeric_figs=st.session_state.numeric_figs,       
                        categorical_figs=st.session_state.categorical_figs,    
                        correlation_figs=st.session_state.correlation_figs,    
                        time_series_figs=st.session_state.time_series_figs,      
                        outlier_figs=st.session_state.outlier_figs,         
                        dataset_name=data_set_name
                    )
                    st.download_button(
                        label="Download PPT (Subset)",
                        data=ppt_buffer,
                        file_name="EDA_Subset_Report.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )

        if not st.session_state.data_peek_mode:
            st.markdown("---")
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📊 Numerical Analysis",
                "📚 Categorical Analysis",
                "📈 Correlations",
                "⏳ Time Series",
                "🔍 Outliers",
                "📑 AI Insights",
                "🤖 Ask AI"
            ])
            with tab1:
                st.markdown("### :1234: Numerical Column Analysis")
                for col, det in eda["columns"].items():
                    if "numeric_stats" in det:
                        plot_numeric(col, det, df)
            with tab2:
                for col, det in eda["columns"].items():
                    if det.get("dtype", "").lower() == "object":
                        plot_categorical(col, det, df)

            with tab3:
                plot_correlations(df, eda)

            with tab4:
                plot_time_series(df)

            with tab5:
                st.markdown("### :mag: Outlier Detection")
                for col, det in eda["columns"].items():
                    if "numeric_stats" in det and det.get("outlier_count", 0) > 0:
                        fig = px.box(df, y=col, 
                                    title=f"{col.capitalize()} Outlier Analysis",
                                    template="plotly_dark")
                        fig.update_layout(
                            plot_bgcolor="#1A2A3A",
                            paper_bgcolor="#1A2A3A",
                            font_color="#FAFAFA"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab6:
                st.subheader("🤖 AI Insights")
                if "ai_insights" not in st.session_state:
                    #get_gemini_response("Analyze dataset: " + json.dumps(eda))
                    st.session_state.ai_insights = "hehe xD"
                st.markdown(st.session_state.ai_insights)
            
            with tab7:
                st.subheader("🤖 Ask AI")
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                if "selected_question" not in st.session_state:
                    st.session_state.selected_question = None

                if not st.session_state.chat_history and st.session_state.selected_question is None:
                    st.markdown("Select a question to start the chat:")
                    questions = generate_pre_questions(eda)
                    q_cols = st.columns(len(questions))
                    for i, q in enumerate(questions):
                        if q_cols[i].button(q, key=f"q_{i}"):
                            st.session_state.selected_question = q
                            st.session_state.chat_history.append(("User", q))
                            with st.spinner("Generating response..."):
                                response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + q)
                            st.session_state.chat_history.append(("AI", response))
                            st.rerun()

                for sender, msg in st.session_state.chat_history:
                    alignment_class = "user" if sender == "User" else "ai"
                    bubble_class = "chat-user" if sender == "User" else "chat-ai"
                    st.markdown(
                        f'<div class="chat-row {alignment_class}"><div class="chat-bubble {bubble_class}">{msg}</div></div>',
                        unsafe_allow_html=True
                    )

                with st.form(key="chat_form", clear_on_submit=True):
                    chat_input = st.text_input("Type your message here", key="chat_input")
                    submit_button = st.form_submit_button("Send")
                    if submit_button and chat_input:
                        st.session_state.chat_history.append(("User", chat_input))
                        with st.spinner("Generating response..."):
                            response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + chat_input)
                        st.session_state.chat_history.append(("AI", response))
                        st.rerun()
        
        else:
            st.markdown("---")
            empty_col, main_col, empty_col2 = st.columns([1,2,1])
            with main_col:
                st.markdown("### 🕵️ Explore Subset with Data Peek")
                st.markdown("Use natural language to filter the dataset and analyze specific insights.")

                user_query = st.text_input("Enter your question", key="datapeek_query", max_chars=200)
                run_analysis_clicked = st.button("Run Analysis", key="run_data_peek")

            if run_analysis_clicked:
                if user_query.strip():
                    sql_query = generate_sql_query(user_query, eda)

                    st.session_state.subset_df = execute_sql_on_df(df, sql_query, eda)
                    # clean the subset_df
                    st.session_state.subset_df = clean_data(st.session_state.subset_df)
                    st.session_state.subset_eda = enhanced_eda_json(st.session_state.subset_df)

                    if not st.session_state.subset_df.empty:
                        st.markdown("### 🔍 **Filtered Data Subset**")
                        st.dataframe(st.session_state.subset_df, use_container_width=True)
                        st.markdown("---")
                        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                            "📊 Numerical Analysis",
                            "📚 Categorical Analysis",
                            "📈 Correlations",
                            "⏳ Time Series",
                            "🔍 Outliers",
                            "📑 AI Insights",
                            "🤖 Ask AI"
                        ])
                        with tab1:
                            st.markdown("### :1234: Numerical Column Analysis")
                            for col, det in st.session_state.subset_eda["columns"].items():
                                if "numeric_stats" in det:
                                    plot_numeric(col, det, st.session_state.subset_df)
                        with tab2:
                            for col, det in st.session_state.subset_eda["columns"].items():
                                if det.get("dtype", "").lower() == "object":
                                    plot_categorical(col, det, st.session_state.subset_df)

                        with tab3:
                            plot_correlations(st.session_state.subset_df, st.session_state.subset_eda)

                        with tab4:
                            plot_time_series(st.session_state.subset_df)

                        with tab5:
                            st.markdown("### :mag: Outlier Detection")
                            for col, det in st.session_state.subset_eda["columns"].items():
                                if "numeric_stats" in det and det.get("outlier_count", 0) > 0:
                                    fig = px.box(st.session_state.subset_df, y=col, 
                                                title=f"{col.capitalize()} Outlier Analysis",
                                                template="plotly_dark")
                                    fig.update_layout(
                                        plot_bgcolor="#1A2A3A",
                                        paper_bgcolor="#1A2A3A",
                                        font_color="#FAFAFA"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                        
                        with tab6:
                            st.subheader("🤖 AI Insights")
                            if "ai_insights" not in st.session_state:
                                #get_gemini_response("Analyze dataset: " + json.dumps(eda))
                                st.session_state.ai_insights = get_gemini_response("Analyze dataset: " + json.dumps(st.session_state.subset_eda))
                            st.markdown(st.session_state.ai_insights)
                        
                        with tab7:
                            st.subheader("🤖 Ask AI")
                            if "chat_history" not in st.session_state:
                                st.session_state.chat_history = []
                            if "selected_question" not in st.session_state:
                                st.session_state.selected_question = None

                            if not st.session_state.chat_history and st.session_state.selected_question is None:
                                st.markdown("Select a question to start the chat:")
                                questions = generate_pre_questions(st.session_state.subset_eda)
                                q_cols = st.columns(len(questions))
                                for i, q in enumerate(questions):
                                    if q_cols[i].button(q, key=f"q_{i}"):
                                        st.session_state.selected_question = q
                                        st.session_state.chat_history.append(("User", q))
                                        with st.spinner("Generating response..."):
                                            response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + q)
                                        st.session_state.chat_history.append(("AI", response))
                                        st.rerun()

                            for sender, msg in st.session_state.chat_history:
                                alignment_class = "user" if sender == "User" else "ai"
                                bubble_class = "chat-user" if sender == "User" else "chat-ai"
                                st.markdown(
                                    f'<div class="chat-row {alignment_class}"><div class="chat-bubble {bubble_class}">{msg}</div></div>',
                                    unsafe_allow_html=True
                                )

                            with st.form(key="chat_form", clear_on_submit=True):
                                chat_input = st.text_input("Type your message here", key="chat_input")
                                submit_button = st.form_submit_button("Send")
                                if submit_button and chat_input:
                                    st.session_state.chat_history.append(("User", chat_input))
                                    with st.spinner("Generating response..."):
                                        response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + chat_input)
                                    st.session_state.chat_history.append(("AI", response))
                                    st.rerun()

                    else:
                        st.warning("No results found or either the question was too ambiguos, Try a different query.")
                else:
                    st.warning("Please enter a query before running.")

    else:
        st.warning(":warning: Please upload a valid CSV file or an Excel sheet to begin")

if __name__ == "__main__":
    main()
