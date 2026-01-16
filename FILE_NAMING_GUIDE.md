# File Naming Convention Guide

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

## Key Rules Summary

| Rule | Why It Matters |
|------|----------------|
| **`_registration` suffix is STRICT** | Tracking needs registered (jump-corrected) data; 3D reconstruction needs unregistered (spatial accuracy). Mixing these breaks results. |
| **Organelle type must match** | Pipeline handles each organelle type differently (single vs. multiple instance detection). |
| **Sperm ID must match** | Prevents accidental mixing of data from different cells. |
| **Case/spacing is flexible** | Makes naming more forgiving; "MO_16.tif" and "mo 16.tif" both work. |

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

