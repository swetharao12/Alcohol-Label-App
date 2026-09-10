from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from src.verification import VerificationResult, verify_label


st.set_page_config(
    page_title="Alcohol Label Verification App",
    page_icon="🏷️",
    layout="wide",
)


@dataclass
class UploadedLabel:
    filename: str
    image: Any


def _parse_batch_input(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue
        record: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            record[key.strip().lower()] = value.strip()
        if record:
            items.append(record)
    return items


def _default_reference_text() -> str:
    return (
        "OLD TOM DISTILLERY\n"
        "Kentucky Straight Bourbon Whiskey\n"
        "45% Alc./Vol. (90 Proof)\n"
        "750 mL\n"
        "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY..."
    )


st.title("Alcohol Label Verification App")
st.caption(
    "Prototype for fast label review with batch uploads, clear pass/fail/uncertain checks, and human-in-the-loop approval."
)

with st.sidebar:
    st.header("Application Data")
    brand_name = st.text_input("Brand name", value="OLD TOM DISTILLERY")
    class_type = st.text_input("Class / type", value="Kentucky Straight Bourbon Whiskey")
    alcohol_content = st.text_input("Alcohol content", value="45% Alc./Vol. (90 Proof)")
    net_contents = st.text_input("Net contents", value="750 mL")
    government_warning = st.text_area(
        "Government warning statement",
        value=(
            "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK "
            "ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) "
            "CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE "
            "MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
        ),
        height=160,
    )
    strict_warning = st.checkbox("Require exact warning match", value=True)

st.subheader("Upload labels")
uploads = st.file_uploader(
    "Upload one or more label images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)

st.subheader("Optional batch text input")
st.caption("Paste one or more label-text blocks to compare against the same application data when OCR text is not available.")
reference_text = st.text_area("Observed label text", value=_default_reference_text(), height=180)

batch_records = _parse_batch_input(reference_text)

if st.button("Run verification", type="primary"):
    if not uploads and not batch_records:
        st.error("Upload at least one image or provide observed label text.")
    else:
        if uploads:
            st.markdown("### Image review")
            for upload in uploads:
                with st.container(border=True):
                    left, right = st.columns([1, 2])
                    with left:
                        st.image(upload, caption=upload.name, use_container_width=True)
                    with right:
                        result: VerificationResult = verify_label(
                            observed_text=reference_text,
                            expected={
                                "brand_name": brand_name,
                                "class_type": class_type,
                                "alcohol_content": alcohol_content,
                                "net_contents": net_contents,
                                "government_warning": government_warning,
                            },
                            strict_warning=strict_warning,
                        )
                        st.metric("Overall result", result.overall)
                        for check in result.checks:
                            st.write(f"**{check.name}**: {check.status} — {check.reason}")

        if batch_records:
            st.markdown("### Text batch review")
            for index, record in enumerate(batch_records, start=1):
                observed = record.get("observed_text", record.get("text", ""))
                expected_brand = record.get("brand_name", brand_name)
                expected_class = record.get("class_type", class_type)
                expected_alcohol = record.get("alcohol_content", alcohol_content)
                expected_contents = record.get("net_contents", net_contents)
                expected_warning = record.get("government_warning", government_warning)

                result = verify_label(
                    observed_text=observed,
                    expected={
                        "brand_name": expected_brand,
                        "class_type": expected_class,
                        "alcohol_content": expected_alcohol,
                        "net_contents": expected_contents,
                        "government_warning": expected_warning,
                    },
                    strict_warning=strict_warning,
                )

                with st.container(border=True):
                    st.write(f"**Item {index}**")
                    st.metric("Overall result", result.overall)
                    for check in result.checks:
                        st.write(f"**{check.name}**: {check.status} — {check.reason}")

st.markdown("---")
st.markdown(
    "This prototype is intentionally standalone and does not connect to COLA or store sensitive data."
)