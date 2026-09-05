import pandas as pd
from pathlib import Path


def load_products():
    """
    Load the cleaned headphone dataset.
    """

    # Project root = parent of src/
    project_root = Path(__file__).resolve().parent.parent

    data_path = project_root / "data" / "processed" / "headphones_clean.csv"

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at:\n{data_path}\n\n"
            "Make sure headphones_clean.csv exists inside "
            "data/processed/"
        )

    df = pd.read_csv(data_path)

    return df