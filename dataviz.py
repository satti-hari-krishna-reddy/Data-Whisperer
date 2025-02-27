import streamlit as st
import pandas as pd
import plotly.express as px
import json
import google.generativeai as genai
import os

from smart_query import generate_sql_query, execute_sql_on_df

# Set page configuration
st.set_page_config(
    page_title="EDA Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

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
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.histogram(df, x=col, nbins=10, 
                                title=f"{col.capitalize()} Distribution",
                                template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.histogram(df, x=col, nbins=10, 
                            title=f"{col.capitalize()} Distribution",
                            template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        if details.get("outlier_count", 0) > 0:
            fig = px.box(df, y=col, 
                        title=f"{col.capitalize()} Outliers",
                        template="plotly_dark")
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            uniq = df[col].value_counts().nlargest(10)
            df_bar = pd.DataFrame(uniq.items(), 
                                columns=["Category", "Count"])
            fig = px.bar(df_bar, x="Category", y="Count",
                        title=f"Top 10 {col.capitalize()} Categories",
                        template="plotly_dark")
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
    # Header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div class="logo"></div>', unsafe_allow_html=True)
    with col2:
        st.title("EDA Pro: Automated Analysis Dashboard")
        st.markdown(
            "<p style='font-size: 16px; color: #888;'>🚀 The ultimate tool for data exploration and visualization</p>", 
            unsafe_allow_html=True
        )
    
    # File uploaders
    eda_file = st.file_uploader("Upload EDA JSON file", type=["json"])
    csv_file = st.file_uploader("Upload CSV dataset", type=["csv"])
    
    if eda_file and csv_file:
        eda = load_eda(eda_file)
        df = load_csv(csv_file)
        
        st.markdown("## :clipboard: Dataset Overview")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Rows", f"{df.shape[0]:,}")
        with col_info2:
            st.metric("Columns", f"{df.shape[1]}")
        
                # Tabs with enhanced styling
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📊 Numerical Analysis",
            "📚 Categorical Analysis",
            "📈 Correlations",
            "⏳ Time Series",
            "🔍 Outliers",
            "📑 AI Insights",
            "🤖 Ask AI",
            "🔍📊 Data Peek"
        ])
            # Tab 1: Data Visualization
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
                st.session_state.ai_insights = get_gemini_response("Analyze dataset: " + json.dumps(eda))
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

            # Chat input form with enter-to-send and auto-clear
            with st.form(key="chat_form", clear_on_submit=True):
                chat_input = st.text_input("Type your message here", key="chat_input")
                submit_button = st.form_submit_button("Send")
                if submit_button and chat_input:
                    st.session_state.chat_history.append(("User", chat_input))
                    with st.spinner("Generating response..."):
                        response = get_gemini_response("Dataset context: " + json.dumps(eda) + "\nQuestion: " + chat_input)
                    st.session_state.chat_history.append(("AI", response))
                    st.rerun()

        with tab8:
            st.subheader("🔍📊 Data Peek")
            user_query = st.text_input("Enter your query for Data Peek")
            if st.button("Run Query"):
                sql_query = generate_sql_query(user_query, eda)
                subset_df = execute_sql_on_df(df, sql_query, eda)
                st.dataframe(subset_df)
    else:
        st.warning(":warning: Please upload both EDA JSON and CSV files to begin")
    
if __name__ == "__main__":
    main()
