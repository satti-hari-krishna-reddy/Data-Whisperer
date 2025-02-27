import pandas as pd
import numpy as np
import logging
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_and_validate_file(file_path):
    logging.info("Starting file upload and validation process...")
    try:
        if file_path.endswith('.csv'):
            logging.info("Detected CSV file. Reading file...")
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            logging.info("Detected Excel file. Reading file...")
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            if len(sheet_names) > 1:
                logging.info(f"Multiple sheets found: {sheet_names}")
                print("Please select a sheet to proceed:")
                for i, sheet in enumerate(sheet_names):
                    print(f"{i + 1}. {sheet}")
                choice = int(input("Enter the sheet number: ")) - 1
                selected_sheet = sheet_names[choice]
                logging.info(f"User selected sheet: {selected_sheet}")
                df = excel_file.parse(selected_sheet)
            else:
                logging.info(f"Only one sheet found: {sheet_names[0]}")
                df = excel_file.parse(sheet_names[0])
        else:
            logging.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return None
        
        if df.empty:
            logging.error("The file is empty. Please upload a valid dataset.")
            return None
        
        logging.info("File successfully read into a DataFrame.")
        return df
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return None

def clean_data(df):
    logging.info("Starting data cleaning process...")
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        logging.info(f"Initial numeric columns: {numeric_cols}")
        logging.info(f"Initial categorical columns: {categorical_cols}")
        logging.info(f"Initial date columns: {date_cols}")
        
        logging.info("Handling missing values...")
        for col in df.columns:
            missing_percentage = df[col].isnull().mean() * 100
            if missing_percentage > 50:
                logging.info(f"Dropping column '{col}' due to {missing_percentage:.2f}% missing values.")
                df.drop(col, axis=1, inplace=True)
            elif col in numeric_cols:
                logging.info(f"Imputing missing values in numeric column '{col}' with median.")
                df[col] = df[col].fillna(df[col].median())
            else:
                logging.info(f"Imputing missing values in categorical column '{col}' with mode.")
                df[col] = df[col].fillna(df[col].mode()[0])
        
        initial_rows = df.shape[0]
        df.drop_duplicates(inplace=True)
        final_rows = df.shape[0]
        logging.info(f"Removed {initial_rows - final_rows} duplicate rows.")
        
        for col in categorical_cols:
            try:
                converted = pd.to_datetime(df[col], errors='coerce')
                valid_ratio = converted.notnull().mean()
                if valid_ratio > 0.8:
                    df[col] = converted
                    logging.info(f"Converted column '{col}' to datetime.")
            except Exception as e:
                logging.info(f"Column '{col}' could not be converted to datetime: {e}")
        
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            logging.info(f"Column '{col}' has {outliers.shape[0]} outliers based on IQR method.")
        
        for col in categorical_cols:
            unique_vals = df[col].dropna().astype(str).str.strip().str.lower().unique()
            if set(unique_vals) == set(["yes", "no"]):
                mapping = {"yes": 1, "no": 0}
                df[col] = df[col].astype(str).str.strip().str.lower().map(mapping)
                logging.info(f"Converted boolean text in column '{col}' to 1/0 using yes/no mapping.")
            elif set(unique_vals) == set(["true", "false"]):
                mapping = {"true": 1, "false": 0}
                df[col] = df[col].astype(str).str.strip().str.lower().map(mapping)
                logging.info(f"Converted boolean text in column '{col}' to 1/0 using true/false mapping.")
        
        logging.info("Normalizing column names...")
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        logging.info(f"Normalized column names: {list(df.columns)}")
        
        logging.info("Data cleaning completed successfully.")
        return df
    except Exception as e:
        logging.error(f"Error during data cleaning: {e}")
        return None

