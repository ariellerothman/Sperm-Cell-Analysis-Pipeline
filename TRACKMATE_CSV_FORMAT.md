# TrackMate CSV Format Documentation

Complete guide to understanding TrackMate tracking CSV files used in the sperm cell analysis pipeline.

---

## Overview

TrackMate exports tracking data in CSV format. The pipeline processes these files through several conversion steps:

1. **Raw Export** → TrackMate exports wide format (organizes by blocks)
2. **Block Reorganization** → Merge blocks horizontally 
3. **Format Conversion** → Wide format → Long format
4. **Analysis** → Used for watershed segmentation with tracking markers

---

## Raw TrackMate Export (Wide Format)

### Example Input File
File: `MO_tracking_results_16.csv` (or similar naming)

```
Frame,X1,Y1,Flag1,X2,Y2,Flag2,X3,Y3,Flag3,...,X400,Y400,Flag400
Tracks 1
1,100,150,,,,,,
2,105,155,,,,,,
3,110,160,,,,,,
...
Tracks 76
75,200,250,,,,,,
76,205,255,,,,,,
...
Tracks 151
150,300,350,,,,,,
...
```

### Structure

- **Columns**: `Frame` + pairs of (X, Y, Flag) columns for each track
  - `X1, Y1, Flag1` = coordinates for Track 1
  - `X2, Y2, Flag2` = coordinates for Track 2
  - Up to 400 tracks (configurable)

- **Block Separators**: Rows containing "Tracks N" mark where TrackMate grouping changes
  - TrackMate groups tracks into blocks (default 75 tracks per block)
  - Block separators indicate: "next 75 tracks follow"

- **Empty Cells**: Missing tracking points appear as blank cells
  - If Track 2 isn't visible in Frame 5: X2 and Y2 cells are empty
  - Flag column indicates confidence/status

- **Frame Numbering**: 1-indexed (Frame 1 = first Z-slice)

---

## After Block Reorganization

After running `move_tracks_horizontally()`:

```
Frame,X1,Y1,Flag1,X2,Y2,Flag2,...,X75,Y75,Flag75,X76,Y76,Flag76,...,X400,Y400,Flag400
1,100,150,,105,155,,,,,,200,250,,
2,102,152,,108,158,,,,,,205,255,,
3,105,155,,110,160,,,,,,210,260,,
...
```

### What Changed

- Block separator rows removed
- Tracks renumbered across all blocks
- Track 76 (first track in 2nd block) now appears as column X76
- All tracks in single continuous set of columns (1-400)

---

## Final Long Format (Processed)

After running `wide_to_long()`:

File: `MO_temp_long.csv`

```
Frame,Track,X,Y,Flag
1,1,100,150,
1,2,105,155,
1,76,200,250,
2,1,102,152,
2,2,108,158,
2,76,205,255,
3,1,105,155,
3,2,110,160,
3,76,210,260,
...
```

### Structure

- **One row per tracking point** (one observation)
- **Columns**:
  - `Frame`: Z-slice index (1-indexed from TrackMate)
  - `Track`: Organelle instance ID (1-400)
  - `X`: X-pixel coordinate (horizontal in image)
  - `Y`: Y-pixel coordinate (vertical in image)
  - `Flag`: TrackMate quality flag (often empty)

- **Example Row**: Frame 3, Track 76 detected at (X=210, Y=260)
  - Means: In Z-slice 3, organelle instance #76 is at pixel position (210, 260)

---

## Key Concepts

### Track ID vs Frame
- **Track ID** (1-400): Unique identifier for an organelle instance
  - Same Track ID across multiple frames = same organelle being tracked
  - Used to follow an organelle's movement through the Z-stack

- **Frame**: Z-slice number in the 3D stack
  - Frame 1 = first Z-slice (most inferior)
  - Frame N = last Z-slice (most superior)

### Tracking in 3D
The long format CSV enables 3D tracking:

```
Track 42:
  Frame 1: (100, 150) ← Same organelle #42
  Frame 2: (102, 155) ← Moves slightly in Z=2
  Frame 3: (105, 158) ← Moves slightly in Z=3
  Frame 4: (103, 160) ← Moves slightly in Z=4
  ...
  Frame 10: (95, 145)  ← Visible across many Z-slices
```

---

## Coordinate System

### Image Space vs Array Space
The CSV coordinates match **image space** (how ImageJ/FIJI displays them):

