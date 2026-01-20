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

### Option 1: Use the Notebook (Easiest)

**Step 2e** in `Sperm_Cell_Analysis_Pipeline.ipynb` automatically generates overlays:

```python
# Just change this to the cell you want to analyze
sperm_id = 16  # (set in configuration cell)

# Configure which organelles to visualize
organelles_to_visualize = ["mitochondria", "MO"]  # or just ["mitochondria"]

# Run the cell - overlays are generated automatically
# Saved to: Sperm {ID}/{organelle} tracking/tracking_overlays/{organelle}_overlays/
```

### Option 2: Generate Programmatically

```python
from src.tracking import visualize_tracking

# Generate overlays for mitochondria
mito_overlay_dir = visualize_tracking(
    tiff_path="Sperm 14/mitochondria_stack_14_registration.tif",
    csv_path="Sperm 14/Mito tracking/tracking.csv",
    frames_to_display=200,  # Show first 200 frames
    save_overlays=True,     # Save PNG files to disk
    output_dir="Sperm 14/Mito tracking"  # Optional: custom output location
)

print(f" Overlays saved to: {mito_overlay_dir}")
```

---

## Where Overlays Are Stored

All overlays follow the same directory structure:

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
