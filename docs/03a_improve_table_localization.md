# Iteration 03a – Improve Table Localization

**Status:** Required before starting Iteration 04

## Objective

The previous implementation successfully detects the answer table for many scans, but not all.

Do not begin answer segmentation or OCR.

Your only objective is to improve the existing table localization until it succeeds on the entire current dataset.

---

## Current Situation

Most scans are localized correctly.

Several scans produce a bounding box that is significantly wider than the actual answer table.

The vertical position is generally correct.

The remaining work is to make the horizontal localization reliable.

---

## Requirements

Review the current implementation and improve it as needed.

You are free to redesign the localization algorithm if that results in a more robust solution.

Do not assume a particular implementation technique.

The goal is correctness and robustness.

---

## Acceptance Criteria

This iteration is complete only when all of the following are true:

- Every scan in the current dataset produces a detected table.
- The detected table contains the complete answer table.
- Very little surrounding page content is included.
- Previously successful scans continue to succeed.
- The implementation remains readable and maintainable.

---

## Validation

Run the implementation against the complete dataset.

Produce a short summary similar to:

- Total scans processed
- Successful localizations
- Failed localizations

If any scan fails, list its filename.

Do not consider the iteration complete while failures remain.

---

## Deliverables

- Updated implementation.
- Updated debug images.
- Validation summary.
- Updated documentation if appropriate.

---

## Notes

The project manager will decide when this milestone is complete.

Do not begin the next milestone until the acceptance criteria above are satisfied.
