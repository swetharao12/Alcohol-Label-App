# Alcohol Label Verification App Spec

## Goal
Build a standalone prototype that helps alcohol label compliance agents verify uploaded label images against application data quickly and simply.

The app should reduce repetitive manual checks while preserving human judgment for nuanced cases.

## Primary Users
- Compliance agents with mixed technical comfort levels.
- Senior reviewers who want fast assistance but still make the final call.
- Occasional heavy users processing large batches of applications.

## Core User Problem
Agents currently verify labels by visually comparing fields on the application with the label artwork. This is repetitive, time-consuming, and error-prone when done at scale.

## Product Principles
- Fast first: return results in about 5 seconds or less.
- Simple enough for a non-technical user to understand immediately.
- Batch-friendly for peak intake periods.
- Assistive, not autonomous: surface likely matches and mismatches, but keep human review in control.
- Robust to imperfect label images when possible, especially angle, glare, and poor lighting.

## Scope

### In Scope
- Upload one or many label images at once.
- Show a clear results view for each label.
- Compare uploaded image content against provided application fields.
- Flag obvious matches and mismatches for:
  - Brand name
  - Class / type designation
  - Alcohol content
  - Net contents
  - Government warning statement
  - Required government warning formatting when detectable
- Support a simple approve / needs review / reject outcome.
- Show confidence or rationale for each check in plain language.
- Provide feedback when an image is unreadable or too ambiguous.

### Out of Scope for Prototype
- Direct integration with COLA or other internal systems.
- Long-term storage of sensitive or regulated data.
- Workflow automation that replaces human review.
- Cloud dependencies that require outbound network access.
- Full regulatory rule coverage for every beverage type and edge case.

## Functional Requirements

### Upload and Batch Processing
- Users can upload a single label image or multiple images in one session.
- The app should accept common image formats.
- Batch jobs should process independently so one bad image does not block the rest.
- Users should see per-item status updates during processing.

### Verification Checks
- The system should extract or inspect key label fields and compare them to submitted application data.
- Each check should clearly show pass, fail, or uncertain.
- The app should treat the government warning statement as a high-priority exact-match check when possible.
- The app should distinguish obvious formatting issues from content mismatches when feasible.
- The app should allow nuanced handling for cases like capitalization differences in brand names.

### Result Presentation
- Results should be readable without training.
- The screen should emphasize the overall decision first, then supporting evidence.
- The app should surface why a result was flagged, in plain language.
- Users should be able to quickly move through a batch without friction.

### Image Quality Handling
- The app should tolerate imperfect images better than a strict OCR-only flow.
- It should detect when an image is too degraded to support a reliable decision.
- In unreadable cases, the app should prompt for a better image or manual review.

## Non-Functional Requirements
- Latency: target under 5 seconds per label for an initial result.
- Usability: intuitive for users with limited technical experience.
- Accessibility: clear hierarchy, large readable text, obvious controls, and minimal hidden actions.
- Reliability: no batch-wide failure because one item errors.
- Security: prototype should avoid storing sensitive data unnecessarily.
- Deployment: should work in an environment with restricted outbound network access.

## UX Requirements
- One obvious primary action to upload labels.
- Minimal navigation and no cluttered settings surface.
- Clear status messaging for queued, processing, completed, and failed items.
- Results should be easy to scan on first glance.
- Use language that a non-technical compliance agent would understand.

## Suggested Workflow
1. User uploads one or more label images.
2. User enters or pastes the corresponding application data.
3. The app analyzes each image and compares it against the supplied fields.
4. The app returns a fast summary with per-field verification results.
5. The user reviews flagged items and makes the final decision.

## Success Criteria
- A user can complete a single-label verification quickly and understand the outcome without training.
- A batch of labels can be uploaded and processed without one-at-a-time handling.
- The app returns useful results fast enough that agents would reasonably prefer it over manual checking.
- The app handles at least the core required fields and the government warning check.

## Assumptions
- This prototype is standalone and does not need to connect to COLA.
- The initial dataset can be supplied manually or through simple mock inputs.
- Human review remains the final authority.
- The first version can focus on common distilled spirits label patterns and then broaden later.

## Risks and Trade-Offs
- Overly strict matching may reject valid labels with harmless casing or formatting differences.
- OCR or vision quality may be inconsistent on angled or low-quality images.
- A complex interface would reduce adoption among less technical users.
- External model dependencies may violate connectivity or deployment constraints.

## Open Questions for Implementation
- Should the prototype use OCR only, multimodal model analysis, or a hybrid approach?
- What exact data fields will users provide alongside each upload?
- Should batch upload support mixed beverage types in one run?
- Should results be exportable for review or recordkeeping?
