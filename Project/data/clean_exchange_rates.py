from pathlib import Path
import pandas as pd

# Locate the original CSV beside this script.
PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_DIR / "eurofxref-hist.csv"

OUTPUT_DIR = PROJECT_DIR / "cleaning_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Read all fields as text initially to make validation explicit.
raw = pd.read_csv(
    INPUT_FILE,
    dtype="string",
    skipinitialspace=True,
    na_values=["N/A"],
    encoding="utf-8-sig"
)

# Remove extra spaces from column names.
raw.columns = raw.columns.str.strip()

original_rows = len(raw)

print("Original dataset shape:", raw.shape)
print("Available columns:", raw.columns.tolist())
print(raw.head())


CURRENCIES = [
    "CNY", "USD", "JPY", "GBP",
    "HKD", "CHF", "AUD", "CAD"
]

REQUIRED_COLUMNS = ["Date"] + CURRENCIES

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in raw.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns are missing: {missing_columns}"
    )

df = raw[REQUIRED_COLUMNS].copy()

# Remove spaces around field values.
for column in REQUIRED_COLUMNS:
    df[column] = df[column].str.strip()

# Recognize additional explicit missing markers after trimming.
df = df.replace({
    "": pd.NA,
    "N/A": pd.NA
})

print("Selected columns:", df.columns.tolist())


# The ECB download uses YYYY/MM/DD; some copies use YYYY-MM-DD.
# Accept both explicitly so the script stays reproducible across downloads.
parsed_dates = pd.to_datetime(
    df["Date"],
    format="%Y-%m-%d",
    errors="coerce"
)

if parsed_dates.isna().any():
    fallback_dates = pd.to_datetime(
        df["Date"],
        format="%Y/%m/%d",
        errors="coerce"
    )
    parsed_dates = parsed_dates.fillna(fallback_dates)

invalid_dates = parsed_dates.isna()

print("Invalid or missing dates:", int(invalid_dates.sum()))

if invalid_dates.any():
    df.loc[invalid_dates].to_csv(
        OUTPUT_DIR / "invalid_dates.csv",
        index=False
    )

    raise ValueError(
        "Invalid dates found. Check cleaning_output/invalid_dates.csv."
    )

df["Date"] = parsed_dates



START_DATE = "2010-01-01"
END_DATE = "2025-12-31"

within_period = df["Date"].between(
    START_DATE,
    END_DATE,
    inclusive="both"
)

excluded_date_rows = int((~within_period).sum())

df = df.loc[within_period].copy()

if df.empty:
    raise ValueError("No observations exist in the selected period.")

selected_period_rows = len(df)

# Arrange observations from oldest to newest.
df = df.sort_values("Date").reset_index(drop=True)

print("Rows outside the requested period:", excluded_date_rows)
print("Rows within the requested period:", selected_period_rows)
print("First available date:", df["Date"].min().date())
print("Last available date:", df["Date"].max().date())


# Record the row count before deduplication for the cleaning summary.
rows_before_duplicates = len(df)

for currency in CURRENCIES:
    original_values = df[currency]

    numeric_values = pd.to_numeric(
        original_values,
        errors="coerce"
    )

    # Identify nonmissing text that cannot be interpreted as a number.
    invalid_text = (
        original_values.notna()
        & numeric_values.isna()
    )

    if invalid_text.any():
        issue_file = OUTPUT_DIR / f"invalid_text_{currency}.csv"

        df.loc[invalid_text, ["Date", currency]].to_csv(
            issue_file,
            index=False
        )

        raise ValueError(
            f"Invalid text found in {currency}. Check {issue_file.name}."
        )

    df[currency] = numeric_values

# Remove rows whose date and all eight rates are identical.
df = df.drop_duplicates().copy()

exact_duplicates_removed = rows_before_duplicates - len(df)

print("Exact duplicate rows removed:", exact_duplicates_removed)

# A repeated date remaining here has conflicting records.
conflicting_dates = df["Date"].duplicated(keep=False)

if conflicting_dates.any():
    df.loc[conflicting_dates].to_csv(
        OUTPUT_DIR / "conflicting_dates.csv",
        index=False,
        date_format="%Y-%m-%d"
    )

    raise ValueError(
        "Conflicting records exist for the same date. "
        "Check cleaning_output/conflicting_dates.csv."
    )

df = df.reset_index(drop=True)


invalid_rates = (
    df[CURRENCIES].le(0)
    | df[CURRENCIES].isin([
        float("inf"),
        float("-inf")
    ])
).fillna(False)

invalid_rate_rows = invalid_rates.any(axis=1)

print("Rows with invalid rates:", int(invalid_rate_rows.sum()))

if invalid_rate_rows.any():
    df.loc[invalid_rate_rows].to_csv(
        OUTPUT_DIR / "invalid_rates.csv",
        index=False,
        date_format="%Y-%m-%d"
    )

    raise ValueError(
        "Nonpositive or infinite rates found. "
        "Check cleaning_output/invalid_rates.csv."
    )


missing_report = pd.DataFrame({
    "missing_count": df[CURRENCIES].isna().sum(),
    "missing_percentage": (
        df[CURRENCIES].isna().mean() * 100
    )
})

rows_with_missing = df.loc[
    df[CURRENCIES].isna().any(axis=1)
].copy()

print("\nMissing-value report:")
print(missing_report)

print(
    "\nDates with at least one missing rate:",
    len(rows_with_missing)
)

missing_report.to_csv(
    OUTPUT_DIR / "missing_value_report.csv",
    index_label="currency"
)

rows_with_missing.to_csv(
    OUTPUT_DIR / "rows_with_missing_values.csv",
    index=False,
    date_format="%Y-%m-%d",
    na_rep="N/A"
)


# Final structural checks.
assert df.columns.tolist() == REQUIRED_COLUMNS
assert df["Date"].is_monotonic_increasing
assert df["Date"].is_unique

assert df["Date"].between(
    START_DATE,
    END_DATE,
    inclusive="both"
).all()

CLEAN_FILE = OUTPUT_DIR / "fx_eur_8currencies_2010_2025.csv"

df.to_csv(
    CLEAN_FILE,
    index=False,
    date_format="%Y-%m-%d",
    na_rep="N/A",
    encoding="utf-8"
)

# Record what the cleaning process actually did.
summary = pd.DataFrame([
    ("original_rows", original_rows),
    ("rows_outside_period", excluded_date_rows),
    ("rows_in_period_before_deduplication", selected_period_rows),
    ("exact_duplicates_removed", exact_duplicates_removed),
    ("final_rows", len(df)),
    ("rows_with_missing_rates", len(rows_with_missing)),
    ("first_observation", df["Date"].min().strftime("%Y-%m-%d")),
    ("last_observation", df["Date"].max().strftime("%Y-%m-%d")),
    ("base_currency", "EUR"),
    ("quote_definition", "Foreign currency units per 1 EUR"),
    ("currencies", ", ".join(CURRENCIES))
], columns=["item", "value"])

summary.to_csv(
    OUTPUT_DIR / "cleaning_summary.csv",
    index=False
)

print("\nCleaning completed.")
print("Cleaned dataset:", CLEAN_FILE)
print("Final shape:", df.shape)
print(df.head())