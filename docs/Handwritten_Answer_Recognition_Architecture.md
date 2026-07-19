# Handwritten Answer Sheet Recognition - Architecture

## Goal

Automatically extract handwritten answers from scanned multiple-choice
answer sheets.

This is **not** a general OCR problem. The solution exploits:

-   Fixed page layout
-   Five possible letters (א--ה)
-   Optional multiple answers (e.g. א,ג)
-   Consistent handwriting within each student's sheet
-   Three known exam versions (used only as an optional confidence aid)

## Pipeline

``` text
Scan
  ↓
Locate answer tables
  ↓
Perspective correction
  ↓
Detect rows
  ↓
Extract answer cells
  ↓
Remove printed grid
  ↓
Threshold & clean handwriting
  ↓
Split into symbols (letters / commas)
  ↓
Extract image features
  ↓
Cluster similar symbols per student
  ↓
Identify clusters using classifier + confidence
  ↓
Reassemble answers
  ↓
(Optional) Use exam version & answer key to improve confidence
  ↓
Export answers
```

## Main modules

1.  Geometry (OpenCV)
    -   Detect tables
    -   Perspective correction
    -   Crop answer cells
2.  Segmentation
    -   Remove printed lines
    -   Separate letters and commas
3.  Recognition
    -   Compute descriptors (HOG/CNN embedding)
    -   Cluster symbols per student
    -   Classify only high-confidence clusters
4.  Reasoning
    -   Share evidence between occurrences of the same handwriting
    -   Keep probabilities instead of forcing early decisions
    -   Optionally use exam version and answer key as a weak prior
5.  Review UI
    -   Present only low-confidence answers
    -   User corrections immediately improve remaining predictions

## Suggested Python libraries

-   OpenCV
-   NumPy
-   scikit-image
-   scikit-learn
-   pandas
-   matplotlib (debug visualizations)
