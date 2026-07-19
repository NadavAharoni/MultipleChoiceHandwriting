# Iteration 03 – Table Detection

**Status:** Planned

---

# Goal

The goal of this iteration is to reliably locate the answer table on every scanned exam.

This iteration ends when the project can automatically extract the answer table from every scan in the current dataset.

No handwriting recognition is required yet.

---

# Input

The geometry stage already produces intermediate images that emphasize the table structure.

This iteration should build on the existing geometry pipeline.

---

# Output

For every scanned page, produce a normalized image containing only the answer table.

Example:

```
scan.jpg
    ↓
answer_table.png
```

The output image should:

- contain only the answer table
- be correctly aligned
- have a fixed size
- preserve all printed grid lines

The exact output dimensions are left to the implementation.

---

# Requirements

The implementation should:

- detect the answer table automatically
- tolerate variations in page placement
- tolerate small rotations
- tolerate partially covered pages
- avoid assumptions about absolute page position

The implementation should exploit the fixed layout of the exam form whenever appropriate.

---

# Debug Output

Continue generating intermediate debug images.

In addition, generate a visualization showing the detected answer table on the original page.

The visualization should make it easy to verify whether the localization succeeded.

---

# Acceptance Criteria

The iteration is complete when:

- every scan in the current dataset produces an `answer_table.png`
- the extracted table is correctly aligned
- the entire table is present
- no significant surrounding page content is included

Minor differences in margins are acceptable.

---

# Out of Scope

This iteration does **not** include:

- handwriting recognition
- answer segmentation
- OCR
- exam grading

Those will be implemented in later iterations.

---

# Deliverables

- Updated geometry pipeline
- `answer_table.png` for every processed scan
- Additional debug visualization(s)
- Updated documentation if needed

---

# Notes

Implementation details are intentionally left to the coding agent.

The objective is a robust and maintainable solution rather than a specific computer vision technique.
