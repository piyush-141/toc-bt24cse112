"""
Schema definitions and validation utilities for workflow event logs.
"""

from typing import Tuple, List, Optional
import pandas as pd


REQUIRED_COLUMNS = ["case_id", "timestamp", "event_type"]
OPTIONAL_COLUMNS = ["state_before", "state_after", "ground_truth_anomaly_type"]


def validate_event_log_schema(df: pd.DataFrame) -> Tuple[bool, Optional[str], pd.DataFrame]:
    """
    Validate that an uploaded or loaded dataframe conforms to the workflow event log schema.

    Args:
        df: Input pandas DataFrame.

    Returns:
        Tuple of (is_valid, error_message, cleaned_df)
    """
    if df is None or df.empty:
        return False, "Uploaded file is empty.", df

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return False, f"Missing mandatory schema columns: {', '.join(missing_cols)}. Required: {', '.join(REQUIRED_COLUMNS)}", df

    df_cleaned = df.copy()

    # Cast case_id and event_type to string and strip whitespace
    df_cleaned["case_id"] = df_cleaned["case_id"].astype(str).str.strip()
    df_cleaned["event_type"] = df_cleaned["event_type"].astype(str).str.strip()

    # Check for empty strings in key fields
    if (df_cleaned["case_id"] == "").any():
        return False, "Validation error: 'case_id' contains empty or whitespace-only values.", df

    if (df_cleaned["event_type"] == "").any():
        return False, "Validation error: 'event_type' contains empty or whitespace-only values.", df

    # Parse timestamps
    try:
        df_cleaned["timestamp"] = pd.to_datetime(df_cleaned["timestamp"], format="ISO8601")
    except Exception:
        try:
            df_cleaned["timestamp"] = pd.to_datetime(df_cleaned["timestamp"], format="mixed")
        except Exception as e:
            return False, f"Timestamp parsing failed: {str(e)}. Ensure timestamps are ISO 8601 or standard datetime formats.", df

    # Sort strictly chronologically within each case_id
    df_cleaned = df_cleaned.sort_values(by=["case_id", "timestamp"]).reset_index(drop=True)

    return True, None, df_cleaned
