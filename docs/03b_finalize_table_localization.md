# Iteration 03b – Finalize Table Localization

**Status:** Required before Iteration 04

## Objective

Complete the table localization milestone.

The implementation is close to completion, but at least one sample still clips part of the handwritten answer area.

Do not begin answer segmentation, OCR, or grading until this issue is resolved.

---

## Current Status

Most scans are localized correctly.

Remaining issues observed:

- At least one scan clips the left side of the handwritten answer area.
- Some scans crop the printed question numbers on the right.

The second issue is acceptable if the handwritten answer cells are completely preserved.

---

## Updated Acceptance Criteria

The milestone is complete only when:

- Every scan in the current dataset is localized successfully.
- Every handwritten answer cell is fully contained in the detected table.
- No handwritten strokes are clipped.
- Previously successful scans continue to succeed.
- The implementation remains robust and maintainable.

Printed question numbers may be partially outside the crop if this improves localization reliability.

---

## Validation

Run the implementation against the complete dataset.

Produce a summary including:

- Total scans processed
- Successful localizations
- Failed localizations

If any scan fails, list the filenames and briefly describe the failure.

Do not mark this milestone complete while failures remain.

---

## Deliverables

- Updated implementation.
- Updated debug images.
- Validation summary.
- Updated documentation if needed.

---

## Notes

The objective of this iteration is reliability.

A stable localization stage is required before work begins on answer segmentation and handwriting recognition.
