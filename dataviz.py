import streamlit as st
import pandas as pd
import plotly.express as px
import json
import deepnote_toolkit

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

deepnote_toolkit.set_integration_env()

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
                fig = px.bar(
                    df_hist, 
                    x="Bin", 
                    y="Count", 
                    title=f"{col.capitalize()} Distribution",
                    template="plotly_white"
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#333333",
                    bargap=0.3,
                    bargroupgap=0.1
                )
                fig.update_traces(marker_color="#FF69B4")
                st.session_state.numeric_figs.append(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.histogram(
                    df, 
                    x=col, 
                    nbins=10, 
                    title=f"{col.capitalize()} Distribution",
                    template="plotly_white"
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#333333",
                    bargap=0.3,
                    bargroupgap=0.1
                )
                fig.update_traces(marker_color="#FF69B4")
                st.session_state.numeric_figs.append(fig)
                st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.histogram(
                df, 
                x=col, 
                nbins=10, 
                title=f"{col.capitalize()} Distribution",
                template="plotly_white"
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#333333",
                bargap=0.3,
                bargroupgap=0.1
            )
            fig.update_traces(marker_color="#FF69B4")
            st.session_state.numeric_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)
        
        if details.get("outlier_count", 0) > 0:
            fig = px.box(
                df, 
                y=col, 
                title=f"{col.capitalize()} Outliers",
                template="plotly_white"
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#333333"
            )
            fig.update_traces(marker_color="#FF69B4", line=dict(color="#FF69B4"))
            # Assuming outlier_figs is a global or session variable similar to numeric_figs
            outlier_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)


