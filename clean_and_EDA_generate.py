import pandas as pd
import numpy as np
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_and_validate_file(uploaded_file, sheet_name=None):
    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith('.xlsx'):
            excel_file = pd.ExcelFile(uploaded_file)
            if sheet_name is None:
                sheet_name = excel_file.sheet_names[0]
            df = excel_file.parse(sheet_name)
        else:
            logging.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return None
        
        if df.empty:
            logging.error("The file is empty. Please upload a valid dataset.")
            return None
    
        return df
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return None


def clean_data(df):
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        for col in df.columns:
            missing_percentage = df[col].isnull().mean() * 100
            if missing_percentage > 50:
                df.drop(col, axis=1, inplace=True)
            elif col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
        
        initial_rows = df.shape[0]
        df.drop_duplicates(inplace=True)
        final_rows = df.shape[0]
        
        for col in categorical_cols:
            try:
                converted = pd.to_datetime(df[col], errors='coerce')
                valid_ratio = converted.notnull().mean()
                if valid_ratio > 0.8:
                    df[col] = converted
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
        
        for col in categorical_cols:
            unique_vals = df[col].dropna().astype(str).str.strip().str.lower().unique()
            if set(unique_vals) == set(["yes", "no"]):
                mapping = {"yes": 1, "no": 0}
                df[col] = df[col].astype(str).str.strip().str.lower().map(mapping)
            elif set(unique_vals) == set(["true", "false"]):
                mapping = {"true": 1, "false": 0}
                df[col] = df[col].astype(str).str.strip().str.lower().map(mapping)
        
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        return df
    except Exception as e:
        logging.error(f"Error during data cleaning: {e}")
        return None


def enhanced_eda_json(df):
    try:
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
                    logging.info(f"Error generating monthly distribution for column '{col}': {e}")
            
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
        
        eda_string = json.dumps(eda_summary, indent=4)
        eda_obj = json.loads(eda_string)
        return eda_obj
    except Exception as e:
        return None

