"""Data loader, CSV validation, and dataset splitting utilities."""

from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

from data.schema import validate_event_log_schema


def load_event_log_csv(file_path_or_buffer) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Load and validate an event log from CSV.
    """
    try:
        df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        return False, f"CSV parsing error: {str(e)}", None

    is_valid, err, cleaned_df = validate_event_log_schema(df)
    if not is_valid:
        return False, err, None

    return True, None, cleaned_df


def split_dataset_by_case(
    df: pd.DataFrame,
    train_ratio: float = 0.60,
    val_ratio: float = 0.20,
    test_ratio: float = 0.20,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into Train, Validation, and Test sets strictly by case_id.
    Ensures that no case has events split across sets (preventing data leakage).
    """
    unique_cases = np.array(sorted(df["case_id"].unique()))
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_cases)

    n_total = len(unique_cases)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_cases = set(unique_cases[:n_train])
    val_cases = set(unique_cases[n_train:n_train + n_val])
    test_cases = set(unique_cases[n_train + n_val:])

    train_df = df[df["case_id"].isin(train_cases)].copy()
    val_df = df[df["case_id"].isin(val_cases)].copy()
    test_df = df[df["case_id"].isin(test_cases)].copy()

    return train_df, val_df, test_df

