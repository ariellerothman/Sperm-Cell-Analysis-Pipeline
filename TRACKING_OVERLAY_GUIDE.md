# Tracking Overlay Verification Guide

**Quick Summary**: Use tracking overlays to **visually verify that the tracking system correctly linked organelles across image slices**. If you get weird metrics for mitochondria (Mito) or MO, check the overlays first!

---

## What Are Tracking Overlays?

Tracking overlays are **PNG images** that show:
- Your original microscopy image (as gray background)
- **White circles**: All detected organelles in that frame
- **Red circles with numbers**: Organelles with assigned track IDs
- **Title**: Frame number and organelle count

**One PNG per Z-slice** → you can flip through them like a slideshow to see how tracking performed.

---

## How to Generate Overlays

### Option 1: Single Cell (Step 2e in Notebook)

**When to use**: Analyzing one sperm cell and want to verify tracking quality before running metrics.

**Steps**:
1. Set `sperm_id` in the configuration cell at the top of the notebook
2. Go to **Step 2e: Visualize Tracking Overlays**
3. Configure which organelles to visualize:

```python
organelles_to_visualize = ["mitochondria", "MO"]  # or just ["mitochondria"]
```

4. Run the cell - overlays are generated automatically
5. Overlays saved to: `Sperm {ID}/{organelle} tracking/tracking_overlays/{organelle}_overlays/`

### Option 2: Multiple Cells (Step 3 - Batch Processing)

**When to use**: Analyzing many cells and want overlays for all of them automatically.

**What happens**:
- Overlays are **automatically generated** while batch processing runs
- No extra step needed—they're created as part of the standard workflow
- Each cell gets overlays saved to the same directory structure
- Status messages show: "Tracking overlays saved (mitochondria)" for each processed cell

**Output**:
- All overlays organized by sperm cell ID
- Batch processing prints summary of where overlays were saved

---

## Where Overlays Are Stored

All overlays follow the same directory structure, whether generated via Option 1 or Option 2:

```
Sperm {ID}/
└── {Organelle} tracking/
    └── tracking_overlays/
        └── {organelle}_overlays/
            ├── frame_001_overlay.png
            ├── frame_002_overlay.png
            ├── frame_003_overlay.png
            └── ... (one PNG per frame)
```

**Examples**:
- `Sperm 14/Mito tracking/tracking_overlays/mitochondria_overlays/frame_042_overlay.png`
- `Sperm 16/MO tracking/tracking_overlays/MO_overlays/frame_150_overlay.png`

---

## How to Interpret Overlays

###  Good Tracking Looks Like:

1. **Consistent IDs across frames**
   - Track #5 appears in frames 5, 6, 7, 8 (same ID stays same)
   - Tracks appear and disappear naturally (organelles enter/exit field)

2. **Smooth motion**
   - Red circles move gradually from one frame to the next
   - No sudden jumps 

3. **Clear separation**
   - Different organelles have different IDs
   - ID numbers are readable

---

## CSV Format Reference

The pipeline processes TrackMate CSV files in specific formats. Quick summary:
- **Input**: Wide format with block separators (TrackMate raw export)
- **Processing**: Remove separators → reorganize blocks → convert to long format
- **Output**: Long format with columns: Frame, Track, X, Y, Flag
- **1-indexed**: Frame numbering starts from 1 (convert to 0-indexed for Python arrays)
- **Validation**: Check CSV exists, columns correct, coordinate ranges valid

---
