# Alcohol Label Verification App

A standalone prototype for helping alcohol compliance agents verify uploaded label images against application data quickly and simply.

This project is designed around the requirements in the take-home brief:
- fast results, ideally within 5 seconds per label
- support for single and batch uploads
- simple, low-friction UI for non-technical users
- human-in-the-loop review for nuanced or ambiguous cases
- no direct COLA integration for the prototype

## Problem Statement

Compliance agents spend a large portion of their time comparing label artwork against application fields such as brand name, class/type, alcohol content, net contents, and the government warning statement. Much of this work is repetitive and can be assisted by automation, as long as the system stays fast, understandable, and easy to use.

## What the App Should Do

- Accept one label image or many images at once
- Compare label content against submitted application data
- Flag pass, fail, or uncertain checks for key fields
- Treat the government warning statement as a high-priority exact-match check when possible
- Surface a clear overall decision, plus the reasoning behind it
- Handle imperfect photos when possible, including angle, glare, and low-light conditions

## Core Requirements

- Batch upload support for peak intake periods
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

1. Upload one or more label images.
2. Enter or paste the corresponding application data.
3. Review the app’s per-field verification results.
4. Confirm, reject, or send the item for manual review.

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
- OCR or vision accuracy may vary on low-quality images.
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

## Next Step

Extend the prototype with real OCR or multimodal extraction if you want automated label reading instead of the current text-assisted verification flow.