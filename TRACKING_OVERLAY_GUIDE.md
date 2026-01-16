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

## Why Check Overlays?

### 🎯 The Problem It Solves

You ran the pipeline and got these results:
- ❌ Volume = 0 for some mitochondria
- ❌ Distance = NaN (not a number)
- ❌ Metrics that don't make biological sense
- ❌ Inconsistent results between similar cells

**You might think**: "The metrics code must be broken!"  
**Reality**: 90% of the time, it's **tracking failure**.

Tracking directly feeds into metrics:
1. CSV tracks which organelle is which frame
2. Metrics code uses tracking to assemble 3D structure
3. Bad tracking → bad 3D assembly → bad metrics

### ✅ How Overlays Help

Overlays show exactly what the tracking system did, making problems obvious:
- **Missing IDs** = organelles not tracked
- **ID jumps** = linking algorithm failed
- **Erratic circles** = registration artifact
- **Ghost tracks** = false detections

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

print(f"✅ Overlays saved to: {mito_overlay_dir}")
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

### ✅ Good Tracking Looks Like:

1. **Consistent IDs across frames**
   - Track #5 appears in frames 5, 6, 7, 8 (same ID stays same)
   - Tracks appear and disappear naturally (organelles enter/exit field)

2. **Smooth motion**
   - Red circles move gradually from one frame to the next
   - No sudden jumps or teleportation

3. **Clear separation**
   - Different organelles have different IDs
   - ID numbers are readable

4. **Expected population**
   - Number of tracked organelles stays roughly constant
   - Matches biological reality (e.g., ~20-30 mitochondria)

**Example good overlay**:
```
Frame 10: 25 white circles (all detected), 25 red circles with IDs
Frame 11: 24 white circles, 24 red circles with IDs (one left field)
Frame 12: 26 white circles, 26 red circles with IDs (one entered field)
```

### 🚨 Bad Tracking Looks Like:

1. **ID jumps or resets**
   - Track #5 in frame 10, then doesn't appear again until frame 20
   - Same organelle has different IDs in different frames

2. **Erratic motion**
   - Red circle moves far away in the next frame
   - Suggests registration artifact or detection error

3. **No IDs/missing tracks**
   - Many white circles but few/no red circles
   - Organelles detected but not linked

4. **Ghost tracks**
   - IDs appearing in random places, not on actual organelles
   - False detections not being filtered

**Example bad overlay**:
```
Frame 15: 22 white circles, but only 5 red circles with IDs ❌
Frame 16: Track #7 is 100 pixels away from frame 15 position ❌
Frame 17: Same physical organelle has ID #7 in frame 15, but ID #12 in frame 17 ❌
```

---

## Troubleshooting Tracking Problems

### Problem: Some frames have no track IDs

**What it means**: Organelles detected (white circles) but not linked to tracking.

**Causes**:
1. **Tracking CSV incomplete** - missing data for those frames
2. **Detection failed** - organelles too small/dim to detect
3. **Tracking broke** - linking algorithm couldn't connect to previous frame

**How to fix**:
1. Open original TIFF in ImageJ: `Sperm 14/mitochondria_stack_14_registration.tif`
2. Go to the problematic frame
3. Check if organelles are clearly visible
4. If visible but not detected → segmentation or registration issue
5. If invisible → image is bad, may need to re-register

### Problem: Circles jumping around erratically

**What it means**: Track IDs show motion that doesn't match physical movement.

**Causes**:
1. **Registration artifact** - stackreg created artificial shifts
2. **False detections** - algorithm finding things that aren't there
3. **Overlapping organelles** - two organelles too close, system confusing them

**How to fix**:
1. Compare registered vs unregistered: `*_registration.tif` vs `*.tif`
2. Look for shifted or warped regions in registered version
3. If registration looks bad → re-run stackreg with different parameters
4. If looks okay → problem is in segmentation masks

### Problem: Track IDs keep changing (same organelle = different IDs)

**What it means**: Linking algorithm failing to connect organelle across frames.

**Causes**:
1. **Organelles moved far between frames** - beyond linking distance threshold
2. **Detection missed frame** - organelle not detected in one slice
3. **Split detection** - one organelle detected as two (or vice versa)

**How to fix**:
1. Check `src/tracking.py` - look for `max_linking_distance` parameter
2. Increase if organelles legitimately move far between slices
3. Or fix segmentation to prevent split detections

---

## Quick Quality Control Workflow

### Before Running Batch Processing

```
1. Pick 1-2 sample cells
   ↓
2. Generate overlays for those cells
   ↓
3. Flip through frames quickly (look for obvious problems)
   ↓
4. Do overlays look mostly good? (70%+ tracked IDs, smooth motion)
   YES → Safe to process entire batch
   NO → Fix the problem in 1 cell first, test again
```

### After Getting Weird Metrics

```
1. Note which cell has bad metrics
   ↓
2. Generate overlays for THAT cell
   ↓
3. Look through all frames systematically
   ↓
4. Find frames where tracking looks bad
   ↓
5. Investigate ROOT CAUSE:
   - Check registration (SEM image jumping?)
   - Check segmentation (mask problems?)
   - Check detection (organelles visible?)
   ↓
6. Fix the root cause
   ↓
7. Re-generate overlays to verify fix
   ↓
8. Re-run metrics for that cell
```

