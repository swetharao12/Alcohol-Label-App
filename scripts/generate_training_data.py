"""Generates a synthetic labeled dataset for training the label verification classifier.

Each row represents one label check: similarity scores between the application data
and the extracted label data for five fields, plus the Pass/Fail outcome. Pass rows have
uniformly high similarity across all fields (minor OCR noise only). Fail rows have one or
two fields degraded to simulate a real mismatch (wrong ABV, altered warning text, etc.).
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

FIELDS = ["brand_name", "class_type", "abv", "net_contents", "government_warning"]
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "label_verification_training_data.csv"


def sample_high_similarity(rng: random.Random) -> float:
    return round(min(1.0, rng.betavariate(12, 1.2)), 4)


def sample_low_similarity(rng: random.Random) -> float:
    return round(rng.betavariate(2, 5), 4)


def generate_row(rng: random.Random) -> dict:
    is_pass = rng.random() < 0.5
    row = {field: sample_high_similarity(rng) for field in FIELDS}

    if not is_pass:
        num_bad_fields = rng.choice([1, 1, 1, 2])
        bad_fields = rng.sample(FIELDS, num_bad_fields)
        for field in bad_fields:
            row[field] = sample_low_similarity(rng)

    row["label"] = "Pass" if is_pass else "Fail"
    return row


def main(num_rows: int = 400, seed: int = 42) -> None:
    rng = random.Random(seed)
    rows = [generate_row(rng) for _ in range(num_rows)]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=[f"{field}_similarity" for field in FIELDS] + ["label"])
        writer.writeheader()
        for row in rows:
            writer.writerow({f"{field}_similarity": row[field] for field in FIELDS} | {"label": row["label"]})

    print(f"Wrote {num_rows} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
