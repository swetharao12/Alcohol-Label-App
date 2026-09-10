from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class VerificationResult:
    overall: str
    checks: list[CheckResult]


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _contains_match(observed: str, expected: str) -> bool:
    observed_normalized = _normalize(observed)
    expected_normalized = _normalize(expected)
    return bool(expected_normalized) and expected_normalized in observed_normalized


def _exact_warning_match(observed: str, expected: str, strict_warning: bool) -> tuple[str, str]:
    observed_normalized = _normalize(observed)
    expected_normalized = _normalize(expected)

    if not expected_normalized:
        return "UNCERTAIN", "No expected warning statement was provided."

    if strict_warning:
        if observed_normalized == expected_normalized:
            return "PASS", "Government warning matches exactly after whitespace normalization."
        return "FAIL", "Government warning does not match the expected statement exactly."

    if expected_normalized in observed_normalized:
        return "PASS", "Government warning appears to contain the expected statement."
    return "UNCERTAIN", "Government warning text could not be confirmed confidently."


def verify_label(observed_text: str, expected: dict[str, str], strict_warning: bool = True) -> VerificationResult:
    observed_text = observed_text or ""

    checks: list[CheckResult] = []

    brand = expected.get("brand_name", "")
    if not brand:
        checks.append(CheckResult("Brand name", "UNCERTAIN", "No expected brand name was provided."))
    elif _contains_match(observed_text, brand):
        checks.append(CheckResult("Brand name", "PASS", "Brand name appears on the label."))
    else:
        checks.append(CheckResult("Brand name", "FAIL", "Brand name was not found in the observed text."))

    class_type = expected.get("class_type", "")
    if not class_type:
        checks.append(CheckResult("Class / type", "UNCERTAIN", "No expected class or type was provided."))
    elif _contains_match(observed_text, class_type):
        checks.append(CheckResult("Class / type", "PASS", "Class or type designation appears on the label."))
    else:
        checks.append(CheckResult("Class / type", "FAIL", "Class or type designation was not found in the observed text."))

    alcohol = expected.get("alcohol_content", "")
    if not alcohol:
        checks.append(CheckResult("Alcohol content", "UNCERTAIN", "No expected alcohol content was provided."))
    elif _contains_match(observed_text, alcohol):
        checks.append(CheckResult("Alcohol content", "PASS", "Alcohol content appears on the label."))
    else:
        checks.append(CheckResult("Alcohol content", "FAIL", "Alcohol content was not found in the observed text."))

    contents = expected.get("net_contents", "")
    if not contents:
        checks.append(CheckResult("Net contents", "UNCERTAIN", "No expected net contents were provided."))
    elif _contains_match(observed_text, contents):
        checks.append(CheckResult("Net contents", "PASS", "Net contents appears on the label."))
    else:
        checks.append(CheckResult("Net contents", "FAIL", "Net contents was not found in the observed text."))

    warning = expected.get("government_warning", "")
    warning_status, warning_reason = _exact_warning_match(observed_text, warning, strict_warning)
    checks.append(CheckResult("Government warning", warning_status, warning_reason))

    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        overall = "REJECT"
    elif statuses == {"PASS"}:
        overall = "APPROVE"
    else:
        overall = "NEEDS REVIEW"

    return VerificationResult(overall=overall, checks=checks)