```
CSV: Frame=5, X=200, Y=150

Array indices (Python):
  z_index = Frame - 1 = 4  (0-indexed, Frame is 1-indexed)
  y_index = Y = 150        (Y stays Y)
  x_index = X = 200        (X stays X)

Access pixel:
  value = stack[z_index, y_index, x_index]
            ↓
  value = stack[4, 150, 200]
```

### Why This Matters
- CSV uses 1-indexed frames (TrackMate convention)
- Python uses 0-indexed arrays
- The pipeline converts: `z_array_index = Frame - 1`

---

## Common Issues & Solutions

### Issue: CSV Has 0 Rows After Conversion
**Cause**: TrackMate export file is empty or headers are wrong

**Check**:
```bash
# Look at the file
head -20 MO_tracking_results_16.csv

# Count data rows
wc -l MO_tracking_results_16.csv
```

---

### Issue: Some Frames Have No Tracks
**This is normal**. Tracks may:
- Start later (not in early frames)
- End early (not in late frames)
- Disappear and reappear (due to image artifacts)

**Pipeline handles this**: Watershed only uses frames with valid marker points.

---

### Issue: Track IDs Jump (1, 2, 3... 75, 76, 77...)
**This is expected**. TrackMate may skip IDs or use non-consecutive numbering.

**Not a problem**: The pipeline uses Track IDs as-is from the CSV.

---

### Issue: X/Y Values Are Out of Range
**Cause**: Coordinates from full image, but stack might be cropped

**Solution**: Use registered (cropped) TIFF stack that matches CSV coordinates

---

## Validation Checklist

When troubleshooting tracking problems:

- [ ] CSV file exists and has data rows (not just header)
- [ ] Column names are: `Frame`, `Track`, `X`, `Y`, `Flag`
- [ ] Frame values are 1-indexed (start from 1, not 0)
- [ ] Track IDs are positive integers
- [ ] X, Y coordinates are within image dimensions
- [ ] Coordinates match the TIFF stack being used (both registered or both raw)
- [ ] At least 2 tracks per frame (configurable MIN_TRACKS in config.py)

---

## Example: End-to-End Workflow

### Step 1: TrackMate Exports
File: `Sperm 16/MO tracking/MO_tracking_results_16.csv` (wide format with block separators)

### Step 2: Block Reorganization
```python
move_tracks_horizontally(
    input_csv="MO_tracking_results_16.csv",
    output_csv="MO_temp_wide.csv"
)
```
Result: Removes separators, merges tracks into columns 1-400

### Step 3: Format Conversion
```python
wide_to_long(
    input_csv="MO_temp_wide.csv",
    output_csv="MO_temp_long.csv",
    num_tracks=400
)
```
Result: One row per observation (Frame, Track, X, Y, Flag)

### Step 4: Used in Analysis
```python
compute_organelle_metrics(
    organelle_name="MO",
    segmentation_path="MO_stack.tif",
    csv_path="MO_temp_long.csv",  # ← Long format
    ...
)
```

The watershed algorithm:
1. Reads `MO_temp_long.csv`
2. Places markers at (Frame-1, Y, X) with value = Track ID
3. Runs watershed to segment each track
4. Returns labeled regions with Track IDs as labels

---

## File Locations in Pipeline

```
Sperm {ID}/
├── {Organelle} tracking/
│   ├── {Raw export}.csv          (original TrackMate export)
│   ├── {Organelle}_temp_wide.csv (after block reorganization)
│   └── {Organelle}_temp_long.csv (final long format, used for analysis)
└── tracking_overlays/
    └── {organelle}_overlays/      (PNG visualizations)
        ├── frame_001_overlay.png
        ├── frame_002_overlay.png
        └── ...
```

---

## Summary

| Concept | Details |
|---------|---------|
| **Raw Format** | Wide format with (X, Y, Flag) pairs per track, block separators |
| **Processing** | Remove separators → reorganize blocks → pivot to long format |
| **Final Format** | Long format: Frame, Track, X, Y, Flag (one row per observation) |
| **Frame Indexing** | 1-indexed (comes from TrackMate, convert to 0-indexed for arrays) |
| **Track ID** | Unique identifier for organelle instance, preserved through pipeline |
| **Use in Analysis** | Markers for watershed segmentation, enables tracking of individual organelles |
| **Validation** | Check CSV exists, columns correct, frame indexing, coordinate ranges |

---

**Document Updated**: January 16, 2026