def summarize_data(df):
    logging.info("Performing quick exploratory data analysis (EDA)...")
    try:
        logging.info(f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns.")
        missing_data = df.isnull().mean() * 100
        logging.info("Column-wise missing data percentages:")
        for col, percent in missing_data.items():
            logging.info(f"- {col}: {percent:.2f}%")
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            logging.info("Basic statistics for numeric columns:")
            stats = df[numeric_cols].agg(['mean', 'median', 'min', 'max']).T
            logging.info(stats)
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if categorical_cols:
            logging.info("Top categories for categorical columns:")
            for col in categorical_cols:
                top_categories = df[col].value_counts().head(5)
                logging.info(f"- {col}:")
                for category, count in top_categories.items():
                    logging.info(f"  - {category}: {count}")
        
        logging.info("Quick EDA completed successfully.")
    except Exception as e:
        logging.error(f"Error during quick EDA: {e}")

def export_cleaned_data(df, output_path):
    try:
        if output_path.endswith('.csv'):
            df.to_csv(output_path, index=False)
            logging.info(f"Cleaned data saved to CSV file: {output_path}")
        elif output_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
            logging.info(f"Cleaned data saved to Excel file: {output_path}")
        else:
            logging.error("Unsupported output format. Please use CSV or XLSX.")
    except Exception as e:
        logging.error(f"Error exporting cleaned data: {e}")

def export_enhanced_eda_json(df, eda_output_path):
    logging.info("Generating enhanced EDA summary...")
    try:
        eda_output_path = os.path.expanduser(eda_output_path)
        eda_summary = {}
        eda_summary["num_rows"] = df.shape[0]
        eda_summary["num_columns"] = df.shape[1]
        columns_info = {}
        for col in df.columns:
            col_info = {}
            col_info["dtype"] = str(df[col].dtype)
            missing_count = int(df[col].isnull().sum())
            missing_percent = round(df[col].isnull().mean() * 100, 2)
            col_info["missing_count"] = missing_count
            col_info["missing_percent"] = missing_percent
            
            if pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
                col_info["numeric_stats"] = {
                    "mean": desc.get("mean"),
                    "median": desc.get("50%"),
                    "min": desc.get("min"),
                    "max": desc.get("max"),
                    "std": desc.get("std"),
                    "25%": desc.get("25%"),
                    "75%": desc.get("75%")
                }
                col_info["skewness"] = df[col].skew()
                col_info["kurtosis"] = df[col].kurt()
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_count = int(df[(df[col] < lower_bound) | (df[col] > upper_bound)].shape[0])
                col_info["outlier_count"] = outlier_count
                col_info["outlier_bounds"] = {"lower_bound": lower_bound, "upper_bound": upper_bound}
                hist_counts, hist_bins = np.histogram(df[col].dropna(), bins=10)
                col_info["histogram"] = {
                    "bins": hist_bins.tolist(),
                    "counts": hist_counts.tolist()
                }
            elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                top_categories = df[col].value_counts().head(5).to_dict()
                col_info["top_categories"] = top_categories
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_info["min_date"] = str(df[col].min())
                col_info["max_date"] = str(df[col].max())
                try:
                    col_series = pd.to_datetime(df[col], errors='coerce')
                    monthly_counts = col_series.dt.to_period('M').value_counts().sort_index().to_dict()
                    if len(monthly_counts) <= 20:
                        col_info["monthly_distribution"] = {str(k): v for k, v in monthly_counts.items()}
                except Exception as e:
                    logging.info(f"Error computing monthly distribution for {col}: {e}")
            
            columns_info[col] = col_info
        
        eda_summary["columns"] = columns_info
        eda_summary["missing_data_overall"] = (df.isnull().mean() * 100).round(2).to_dict()
        duplicate_count = int(df.duplicated().sum())
        eda_summary["duplicate_rows"] = duplicate_count
        eda_summary["duplicate_percentage"] = round(duplicate_count / df.shape[0] * 100, 2)
        
        numeric_df = df.select_dtypes(include=["number"])
        if not numeric_df.empty:
            eda_summary["correlations"] = numeric_df.corr().round(2).to_dict()
            strong_corr = {}
            corr_matrix = numeric_df.corr().round(2)
            threshold = 0.3
            for col1 in corr_matrix.columns:
                for col2 in corr_matrix.index:
                    if col1 != col2 and abs(corr_matrix.loc[col2, col1]) >= threshold:
                        key = f"{col2} vs {col1}"
                        strong_corr[key] = corr_matrix.loc[col2, col1]
            eda_summary["strong_correlations"] = strong_corr
        else:
            eda_summary["correlations"] = {}
            eda_summary["strong_correlations"] = {}
        
        with open(eda_output_path, "w") as f:
            json.dump(eda_summary, f, indent=4)
        logging.info(f"Enhanced EDA summary saved to {eda_output_path}")
    except Exception as e:
        logging.error(f"Error generating enhanced EDA summary: {e}")

if __name__ == "__main__":
    file_path = input("Enter the path to your dataset (CSV or XLSX): ").strip()
    df = read_and_validate_file(file_path)
    
    if df is not None:
        cleaned_df = clean_data(df)
        if cleaned_df is not None:
            summarize_data(cleaned_df)
            logging.info("Preview of cleaned data:")
            print(cleaned_df.head())
            output_path = input("Enter the path to save the cleaned dataset (CSV or XLSX): ").strip()
            export_cleaned_data(cleaned_df, output_path)
            eda_output_path = input("Enter the path to save the enhanced EDA summary (JSON): ").strip()
            export_enhanced_eda_json(cleaned_df, eda_output_path)
