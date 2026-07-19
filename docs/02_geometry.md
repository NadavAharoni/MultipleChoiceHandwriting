# Geometry Detection - Design Revision

**Version:** 2  
**Status:** Planned (Iteration 0002)

---

# Background

The original implementation planned to detect the entire scanned page, estimate its four corners, perform a perspective correction, and only then locate the answer table.

After collecting additional real-world scans, this approach proved unnecessarily complicated.

The scans exhibit:

- Small perspective distortion.
- Small rotation (typically only a few degrees).
- Large variation in page placement inside the scanner.
- Occasionally another sheet partially covering the page.
- Folded corners and imperfect page boundaries.

In contrast, the answer table itself is remarkably consistent.

---

# New Design

Instead of detecting the page, the pipeline will detect the **answer table directly**.

The answer table is the only structure on the page containing:

- long horizontal lines
- long vertical lines
- regular spacing
- a rectangular grid

This makes it a much more reliable target than the paper boundary.

The new processing pipeline becomes:

```
Load image
      │
      ▼
Threshold
      │
      ▼
Extract horizontal lines
      │
      ▼
Extract vertical lines
      │
      ▼
Locate answer table
      │
      ▼
Normalize table
      │
      ▼
Split into answer cells
```

---

# Why Morphology?

OpenCV provides morphological operators that are extremely effective at extracting long straight lines.

Instead of searching for contours or page outlines, we separately extract:

- horizontal lines
- vertical lines

The combination of these two images forms a clean representation of the answer grid.

Conceptually:

```
Threshold
      │
      ├──────────────┐
      ▼              ▼
Horizontal      Vertical
 Extraction     Extraction
      │              │
      └──────┬───────┘
             ▼
        Grid Detection
```

---

# Why We No Longer Crop the Bottom of the Page

An earlier idea was to crop the lower 45% of the page before searching for the answer table.

Additional scans demonstrated that this assumption is not reliable.

The page may be shifted vertically by the scanner, causing the answer table to appear significantly higher or lower.

Rather than relying on a fixed crop, the algorithm will search the entire page for the unique grid structure.

This makes the algorithm independent of scanner alignment.

---

# Grid Detection Strategy

The geometry stage will identify the answer table by detecting a regular grid rather than a rectangle.

Characteristics include:

- approximately 11 horizontal lines
- several long vertical lines
- nearly uniform row spacing
- rectangular layout

No other structure on the exam page shares these properties.

---

# Normalization

Once detected, the table will be transformed into a fixed-size image.

Example target size:

```
1200 × 600 pixels
```

All later stages will operate exclusively in this normalized coordinate system.

Advantages:

- independent of scanner resolution
- independent of paper placement
- independent of small rotations
- simplifies all later geometry

---

# Future Stages

Iteration 0002

- Detect horizontal lines
- Detect vertical lines
- Produce debug images

Iteration 0003

- Detect answer table
- Normalize table
- Save `answer_table.png`

Iteration 0004

- Split normalized table into rows
- Crop each answer cell
- Pass cells to the handwriting recognizer

---

# Design Philosophy

Rather than solving the general problem of document detection, this project exploits the fact that all exams use the same printed form.

By leveraging the fixed geometry of the answer table, the detection algorithm becomes:

- simpler
- faster
- more robust
- easier to debug

This project intentionally favors reliability on a known document layout over general-purpose document analysis.