---

## Advanced: Quality Metrics

Check if tracking quality is acceptable:

```python
# Analyze tracking quality
import pandas as pd

def check_tracking_quality(csv_path, min_track_length=5):
    df = pd.read_csv(csv_path)
    
    # Group by track ID
    tracks = df.groupby('TRACK_ID')
    
    # Check for problematic patterns
    issues = []
    
    for track_id, group in tracks:
        frames = sorted(group['FRAME'].unique())
        
        # Check for gaps in tracking
        gaps = []
        for i in range(len(frames) - 1):
            if frames[i+1] - frames[i] > 1:
                gaps.append((frames[i], frames[i+1]))
        
        if len(frames) < min_track_length:
            issues.append(f"Track {track_id}: Too short ({len(frames)} frames)")
        
        if gaps:
            issues.append(f"Track {track_id}: Has gaps {gaps}")
    
    if issues:
        print("⚠️ Potential tracking issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        return False
    else:
        print("✅ Tracking quality looks good!")
        return True

# Use it:
check_tracking_quality("Sperm 14/Mito tracking/tracking.csv")
```

---

## Key Takeaway

**Tracking overlays are your detective tool for metrics problems.** Before assuming metrics code is broken, generate overlays and look with your own eyes. 90% of the time, the solution is obvious from the images:

- ✅ **Overlays look great?** → Problem is elsewhere (check segmentation, masks, threshold)
- ❌ **Overlays look bad?** → Fix the root cause (registration, detection, segmentation)
- Then re-run metrics with confidence

When in doubt, **visualize first, debug second.**

---

## Visual Examples

### ✅ GOOD TRACKING: Consistent Across Frames

```
Frame 13:  Track IDs: 5, 19, 21, 23, 24, 25, 26, 27 (8 organelles)
Frame 14:  Track IDs: 1, 5, 19, 21, 23, 24, 25, 26, 27, 28 (10 organelles) ← 2 new entered
Frame 15:  Track IDs: 1, 5, 19, 21, 22, 23, 24, 25, 27 (9 organelles) ← 1 exited, tracking stable
Frame 16:  Track IDs: 1, 5, 19, 21, 22, 23, 24, 25, 27, 29 (10 organelles) ← 1 new entered
```

**Analysis**:
- ✅ IDs stay the same (track 5 is track 5 throughout)
- ✅ New IDs appear naturally (new organelles enter field)
- ✅ Population is stable
- ✅ Smooth transitions between frames

**Conclusion**: **SAFE TO USE FOR METRICS**

---

### 🚨 BAD TRACKING 1: ID Jumps

```
Frame 10:  Track IDs: 5, 19, 21, 23, 24, 25 (6 organelles)
Frame 11:  Track IDs: 3, 7, 12, 18, 29, 35 (6 organelles) ← COMPLETELY DIFFERENT IDs!
Frame 12:  Track IDs: 4, 8, 14, 20, 30, 36 (6 organelles) ← Again, different IDs!
Frame 13:  Track IDs: 6, 9, 15, 22, 31, 37 (6 organelles) ← Still different!
```

**Analysis**:
- ❌ Same number of organelles detected
- ❌ But IDs completely change between frames
- ❌ No continuity in tracking

**Conclusion**: **DO NOT USE FOR METRICS - Fix Registration**

---

### 🚨 BAD TRACKING 2: Missing Detections

```
Frame 20:  Track IDs: 1, 5, 19, 21, 23, 24, 25, 27 (8 organelles)
Frame 21:  (no IDs shown) - 8 white circles but no red circles!
Frame 22:  Track IDs: 1, 5, 19, 21, 23, 24, 25, 27 (8 organelles)
Frame 23:  (no IDs shown) - same problem
```

**Analysis**:
- ❌ Organelles are detected (white circles present)
- ❌ But tracking IDs are missing entirely in some frames
- ❌ Metrics computed from this will have gaps

**Conclusion**: **DO NOT USE FOR METRICS - Fix Segmentation or CSV**

---

### 🚨 BAD TRACKING 3: Erratic Motion

```
Frame 30:  Track 5 at position (150, 200) ← marked with red circle
Frame 31:  Track 5 at position (155, 205) ← normal motion, nearby
Frame 32:  Track 5 at position (700, 50)  ← JUMPED FAR AWAY!
Frame 33:  Track 5 at position (160, 210) ← Back to normal area
```

**Analysis**:
- ❌ Same organelle (track 5) suddenly jumps away
- ❌ Suggests registration artifact (SEM image shifted)
- ❌ Position jumps are not biological reality

**Conclusion**: **DO NOT USE FOR METRICS - Re-register Images**

---

## CSV Format Reference

The pipeline processes TrackMate CSV files in specific formats. **For complete details on CSV format, structure, and validation, see [TRACKMATE_CSV_FORMAT.md](TRACKMATE_CSV_FORMAT.md).**

Quick summary:
- **Input**: Wide format with block separators (TrackMate raw export)
- **Processing**: Remove separators → reorganize blocks → convert to long format
- **Output**: Long format with columns: Frame, Track, X, Y, Flag
- **1-indexed**: Frame numbering starts from 1 (convert to 0-indexed for Python arrays)
- **Validation**: Check CSV exists, columns correct, coordinate ranges valid

---
