# File Naming Convention Guide

## Overview

Your pipeline now uses **flexible file naming conventions** that accept variations in:
- **Case**: `nucleus`, `Nucleus`, `NUCLEUS`
- **Spacing**: `sperm cell`, `sperm_cell`, `spermcell`
- **Optional "stack" keyword**: Files with or without the word "stack" in the name

However, the **registered vs. unregistered distinction remains strict** because it's critical for correct analysis:
- **Registered versions** (`_registration` suffix): Used for **tracking** (jump corrections applied)
- **Unregistered versions** (no suffix): Used for **3D reconstruction** (coordinates match masks)

---

## TIFF File Naming

### Single Organelles (Always Unregistered)
These are always found unregistered because they don't need registration:

| Organelle | Acceptable Patterns |
|-----------|-------------------|
| **Pseudopod** | `pseudopod_stack_16.tif`, `pseudopod_16.tif`, `Pseudopod_stack_16.tif`, `pseudopod stack 16.tif` |
| **Nucleus** | `nucleus_stack_16.tif`, `nucleus_16.tif`, `Nucleus_stack_16.tif`, `nucleus stack 16.tif` |
| **Sperm Cell** | `sperm_cell_stack_16.tif`, `sperm_cell_16.tif`, `sperm cell stack 16.tif` |

### Multiple Organelles (Can Be Registered OR Unregistered)

| Organelle | **For Tracking (Registered)** | **For 3D (Unregistered)** |
|-----------|------------------------------|-------------------------|
| **MO** | `MO_stack_16_registration.tif`, `mo_stack_16_registration.tif`, `MO_16_registration.tif` | `MO_stack_16.tif`, `MO_16.tif`, `mo_stack_16.tif` |
| **Mitochondria** | `mitochondria_stack_16_registration.tif`, `Mito_16_registration.tif`, `mitochondria_16_registration.tif` | `mitochondria_stack_16.tif`, `mitochondria_16.tif`, `mito_16.tif` |

**Key Point**: The presence of `_registration` suffix determines which version is used. The code automatically selects:
- Registered versions when tracking
- Unregistered versions when reconstructing

---

## CSV File Naming

Tracking CSVs are found using flexible patterns:

| Organelle | Acceptable Patterns |
|-----------|-------------------|
| **MO Tracking** | `MO_tracking_16.csv`, `mo_tracking_16.csv`, `MO tracking 16.csv`, `tracking_MO_16.csv` |
| **Mitochondria Tracking** | `mitochondria_tracking_16.csv`, `mito_tracking_16.csv`, `Mito tracking 16.csv`, `tracking_mitochondria_16.csv` |

Subdirectory locations:
- `Sperm 16/MO_tracking_16.csv` or `Sperm 16/MO tracking/temp_long.csv`
- `Sperm 16/mitochondria_tracking_16.csv` or `Sperm 16/Mito tracking/temp_long.csv`

---

## How the Matching Works

### TIFF Discovery (`find_file_by_pattern`)
1. Accepts organelle name with flexible capitalization
2. Builds glob pattern: `*{organelle}*{sperm_id}*.tif`
3. **Filters** by registration status:
   - If `registered=True`: keeps only files with `_registration` suffix
   - If `registered=False`: excludes files with `_registration` suffix
4. Returns first match found

Example:
```python
# For tracking (needs registered version)
find_file_by_pattern(folder, "MO", 16, registered=True)
# Finds: "MO_stack_16_registration.tif"

# For 3D reconstruction (needs unregistered version)
find_file_by_pattern(folder, "MO", 16, registered=False)
# Finds: "MO_stack_16.tif" (NOT the _registration version)
```

### CSV Discovery (`find_csv_by_pattern`)
1. Tries multiple glob patterns in order:
   - `*{organelle}*tracking*{sperm_id}*.csv`
   - `*tracking*{organelle}*{sperm_id}*.csv`
   - `*{organelle}*{sperm_id}*tracking*.csv`
2. Returns first match from any pattern
3. Removes duplicates

---

## Tracking Overlay Output Files

When you generate tracking overlays using Step 2e or the `visualize_tracking()` function, PNG images are automatically saved to a standard location:

### Output Directory Structure

```
Sperm {ID}/
├── Mito tracking/
│   ├── tracking.csv                          (original tracking data)
│   └── tracking_overlays/
│       └── mitochondria_overlays/
│           ├── frame_001_overlay.png
│           ├── frame_002_overlay.png
│           ├── frame_003_overlay.png
│           └── ...
│
└── MO tracking/
    ├── tracking.csv                          (original tracking data)
    └── tracking_overlays/
        └── MO_overlays/
            ├── frame_001_overlay.png
            ├── frame_002_overlay.png
            ├── frame_003_overlay.png
            └── ...
```

