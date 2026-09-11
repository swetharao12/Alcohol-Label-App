# Alcohol Label Verification App

A standalone prototype for helping alcohol compliance agents verify uploaded label images against application data quickly and simply.

This project is designed around the requirements in the take-home brief:
- fast results, ideally within 5 seconds per label
- support for single and batch uploads
- simple, low-friction UI for non-technical users
- human-in-the-loop review for nuanced or ambiguous cases
- no direct COLA integration for the prototype
- runs entirely locally, with no external API key required
- uploaded images are read with local OCR, and pass/fail decisions come from a trained ML classifier

## Problem Statement

Compliance agents spend a large portion of their time comparing label artwork against application fields such as brand name, class/type, alcohol content, net contents, and the government warning statement. Much of this work is repetitive and can be assisted by automation, as long as the system stays fast, understandable, and easy to use.

## What the App Does

- Accept one label image, or many images at once as a batch
- Extract label text from uploaded images with local OCR (EasyOCR)
- For batch uploads, match each image to the closest application record by brand name before scoring it
- Compute similarity features between the extracted text and the matched application data
- Use a scikit-learn classifier, trained on a labeled CSV dataset, to predict Pass or Fail
- Process each image independently, so one unreadable image does not stop the rest of the batch
- Export batch results to CSV for recordkeeping
- Flag pass, fail, or uncertain checks for key fields
- Treat the government warning statement as a high-priority exact-match check when possible
- Surface a clear overall decision, plus the reasoning behind it
- Handle imperfect photos when possible, including angle, glare, and low-light conditions

## Core Requirements

- Batch upload support for peak intake periods
- Folder-based batch processing that can run immediately or be scheduled for a later time
- Fast initial response, targeting about 5 seconds or less per label
- Clean, obvious interface with minimal navigation
- Per-label processing so one bad image does not break a whole batch
- Human review remains the final authority

## Out of Scope for the Prototype

- Direct integration with COLA
- Long-term storage of sensitive or regulated data
- Full regulatory coverage for every beverage type and edge case
- Cloud dependencies that require unrestricted outbound network access

## Suggested Workflow

### Single label
1. Choose a mock case from the application database (no image required), or upload one image.
2. Click "Run verification".
3. Review the per-field similarity scores and the ML prediction.

### Batch (peak intake periods)
1. Upload many label images at once.
2. Click "Run batch verification".
3. Each image is matched to the closest application record, scored independently, and added to a results table — a failure on one image does not stop the rest.
4. Review the summary counts, download the results as CSV, or expand any row for per-field detail.
5. Confirm, reject, or send flagged items for manual review.

### Folder-based batch: run now or schedule for later
1. Enter the path to a local folder containing label images.
2. Choose "Run now" to process the folder immediately, or "Schedule for later" and set how many minutes from now it should start.
3. A scheduled run happens in a background thread while the app keeps running — results are written to a timestamped CSV under `results/`, and the latest status (scheduled, running, completed, or error) is shown in the UI.
4. Use "Refresh status" to check on a run without restarting the app.

## Design Principles

- Fast first: useful output should arrive quickly enough to beat manual review for routine cases.
- Simple enough for a non-technical user to understand immediately.
- Assistive, not autonomous: the app should support judgment, not replace it.
- Clear status and results language, with no hidden controls.

## Assumptions

- The first version will be a standalone prototype.
- Data may be supplied manually or through simple mock inputs.
- The initial scope can focus on common distilled spirits label patterns.

## Risks and Trade-Offs

- Strict matching may incorrectly reject valid labels with harmless formatting differences.
- OCR accuracy may vary on low-quality images.
- A complicated UI would reduce adoption among agents with limited technical comfort.
- External AI services may not be practical in restricted-network environments.

## Repository Status

This repository now contains a runnable Streamlit prototype, along with the project brief and implementation spec.

## Installation

1. Create and activate a Python virtual environment if you want to isolate dependencies.
2. Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

Start the Streamlit app with:

```bash
streamlit run app.py
```

Then open the local URL printed in the terminal.

The app runs entirely locally and does not call any external AI API.

Uploaded images are read with EasyOCR. The app then computes a similarity score between each extracted field and the corresponding application data field, and feeds those scores into a `RandomForestClassifier` trained on [data/label_verification_training_data.csv](data/label_verification_training_data.csv) to predict Pass or Fail. If OCR cannot read any text from the image, the app falls back to the selected mock case so the demo still runs.

The training data is synthetic and generated by [scripts/generate_training_data.py](scripts/generate_training_data.py). Regenerate it with:

```bash
python scripts/generate_training_data.py
```

## Next Step

Replace the synthetic training data with real, labeled examples if you want the classifier to generalize to production label images.