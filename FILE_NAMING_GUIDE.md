# File Naming Convention Guide

## Quick Start: Standard File Organization

For easiest pipeline execution, organize your sperm cell folders using this standard structure:

```
Sperm {sperm_id}/
├── pseudopod_stack_{sperm_id}.tif              (single version)
├── nucleus_stack_{sperm_id}.tif                (single version)
├── sperm_cell_stack_{sperm_id}.tif             (single version)
│
├── MO_stack_{sperm_id}_registration.tif        ⚠️ REQUIRED FOR TRACKING
├── MO_stack_{sperm_id}.tif                     ⚠️ REQUIRED FOR 3D RECONSTRUCTION
│
├── mitochondria_stack_{sperm_id}_registration.tif ⚠️ REQUIRED FOR TRACKING
├── mitochondria_stack_{sperm_id}.tif           ⚠️ REQUIRED FOR 3D RECONSTRUCTION
│
├── MO tracking/
│   └── temp_long.csv                           (or any naming)
│
└── Mito tracking/
    └── temp_long.csv                           (or any naming)
```

**Key requirement**: For **mitochondria and MO**, you MUST have **both versions** in your folder:
- **`_registration` version**: Used for tracking organelles across Z-slices (jump corrections applied)
- **No suffix version**: Used for 3D reconstruction and spatial analysis (preserves original coordinates)

If you're missing one version, the pipeline will fail with a "No file found" error.

---

## Overview

The pipeline uses **flexible file naming conventions** that accept variations in:
- **Case**: `nucleus`, `Nucleus`, `NUCLEUS`
- **Spacing**: `sperm cell`, `sperm_cell`, `spermcell`
- **Optional "stack" keyword**: Files with or without the word "stack" in the name

However, the **registered vs. unregistered distinction remains strict** because it's critical for correct analysis:
- **Registered versions** (`_registration` suffix): Used for **tracking** (jump corrections applied)
- **Unregistered versions** (no suffix): Used for **3D reconstruction** (coordinates match masks)

---

## TIFF File Naming

### Single Organelles (Always Unregistered)
These organelles only need one version because they are single instances:

| Organelle | Acceptable Patterns |
|-----------|-------------------|
| **Pseudopod** | `pseudopod_stack_16.tif`, `pseudopod_16.tif`, `Pseudopod_stack_16.tif`, `pseudopod stack 16.tif` |
| **Nucleus** | `nucleus_stack_16.tif`, `nucleus_16.tif`, `Nucleus_stack_16.tif`, `nucleus stack 16.tif` |
| **Sperm Cell** | `sperm_cell_stack_16.tif`, `sperm_cell_16.tif`, `sperm cell stack 16.tif` |

### Multiple Organelles (BOTH Versions Required)

**You MUST provide both versions for each organelle**. The pipeline needs:
1. **Registered version** (`_registration` suffix): For tracking across Z-slices
2. **Unregistered version** (no suffix): For 3D reconstruction

| Organelle | **For Tracking (Registered)** | **For 3D (Unregistered)** |
|-----------|------------------------------|-------------------------|
| **MO** | `MO_stack_16_registration.tif`, `mo_stack_16_registration.tif`, `MO_16_registration.tif` | `MO_stack_16.tif`, `MO_16.tif`, `mo_stack_16.tif` |
| **Mitochondria** | `mitochondria_stack_16_registration.tif`, `Mito_16_registration.tif`, `mitochondria_16_registration.tif` | `mitochondria_stack_16.tif`, `mitochondria_16.tif`, `mito_16.tif` |

**Why both versions?**
- **Registered**: Image registration (stackreg) corrects for SEM ribbon compression, eliminating coordinate jumps. Critical for tracking.
- **Unregistered**: Original voxel coordinates match your 3D reconstruction goal. Needed for accurate spatial positions and distances.

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

## Key Rules Summary

| Rule | Why It Matters |
|------|----------------|
| **Both versions required for multi-instance organelles** | Tracking and 3D reconstruction use different versions. Missing either breaks the analysis. |
| **`_registration` suffix is STRICT** | Tracking needs registered (jump-corrected) data; 3D reconstruction needs unregistered (spatial accuracy). Mixing breaks results. |
| **Organelle type must match** | Pipeline handles each organelle type differently (single vs. multiple instance detection). |
| **Sperm ID must match** | Prevents accidental mixing of data from different cells. |
| **Case/spacing is flexible** | Makes naming more forgiving; "MO_16.tif" and "mo 16.tif" both work. |

---

---

---

## Troubleshooting

### "No [organelle] file found" Error
**Cause**: File naming doesn't match expected pattern or file doesn't exist.

**Solutions**:
- Check file exists in correct directory: `Sperm {sperm_id}/`
- Verify organelle name matches accepted names (nucleus, pseudopod, mitochondria, MO, sperm_cell)
- **For mitochondria/MO**: Ensure you have BOTH versions present (`_registration` AND without suffix)
- Verify registration suffix if applicable
- Check for typos and correct file extension (`.tif`, not `.tiff`)

### "Multiple files found, using first"
**Cause**: Duplicate files with same organelle/sperm_id exist in directory.

**Solution**: Remove duplicate files or rename to distinguish them.

### Wrong Version Selected (Registered vs. Unregistered)
**Cause**: Code selected wrong version of file (registered when it needed unregistered, or vice versa).

**Solutions**:
- Verify files have correct `_registration` suffix in their names
- Check that tracking CSVs are in correct subdirectories (`MO tracking/` or `Mito tracking/`)
- If metrics look wrong, verify overlays in TRACKING_OVERLAY_GUIDE.md