def plot_categorical(col, details, df):
    with st.container():
        st.subheader(f":pie_chart: {col.capitalize()} Distribution")
        # Define a custom color sequence with a beautiful pink accent and complementary hues.
        custom_colors = ["#FF69B4", "#FF85C1", "#FF9EC6", "#FFB8CB", "#FFD2D0"]
        
        if "top_categories" in details:
            data = details["top_categories"]
            df_bar = pd.DataFrame(list(data.items()), columns=["Category", "Count"])
            if len(data) <= 6:
                # Create a pie chart for few categories
                fig = px.pie(
                    df_bar, 
                    names="Category", 
                    values="Count",
                    title=f"{col.capitalize()} Distribution",
                    template="plotly_white",
                    hole=0.3,
                    color_discrete_sequence=custom_colors
                )
                # Update layout for a modern look
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#333333"
                )
            else:
                # Create a bar chart for many categories
                fig = px.bar(
                    df_bar, 
                    x="Category", 
                    y="Count",
                    title=f"Top {col.capitalize()} Categories",
                    template="plotly_white",
                    color_discrete_sequence=custom_colors
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#333333",
                    bargap=0.3,
                    bargroupgap=0.1
                )
                # For bar charts, if you want a single color accent:
                fig.update_traces(marker_color="#FF69B4")
                
            st.session_state.categorical_figs.append(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            uniq = df[col].value_counts().nlargest(10)
            df_bar = pd.DataFrame(uniq.items(), columns=["Category", "Count"])
            fig = px.bar(
                df_bar, 
                x="Category", 
                y="Count",
                title=f"Top 10 {col.capitalize()} Categories",
                template="plotly_white",
                color_discrete_sequence=custom_colors
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#333333",
                bargap=0.3,
                bargroupgap=0.1
            )
            fig.update_traces(marker_color="#FF69B4")
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
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "ai_insights" not in st.session_state:
        st.session_state.ai_insights = ""
    if "csv_upload" not in st.session_state:
        st.session_state.csv_upload = False

    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("")
    with col2:
        st.markdown('''
            <h1 style="font-size: 36px; font-weight: bold; color: #FF69B4; margin-bottom: 8px;">
                🌀Data Whisperer: Your AI-Powered Data Companion
            </h1>
        ''', unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:18px;color:#FF69B4;'>⚡ Transform raw data into actionable insights with zero effort—powered by AI, designed for you.</p>", 
            unsafe_allow_html=True
        )


    col_upload, dummy_col, col_demo = st.columns([1.5, 1, 1.5])
    with col_upload:
        uploaded_file = st.file_uploader("Upload a CSV or Excel (.xlsx) file", type=["csv", "xlsx"])

    with col_demo:
        st.write(" ")
        st.write(" ")
        st.write("Use demo csv file")
        use_demo = st.button("lung_disease_data.csv", help="Load a local sample CSV")
        if use_demo:
            st.session_state.csv_upload = True
        
    st.session_state.df = None
    data_set_name = "dataset.csv"
    if use_demo or st.session_state.csv_upload:
        data_set_name = "lung_disease_data.csv"
        try:
            with open(data_set_name, "rb") as f:
                st.session_state.df = read_and_validate_file(f)
            if st.session_state.df is None:
                st.error("Failed to load the demo CSV file.")
        except Exception as e:
            st.error(f"Error loading demo file: {e}")
    elif uploaded_file is not None:
        st.session_state.csv_upload = False
        file_name = uploaded_file.name.lower()
        data_set_name = file_name
        if file_name.endswith(".csv"):
            st.session_state.df = read_and_validate_file(uploaded_file)
            if st.session_state.df is None:
                st.error("Failed to read the CSV file.")
        elif file_name.endswith(".xlsx"):
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            if len(sheet_names) > 1:
                st.info("Multiple sheets found. Please select one below.")
                selected_sheet = st.selectbox("Select a sheet", sheet_names)
            else:
                selected_sheet = sheet_names[0]
            st.session_state.df = read_and_validate_file(uploaded_file, sheet_name=selected_sheet)
            if st.session_state.df is None:
                st.error("Failed to read the Excel file or invalid sheet selected.")

    if st.session_state.df is not None:
        st.session_state.df = clean_data(st.session_state.df)
        eda = enhanced_eda_json(st.session_state.df)
        st.markdown("## :clipboard: Dataset Overview")
        col_rows, col_cols, col_explorer, col_ppt = st.columns([1, 1, 1, 1])
        with col_rows:
            st.metric("Rows", f"{st.session_state.df.shape[0]:,}")
        with col_cols:
            st.metric("Columns", f"{st.session_state.df.shape[1]}")

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
                        df=st.session_state.df,
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

            st.session_state.numeric_figs = []
            st.session_state.categorical_figs = []
            st.session_state.correlation_figs = []
            st.session_state.time_series_figs = []
            st.session_state.outlier_figs = []

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
                        plot_numeric(col, det, st.session_state.df)
            with tab2:
                for col, det in eda["columns"].items():
                    if det.get("dtype", "").lower() == "object":
                        plot_categorical(col, det, st.session_state.df)

            with tab3:
                plot_correlations(st.session_state.df, eda)

            with tab4:
                plot_time_series(st.session_state.df)

            with tab5:
                st.markdown("### :mag: Outlier Detection")
                for col, det in eda["columns"].items():
                    if "numeric_stats" in det and det.get("outlier_count", 0) > 0:
                        fig = px.box(st.session_state.df, y=col, 
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
                if "ai_insights" in st.session_state and st.session_state.ai_insights == "":
                        eda_summary = json.dumps(eda)
                        prompt = f"""
                                You are a senior data analyst. Given the EDA results for {data_set_name}:

                                1. Identify key trends (minimum 3) with statistical evidence
                                2. Highlight actionable insights with clear business implications
                                3. Find anomalies requiring investigation
                                4. Suggest data-driven recommendations
                                5. Explain technical concepts in simple terms

                                EDA Analysis Results:
                                {eda_summary}

                                Specific requirements:
                                - Use bullet points with clear headers
                                - Prioritize business impact
                                - Include confidence levels where applicable
                                - use a around 8110 tokens if there is enough data we needed to provide indepth analysis so you needed to more tokens whereever needed
                                - Suggest next analysis steps
                                """
                        st.session_state.ai_insights = get_gemini_response(prompt, "lite")
                        st.markdown(st.session_state.ai_insights)
                elif st.session_state.ai_insights != "":
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
                                response = get_gemini_response("Your role is a data analyst and answers user questions so try to be conversational and here is Dataset context: " + json.dumps(eda) + "\nQuestion: " + q, "lite")
                            st.session_state.chat_history.append(("AI", response))
                            st.rerun()

                for sender, msg in st.session_state.chat_history:
                    alignment_class = "user" if sender == "User" else "ai"
                    bubble_class = "chat-user" if sender == "User" else "chat-ai"
                    st.markdown(
                        f'<div class="chat-row {alignment_class}"><div class="chat-bubble {bubble_class}">{msg}</div></div>',
                        unsafe_allow_html=True
                    )

                # Chat input form with enter-to-send and auto-clear
                with st.form(key="chat_form", clear_on_submit=True):
                    chat_input = st.text_input("Type your message here", key="chat_input")
                    submit_button = st.form_submit_button("Send")
                    if submit_button and chat_input:
                        st.session_state.chat_history.append(("User", chat_input))
                        with st.spinner("Generating response..."):
                            response = get_gemini_response("Your role is a data analyst and answers user questions so try to be conversational and here is Dataset context: " + json.dumps(eda) + "\nQuestion: " + chat_input, "flash")
                        st.session_state.chat_history.append(("AI", response))
                        st.rerun()
        
        else:
            st.session_state.numeric_figs = []
            st.session_state.categorical_figs = []
            st.session_state.correlation_figs = []
            st.session_state.time_series_figs = []
            st.session_state.outlier_figs = []
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

                    st.session_state.subset_df = execute_sql_on_df(st.session_state.df, sql_query, eda)
                    # clean the subset_df
                    st.session_state.subset_df = clean_data(st.session_state.subset_df)
                    st.session_state.subset_eda = enhanced_eda_json(st.session_state.subset_df)

                    if st.session_state.subset_df is not None and not st.session_state.subset_df.empty:

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
                            subset_eda_summary = json.dumps(st.session_state.subset_eda)
                            prompt = f"""
                                    You are a senior data analyst. Given the EDA results for a subset of {data_set_name}:

                                    1. Identify key trends (minimum 3) with statistical evidence
                                    2. Highlight actionable insights with clear business implications
                                    3. Find anomalies requiring investigation
                                    4. Suggest data-driven recommendations
                                    5. Explain technical concepts in simple terms

                                    EDA Analysis Results:
                                    ${subset_eda_summary}

                                    Specific requirements:
                                    - Use bullet points with clear headers
                                    - Prioritize business impact
                                    - Include confidence levels where applicable
                                    - Suggest next analysis steps
                                    - use a around 8110 tokens if there is enough data we needed to provide indepth analysis so you needed to more tokens whereever needed
                                    """
                            st.session_state.ai_insights = get_gemini_response(prompt, "flash")
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
                                            response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + q, "lite")
                                        st.session_state.chat_history.append(("AI", response))
                                        st.rerun()

                            for sender, msg in st.session_state.chat_history:
                                alignment_class = "user" if sender == "User" else "ai"
                                bubble_class = "chat-user" if sender == "User" else "chat-ai"
                                st.markdown(
                                    f'<div class="chat-row {alignment_class}"><div class="chat-bubble {bubble_class}">{msg}</div></div>',
                                    unsafe_allow_html=True
                                )

                            # Chat input form with enter-to-send and auto-clear
                            with st.form(key="chat_form", clear_on_submit=True):
                                chat_input = st.text_input("Type your message here", key="chat_input")
                                submit_button = st.form_submit_button("Send")
                                if submit_button and chat_input:
                                    st.session_state.chat_history.append(("User", chat_input))
                                    with st.spinner("Generating response..."):
                                        response = get_gemini_response("Your role is a data analyst and answers user questions so try to be conversational and here is Dataset context: " + json.dumps(eda) + "\nQuestion: " + chat_input, "flash")
                                    st.session_state.chat_history.append(("AI", response))
                                    st.rerun()

                    else:
                        st.warning("No results found or either the question was too ambiguos, Try a different query.")
                else:
                    st.warning("Please enter a query before running.")

    else:
        col1, col2 = st.columns([1.5, 3])
        with col2:
            st.markdown("")
        with col1:
            st.warning(":warning: Please upload a valid CSV file or an Excel sheet to begin")

if __name__ == "__main__":
    main()

st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #1e1e1e;  /* Dark background */
    color: #f0f0f0;  /* Light text */
    text-align: center;
    padding: 6px;  /* Increased padding slightly */
    font-size: 14px;  /* Slightly larger font */
    z-index: 999;
    border-top: 1px solid #444;  /* Darker border */
}
.footer a {
    color: #4ea8de;  /* Light blue link */
    text-decoration: none;
}
.footer a:hover {
    text-decoration: underline;
}
</style>
<div class="footer">
    👉 Learn more about Data Whisperer in the <a href="https://deepnote.com/app/something-8456/data-whisperer-dfad9c0a-7ad2-4b7a-aae7-043660da1b86" target="_blank">official documentation</a>.
</div>
""", unsafe_allow_html=True)
