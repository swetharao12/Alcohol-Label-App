from __future__ import annotations

import difflib
import io
import json
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    np = None

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency fallback
    Image = None

try:
    import easyocr
except Exception:  # pragma: no cover - optional dependency fallback
    easyocr = None


FIELDS = ["brand_name", "class_type", "abv", "net_contents", "government_warning"]
REQUIRED_DB_COLUMNS = ["label_id"] + FIELDS
TRAINING_DATA_PATH = Path(__file__).resolve().parent / "data" / "label_verification_training_data.csv"
MATCH_CONFIDENCE_THRESHOLD = 0.4
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SCHEDULER_STATUS_PATH = RESULTS_DIR / "scheduler_status.json"

st.set_page_config(page_title="TTB Label Verification App", layout="wide")
st.title("AI-Powered Alcohol Label Verification App")

with st.sidebar:
    st.header("DB Data")
    st.info("Runs fully locally: OCR extraction plus a trained ML classifier. No external API key is required.")
    uploaded_db_csv = st.file_uploader(
        "Upload application database CSV (optional)",
        type=["csv"],
        help="Replaces the built-in demo records. Required columns: " + ", ".join(REQUIRED_DB_COLUMNS),
    )


application_data_df = pd.DataFrame(
    {
        "label_id": ["APP001", "APP002", "APP003", "APP004", "APP005"],
        "brand_name": [
            "OLD TOM DISTILLERY",
            "GOLDEN HARVEST RYE",
            "OCEAN BREEZE GIN",
            "MOUNTAIN WHISPER SCOTCH",
            "DESERT BLOOM TEQUILA",
        ],
        "class_type": [
            "Kentucky Straight Bourbon Whiskey",
            "Straight Rye Whiskey",
            "Dry Gin",
            "Single Malt Scotch Whisky",
            "Tequila Blanco",
        ],
        "abv": [
            "45% Alc./Vol. (90 Proof)",
            "50% Alc./Vol. (100 Proof)",
            "40% Alc./Vol. (80 Proof)",
            "43% Alc./Vol. (86 Proof)",
            "38% Alc./Vol. (76 Proof)",
        ],
        "net_contents": ["750 mL", "750 mL", "1.75 L", "700 mL", "1 L"],
        "government_warning": [
            "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        ],
    }
)

if uploaded_db_csv is not None:
    try:
        custom_db_df = pd.read_csv(uploaded_db_csv, dtype=str).fillna("")
        missing_db_columns = [column for column in REQUIRED_DB_COLUMNS if column not in custom_db_df.columns]
        if missing_db_columns:
            st.sidebar.error(
                f"CSV is missing required columns: {', '.join(missing_db_columns)}. Using the built-in demo records instead."
            )
        else:
            application_data_df = custom_db_df[REQUIRED_DB_COLUMNS]
            st.sidebar.success(f"Loaded {len(application_data_df)} application record(s) from the uploaded CSV.")
    except Exception as exc:
        st.sidebar.error(f"Could not read the uploaded CSV: {exc}. Using the built-in demo records instead.")

simulated_label_ocr_outputs = [
    {
        "label_id": "APP001",
        "application_data": {
            "label_id": "APP001",
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "abv": "45% Alc./Vol. (90 Proof)",
            "net_contents": "750 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "extracted_text": {
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "abv": "45% Alc./Vol. (90 Proof)",
            "net_contents": "750 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "ground_truth_status": "Pass",
    },
    {
        "label_id": "APP002",
        "application_data": {
            "label_id": "APP002",
            "brand_name": "GOLDEN HARVEST RYE",
            "class_type": "Straight Rye Whiskey",
            "abv": "50% Alc./Vol. (100 Proof)",
            "net_contents": "750 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "extracted_text": {
            "brand_name": "GOLDEN HARVEST RYE",
            "class_type": "Straight Rye Whiskey",
            "abv": "49% Alc./Vol. (98 Proof)",
            "net_contents": "750 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "ground_truth_status": "Fail",
    },
    {
        "label_id": "APP003",
        "application_data": {
            "label_id": "APP003",
            "brand_name": "OCEAN BREEZE GIN",
            "class_type": "Dry Gin",
            "abv": "40% Alc./Vol. (80 Proof)",
            "net_contents": "1.75 L",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "extracted_text": {
            "brand_name": "OCEAN BREEZE GIN",
            "class_type": "Dry Gin",
            "abv": "40% Alc./Vol. (80 Proof)",
            "net_contents": "1.75 L",
            "government_warning": "Government Warning: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "ground_truth_status": "Fail",
    },
    {
        "label_id": "APP004",
        "application_data": {
            "label_id": "APP004",
            "brand_name": "MOUNTAIN WHISPER SCOTCH",
            "class_type": "Single Malt Scotch Whisky",
            "abv": "43% Alc./Vol. (86 Proof)",
            "net_contents": "700 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "extracted_text": {
            "brand_name": "MOUNTAIN WHISPER SCOTCH",
            "class_type": "Single Malt Scotch Whisky",
            "abv": "43% Alc./Vol. (86 Proof)",
            "net_contents": "700 mL",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "ground_truth_status": "Pass",
    },
    {
        "label_id": "APP005",
        "application_data": {
            "label_id": "APP005",
            "brand_name": "DESERT BLOOM TEQUILA",
            "class_type": "Tequila Blanco",
            "abv": "38% Alc./Vol. (76 Proof)",
            "net_contents": "1 L",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "extracted_text": {
            "brand_name": "DESERT BLOOM TEQUILA",
            "class_type": "Tequila Blanco",
            "abv": "38% Alc./Vol. (76 Proof)",
            "net_contents": "1 L",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
        },
        "ground_truth_status": "Fail",
    },
]

mock_case_options = [
    {
        "key": f"case-{index + 1}",
        "label": f"Case {index + 1} | {label['label_id']} | {label['ground_truth_status']} | {label['extracted_text']['brand_name']}",
        "data": label,
    }
    for index, label in enumerate(simulated_label_ocr_outputs)
]

with st.sidebar:
    st.caption("Application data base")
    st.dataframe(application_data_df, use_container_width=True)


@st.cache_resource(show_spinner="Loading local OCR model...")
def get_ocr_reader():
    if easyocr is None:
        return None
    try:
        return easyocr.Reader(["en"], gpu=False)
    except Exception:
        return None


BRAND_NAME_LINE_RE = re.compile(r"[A-Z][A-Z\s&'\-]+")
CLASS_TYPE_KEYWORDS = ["whiskey", "whisky", "gin", "vodka", "tequila", "rum", "brandy", "scotch"]
ABV_KEYWORDS = ("alc./vol", "alcohol by volume", "proof")
ABV_CONTINUATION_RE = re.compile(r"alc\.?/vol|alcohol by volume|proof|%", re.IGNORECASE)


def _contains_class_keyword(text):
    # OCR sometimes inserts stray spaces inside a word (e.g. "GI N" for "GIN"); ignore whitespace when matching.
    collapsed = text.casefold().replace(" ", "")
    return any(keyword in collapsed for keyword in CLASS_TYPE_KEYWORDS)


def _clean_ocr_line(line):
    # OCR sometimes tacks on stray punctuation (e.g. "OCEAN BREEZE]"); trim it so the brand regex still matches.
    return re.sub(r"^[^A-Za-z]+|[^A-Za-z&'\-]+$", "", line)


def derive_fields_from_transcript(lines):
    derived_fields = {
        "brand_name": "",
        "class_type": "",
        "abv": "",
        "net_contents": "",
        "government_warning": "",
    }

    index = 0
    class_type_lead_in = []
    while index < len(lines):
        line = lines[index]
        normalized_line = line.casefold()
        cleaned_line = _clean_ocr_line(line)

        if not derived_fields["brand_name"] and BRAND_NAME_LINE_RE.fullmatch(cleaned_line) and not _contains_class_keyword(cleaned_line):
            # Brand names are often stacked/wrapped across several all-caps lines (e.g. a banner design), and the
            # spirit keyword itself is sometimes part of the brand's logotype (e.g. "OCEAN BREEZE" / "GIN"), so
            # allow one keyword-bearing line into the brand before stopping at the formal class/type designation.
            brand_lines = [cleaned_line.strip()]
            merged_keyword = False
            index += 1
            while index < len(lines) and not merged_keyword:
                next_line = _clean_ocr_line(lines[index])
                if not BRAND_NAME_LINE_RE.fullmatch(next_line):
                    break
                brand_lines.append(next_line.strip())
                merged_keyword = _contains_class_keyword(next_line)
                index += 1
            derived_fields["brand_name"] = " ".join(brand_lines)
            continue

        if not derived_fields["class_type"] and _contains_class_keyword(normalized_line):
            # Prepend any preceding qualifier line (e.g. "Kentucky Straight") before "BOURBON WHISKEY".
            derived_fields["class_type"] = " ".join(class_type_lead_in + [line.strip()])
            class_type_lead_in = []
            index += 1
            continue

        if not derived_fields["abv"] and any(keyword in normalized_line for keyword in ABV_KEYWORDS):
            # The percentage and the "(___ Proof)" qualifier are sometimes split across two lines.
            abv_lines = [line.strip()]
            index += 1
            while (
                index < len(lines)
                and ABV_CONTINUATION_RE.search(lines[index])
                and not re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|l)\b", lines[index].casefold())
            ):
                abv_lines.append(lines[index].strip())
                index += 1
            derived_fields["abv"] = " ".join(abv_lines)
            class_type_lead_in = []
            continue

        if not derived_fields["net_contents"] and re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|l)\b", normalized_line):
            derived_fields["net_contents"] = line.strip()
            class_type_lead_in = []
            index += 1
            continue

        if not derived_fields["government_warning"] and "government" in normalized_line:
            # "GOVERNMENT" and "WARNING:" are sometimes detected as separate lines (or merged with no space);
            # matching on "government" alone and taking the rest of the transcript covers both cases.
            derived_fields["government_warning"] = " ".join(warning_line.strip() for warning_line in lines[index:])
            index = len(lines)
            continue

        if derived_fields["brand_name"] and not derived_fields["class_type"] and line.strip():
            # Unclaimed line between the brand name and the class/type keyword line - likely a lead-in qualifier.
            class_type_lead_in.append(line.strip())

        index += 1

    return derived_fields


def extract_label_data_from_image(uploaded_file):
    reader = get_ocr_reader()
    if uploaded_file is None or Image is None or reader is None or np is None:
        return {}, ""

    try:
        image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
        result_lines = reader.readtext(np.array(image), detail=0)
        lines = [line.strip() for line in result_lines if line and line.strip()]
        raw_text = "\n".join(lines)

        if not lines:
            return {}, raw_text

        fields = derive_fields_from_transcript(lines)
        fields["transcribed_lines"] = lines
        return fields, raw_text
    except Exception:
        return {}, ""


def match_application_record(extracted_fields):
    """Fuzzy-match extracted brand name against the application database. Returns (record_dict, score)."""
    extracted_brand = str((extracted_fields or {}).get("brand_name", "")).strip().casefold()
    if not extracted_brand:
        return None, 0.0

    best_record = None
    best_score = 0.0
    for _, row in application_data_df.iterrows():
        score = difflib.SequenceMatcher(None, extracted_brand, row["brand_name"].casefold()).ratio()
        if score > best_score:
            best_score = score
            best_record = row.to_dict()

    return best_record, best_score


@st.cache_resource(show_spinner="Training verification model...")
def train_verification_model():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    training_df = pd.read_csv(TRAINING_DATA_PATH)
    feature_columns = [f"{field}_similarity" for field in FIELDS]
    features = training_df[feature_columns]
    labels = training_df["label"]

    features_train, features_test, labels_train, labels_test = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )

    model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    model.fit(features_train, labels_train)
    test_accuracy = model.score(features_test, labels_test)
    return model, test_accuracy, len(training_df)


def compute_similarity_features(application_data, extracted_data):
    features = {}
    for field in FIELDS:
        app_value = str(application_data.get(field, "") or "").strip().casefold()
        ext_value = str(extracted_data.get(field, "") or "").strip().casefold()
        features[f"{field}_similarity"] = difflib.SequenceMatcher(None, app_value, ext_value).ratio()
    return features


def predict_verdict(model, features):
    feature_columns = [f"{field}_similarity" for field in FIELDS]
    feature_row = pd.DataFrame([features], columns=feature_columns)
    prediction = model.predict(feature_row)[0]
    probabilities = dict(zip(model.classes_, model.predict_proba(feature_row)[0]))
    return prediction, probabilities


verification_model, model_test_accuracy, training_row_count = train_verification_model()

with st.sidebar:
    st.caption("ML verification model")
    st.write(f"Trained on {training_row_count} labeled examples")
    st.write(f"Held-out test accuracy: {model_test_accuracy:.2%}")


def process_one_image(uploaded_file, fallback_case):
    """Extract, match, and score a single uploaded image. Never raises - returns a result row plus detail dict."""
    extracted_fields, raw_text = extract_label_data_from_image(uploaded_file)
    used_ocr = bool(extracted_fields)

    if used_ocr:
        matched_application, match_score = match_application_record(extracted_fields)
        if matched_application is None or match_score < MATCH_CONFIDENCE_THRESHOLD:
            matched_application = fallback_case["application_data"]
            ground_truth_status = fallback_case["ground_truth_status"]
            note = "No confident match in the application database; used a demo fallback record."
        else:
            ground_truth_status = ""
            note = f"Matched application record by brand name similarity ({match_score:.2f})."
    else:
        extracted_fields = fallback_case["extracted_text"]
        matched_application = fallback_case["application_data"]
        ground_truth_status = fallback_case["ground_truth_status"]
        note = "OCR could not read this image; used a demo fallback record."

    similarity_features = compute_similarity_features(matched_application, extracted_fields)
    predicted_label, probabilities = predict_verdict(verification_model, similarity_features)

    result_row = {
        "file_name": uploaded_file.name,
        "matched_label_id": matched_application.get("label_id", ""),
        "matched_brand_name": matched_application.get("brand_name", ""),
        "predicted_status": predicted_label,
        "pass_probability": round(probabilities.get("Pass", 0.0), 3),
        "fail_probability": round(probabilities.get("Fail", 0.0), 3),
        "ground_truth_status": ground_truth_status,
        "note": note,
    }
    detail = {
        "extracted": extracted_fields,
        "application": matched_application,
        "features": similarity_features,
        "raw_text": raw_text,
    }
    return result_row, detail


class LocalImageFile:
    """Wraps a filesystem path so it can be passed anywhere an uploaded_file is expected."""

    def __init__(self, path: Path):
        self._path = path
        self.name = path.name

    def getvalue(self):
        return self._path.read_bytes()


def run_folder_batch(folder_path: Path):
    """Processes every image in a folder through the same pipeline as an interactive batch upload."""
    image_paths = sorted(p for p in folder_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)

    batch_results = []
    for index, image_path in enumerate(image_paths):
        fallback_case = simulated_label_ocr_outputs[index % len(simulated_label_ocr_outputs)]
        try:
            result_row, _ = process_one_image(LocalImageFile(image_path), fallback_case)
        except Exception as exc:
            result_row = {
                "file_name": image_path.name,
                "matched_label_id": "",
                "matched_brand_name": "",
                "predicted_status": "Error",
                "pass_probability": 0.0,
                "fail_probability": 0.0,
                "ground_truth_status": "",
                "note": f"Processing failed, skipped: {exc}",
            }
        batch_results.append(result_row)

    return pd.DataFrame(batch_results), len(image_paths)


def write_scheduler_status(**fields):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    current_status = {}
    if SCHEDULER_STATUS_PATH.exists():
        try:
            current_status = json.loads(SCHEDULER_STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            current_status = {}
    current_status.update(fields)
    SCHEDULER_STATUS_PATH.write_text(json.dumps(current_status, indent=2), encoding="utf-8")


def run_scheduled_batch(folder_path_str: str, run_at_iso: str):
    target_time = datetime.fromisoformat(run_at_iso)
    while datetime.now() < target_time:
        time.sleep(min(5, max(0, (target_time - datetime.now()).total_seconds())))

    write_scheduler_status(status="running", started_at=datetime.now().isoformat())
    try:
        results_df, image_count = run_folder_batch(Path(folder_path_str))
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        csv_name = f"batch_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
        csv_path = RESULTS_DIR / csv_name
        results_df.to_csv(csv_path, index=False)
        status_counts = results_df["predicted_status"].value_counts().to_dict() if not results_df.empty else {}
        write_scheduler_status(
            status="completed",
            completed_at=datetime.now().isoformat(),
            image_count=image_count,
            csv_path=str(csv_path),
            status_counts=status_counts,
        )
    except Exception as exc:
        write_scheduler_status(status="error", completed_at=datetime.now().isoformat(), error=str(exc))


st.subheader("Upload Label Images (Batch Supported)")
uploaded_files = st.file_uploader(
    "Upload one or more label images to process as a batch",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)

if uploaded_files:
    # --- Batch mode ---
    st.write(f"{len(uploaded_files)} image(s) queued for batch verification.")
    run_batch = st.button("Run batch verification", type="primary")

    if run_batch:
        batch_results = []
        batch_details = {}
        progress_bar = st.progress(0.0, text="Processing batch...")

        for index, uploaded_file in enumerate(uploaded_files):
            fallback_case = simulated_label_ocr_outputs[index % len(simulated_label_ocr_outputs)]
            try:
                result_row, detail = process_one_image(uploaded_file, fallback_case)
            except Exception as exc:
                result_row = {
                    "file_name": uploaded_file.name,
                    "matched_label_id": "",
                    "matched_brand_name": "",
                    "predicted_status": "Error",
                    "pass_probability": 0.0,
                    "fail_probability": 0.0,
                    "ground_truth_status": "",
                    "note": f"Processing failed, skipped: {exc}",
                }
                detail = None

            batch_results.append(result_row)
            if detail is not None:
                batch_details[uploaded_file.name] = detail
            progress_bar.progress((index + 1) / len(uploaded_files), text=f"Processed {index + 1} of {len(uploaded_files)}")

        progress_bar.empty()
        results_df = pd.DataFrame(batch_results)

        st.subheader("Batch Verification Results")
        status_counts = results_df["predicted_status"].value_counts()
        summary_columns = st.columns(4)
        summary_columns[0].metric("Total processed", len(results_df))
        summary_columns[1].metric("Predicted Pass", int(status_counts.get("Pass", 0)))
        summary_columns[2].metric("Predicted Fail", int(status_counts.get("Fail", 0)))
        summary_columns[3].metric("Errors", int(status_counts.get("Error", 0)))

        st.dataframe(results_df, use_container_width=True)

        st.download_button(
            "Download batch results as CSV",
            data=results_df.to_csv(index=False),
            file_name="batch_verification_results.csv",
            mime="text/csv",
        )

        known_ground_truth_df = results_df[results_df["ground_truth_status"] != ""]
        if not known_ground_truth_df.empty:
            st.subheader("Evaluation on Items With Known Ground Truth")
            st.caption("These items used a demo fallback record, so the ground truth is known and can be scored.")
            from sklearn.metrics import classification_report

            y_true = known_ground_truth_df["ground_truth_status"].apply(lambda x: 1 if x == "Fail" else 0)
            y_pred = known_ground_truth_df["predicted_status"].apply(lambda x: 1 if x == "Fail" else 0)
            st.text(
                classification_report(
                    y_true,
                    y_pred,
                    labels=[0, 1],
                    target_names=["Pass", "Fail"],
                    zero_division=0,
                )
            )

        st.subheader("Per-Item Details")
        for file_name, detail in batch_details.items():
            with st.expander(f"{file_name}"):
                st.write("Matched application data")
                st.json(detail["application"])
                st.write("Extracted / compared data")
                st.json({key: value for key, value in detail["extracted"].items() if key != "transcribed_lines"})
                st.write("Similarity features")
                st.json({key: round(value, 3) for key, value in detail["features"].items()})
    else:
        st.info("Click 'Run batch verification' to process all uploaded images.")

st.divider()

# --- Single mock-case mode (always available, alongside batch upload) ---
st.markdown("#### Test a single case from the mock application database:")
selected_case = st.selectbox(
    "Choose which mock case to run",
    options=mock_case_options,
    format_func=lambda option: option["label"],
    index=0,
)

st.subheader("Label Data (Mock OCR Output)")
st.json(selected_case["data"]["extracted_text"])

st.subheader("Application Data for Selected Mock Case")
st.json(selected_case["data"]["application_data"])

st.caption(f"Selected mock case: {selected_case['label']}")

with st.expander("What this selected case represents", expanded=False):
    extracted = selected_case["data"]["extracted_text"]
    application = selected_case["data"]["application_data"]
    st.write(f"Ground truth: {selected_case['data']['ground_truth_status']}")
    st.write(f"Brand name: {application['brand_name']}")
    st.write(f"ABV: {application['abv']}")
    st.write(f"Net contents: {application['net_contents']}")
    warning_matches = extracted["government_warning"] == application["government_warning"]
    st.write(f"Government warning: {'matches' if warning_matches else 'differs'}")

    if not warning_matches:
        st.write("Government warning diff:")
        warning_diff = difflib.unified_diff(
            application["government_warning"].split(),
            extracted["government_warning"].split(),
            fromfile="application",
            tofile="mock_ocr",
            lineterm="",
        )
        st.code("\n".join(warning_diff), language="diff")

    mismatched_fields = [field_name for field_name in FIELDS if extracted[field_name] != application[field_name]]
    if mismatched_fields:
        st.write("Mismatched fields:")
        st.write(", ".join(mismatched_fields))
    else:
        st.write("All selected fields match.")

st.subheader("Single-Case Verification Workflow")
run_verification = st.button("Run verification", type="primary")

if run_verification:
    selected_label = selected_case["data"]
    application_data = selected_label["application_data"]
    extracted_data = selected_label["extracted_text"]

    similarity_features = compute_similarity_features(application_data, extracted_data)
    predicted_label, probabilities = predict_verdict(verification_model, similarity_features)

    result_entry = {
        "label_id": selected_label["label_id"],
        "ground_truth_status": selected_label["ground_truth_status"],
        "predicted_status": predicted_label,
        "pass_probability": round(probabilities.get("Pass", 0.0), 3),
        "fail_probability": round(probabilities.get("Fail", 0.0), 3),
        **{key: round(value, 3) for key, value in similarity_features.items()},
    }

    with st.expander(
        f"Process selected label ({selected_label['label_id']}) - Ground truth: {selected_label['ground_truth_status']}",
        expanded=True,
    ):
        st.subheader("Extracted values used for comparison")
        st.json(extracted_data)
        st.subheader("Similarity features and ML prediction")
        st.json(result_entry)

    results_df = pd.DataFrame([result_entry])
    st.subheader("Verification Results")
    st.dataframe(results_df, use_container_width=True)

    st.subheader("Evaluation Metrics")
    from sklearn.metrics import classification_report

    y_true = results_df["ground_truth_status"].apply(lambda x: 1 if x == "Fail" else 0)
    y_pred = results_df["predicted_status"].apply(lambda x: 1 if x == "Fail" else 0)

    st.text("Classification report for this single case:")
    st.text(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["Pass", "Fail"],
            zero_division=0,
        )
    )
    st.caption(f"Model held-out test accuracy across {training_row_count} training rows: {model_test_accuracy:.2%}")

    st.subheader("Anomaly Detection and Detailed Feedback")
    low_similarity_fields = [field for field in FIELDS if similarity_features[f"{field}_similarity"] < 0.85]
    if low_similarity_fields:
        st.warning("Fields with low similarity: " + ", ".join(low_similarity_fields))
    else:
        st.success("All fields show high similarity between the application data and the extracted label data.")
else:
    st.info("Choose a mock case and click 'Run verification'.")

st.divider()
st.subheader("Folder-Based Batch: Run Now or Schedule for Later")
st.caption("Point the app at a local folder of label images. Run the batch immediately, or schedule it to start later.")

folder_path_input = st.text_input("Folder path containing label images", value="")
run_mode = st.radio("When should this batch run?", ["Run now", "Schedule for later"], horizontal=True)

if run_mode == "Schedule for later":
    minutes_from_now = st.number_input("Run in how many minutes from now", min_value=1, value=5, step=1)

schedule_action = st.button("Run now" if run_mode == "Run now" else "Schedule batch run", type="primary")

if schedule_action:
    folder_path = Path(folder_path_input) if folder_path_input else None
    if not folder_path or not folder_path.is_dir():
        st.error("Enter a valid folder path that exists on this machine.")
    elif run_mode == "Run now":
        with st.spinner("Running batch over the folder..."):
            folder_results_df, folder_image_count = run_folder_batch(folder_path)
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            csv_path = RESULTS_DIR / f"batch_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
            folder_results_df.to_csv(csv_path, index=False)
            write_scheduler_status(
                status="completed",
                folder=str(folder_path),
                completed_at=datetime.now().isoformat(),
                image_count=folder_image_count,
                csv_path=str(csv_path),
                status_counts=folder_results_df["predicted_status"].value_counts().to_dict() if not folder_results_df.empty else {},
            )
        st.success(f"Processed {folder_image_count} image(s). Results saved to {csv_path}")
        st.dataframe(folder_results_df, use_container_width=True)
        st.download_button(
            "Download these results as CSV",
            data=folder_results_df.to_csv(index=False),
            file_name=csv_path.name,
            mime="text/csv",
        )
    else:
        target_time = datetime.now() + timedelta(minutes=minutes_from_now)
        write_scheduler_status(
            status="scheduled",
            folder=str(folder_path),
            scheduled_for=target_time.isoformat(),
        )
        scheduler_thread = threading.Thread(
            target=run_scheduled_batch,
            args=(str(folder_path), target_time.isoformat()),
            daemon=True,
        )
        scheduler_thread.start()
        st.success(f"Batch scheduled to run at {target_time.strftime('%Y-%m-%d %H:%M:%S')}. Keep this app running until then.")

st.caption("Latest scheduler status:")
if SCHEDULER_STATUS_PATH.exists():
    latest_status = json.loads(SCHEDULER_STATUS_PATH.read_text(encoding="utf-8"))
    st.json(latest_status)
    if st.button("Refresh status"):
        st.rerun()
else:
    st.write("No scheduled or folder-based runs yet.")

st.subheader("Conclusion and Next Steps")
st.markdown(
    """
This prototype uses local OCR to read uploaded label images and a scikit-learn classifier,
trained on a labeled CSV dataset of field-similarity scores, to decide Pass/Fail. No external
AI API is called, and images can be processed one at a time or as a batch.

Potential improvements include:
1. A larger, real-world labeled dataset instead of synthetic training data.
2. More robust OCR line parsing for complex label layouts.
3. Additional features beyond string similarity (e.g., edit distance per token, numeric ABV parsing).
4. Database integration for application records.
5. Confidence-based routing to human review for borderline probabilities.
6. Progress streaming for very large batches (hundreds of labels at once).
"""
)