### What the Overlays Show

Each PNG file is named `frame_NNN_overlay.png` where NNN is the frame (Z-slice) number, formatted with leading zeros:
- `frame_001_overlay.png` = first Z-slice
- `frame_002_overlay.png` = second Z-slice
- `frame_200_overlay.png` = 200th Z-slice

**Content of each PNG**:
- **Gray background**: Original microscopy image
- **White circles**: Detected organelle instances (all detected organelles in that frame)
- **Red circles with numbers**: Organelles with assigned track IDs (track linking established)
- **Title**: "Slice N (Frame N, Tracks: X)" showing frame number and total tracked organelles

### Why Overlays Matter for Metrics Quality

Tracking overlays are your **quality control tool** for catching problems before they affect metrics:

1. **Identify tracking failures**: If metrics look wrong, overlays show if tracking broke
2. **Verify segmentation**: See if organelles are being detected (white circles)
3. **Spot registration issues**: Erratic circle motion reveals registration artifacts
4. **Validate before batch processing**: Generate overlays for 1-2 cells before processing entire batch

**Quick diagnostic workflow**:
```
Bad metrics for cell X
        ↓
Generate overlays for cell X
        ↓
Review overlays frame-by-frame
        ↓
  Does tracking look good?
        ↙         ↘
      YES          NO
       ↓           ↓
  Problem is    Problem is
   in metrics   in tracking
    or mask       or
  segmentation  registration
```

---

## When Strict Naming Matters

Your system **preserves strictness** where it's critical:

### ✅ Registered vs. Unregistered is STRICT
- Mixing these causes incorrect results
- Tracking uses registered (eliminates SEM image jumps)
- 3D reconstruction uses unregistered (preserves spatial relationships)
- The code automatically enforces this distinction

### ✅ Organelle Type is STRICT
- Different organelles have different analysis approaches
- nucleus, pseudopod, sperm_cell → single instance extraction
- mitochondria, MO → watershed with tracking markers

### 🔆 Everything Else is FLEXIBLE
- Capitalization
- Spacing (`_` vs spaces)
- Optional "stack" keyword
- File organization (subdirectories)

---

## Recommended Best Practices

While flexible naming is supported, consistency helps readability:

### Suggested Standard Format
```
Sperm {sperm_id}/
├── pseudopod_stack_{sperm_id}.tif
├── nucleus_stack_{sperm_id}.tif
├── sperm_cell_stack_{sperm_id}.tif
├── MO_stack_{sperm_id}_registration.tif
├── MO_stack_{sperm_id}.tif
├── mitochondria_stack_{sperm_id}_registration.tif
├── mitochondria_stack_{sperm_id}.tif
├── MO tracking/
│   └── temp_long.csv
└── Mito tracking/
    └── temp_long.csv
```

This format:
- ✅ Clearly distinguishes registered vs. unregistered
- ✅ Uses consistent naming across all cells
- ✅ Works with flexible file discovery
- ✅ Easy to maintain and audit

---

## Troubleshooting

### "No [organelle] file found" Error
The file finder looks for:
1. Files matching `*{organelle}*{sperm_id}*.tif`
2. Correct registration status (registered or unregistered)

**Solutions**:
- Check file exists in correct directory: `Sperm {sperm_id}/`
- Verify registration suffix if needed
- Check for typos in organelle name
- Ensure `.tif` extension (not `.tiff` or `.TIF`)

### "Multiple files found, using first"
If you have duplicate files with same organelle/sperm_id, the first alphabetical match is used.

**Solution**: Remove duplicate files or rename to distinguish them.

### Wrong Version Selected (Registered vs. Unregistered)
If tracking seems wrong or 3D coordinates are misaligned, verify:
- Tracking calls use `registered=True`
- 3D reconstruction uses `registered=False`
- File actually has correct suffix in name

---

## Code Changes Made

### `src/utils.py`
- Added `find_file_by_pattern()`: Flexible TIFF file discovery
- Added `find_csv_by_pattern()`: Flexible CSV discovery
- Updated `get_file_paths()`: Uses new flexible functions

### `src/tracking.py`
- Updated `find_input_csv()`: Multiple glob pattern matching
- Updated `run_tracking_pipeline()`: Uses flexible TIFF discovery

Both modules now import `glob` for pattern matching and handle file discovery gracefully with informative error messages.
