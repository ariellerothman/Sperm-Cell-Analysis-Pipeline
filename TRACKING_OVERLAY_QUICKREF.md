# Tracking Overlays: Quick Reference

## Problem Detection

**Bad metrics?** → Check overlays before debugging code.

```python
from src.tracking import visualize_tracking

visualize_tracking(
    tiff_path="Sperm 14/mitochondria_stack_14_registration.tif",
    csv_path="Sperm 14/Mito tracking/tracking.csv",
    save_overlays=True
)
# Opens: Sperm 14/Mito tracking/tracking_overlays/mitochondria_overlays/
```

---

## What to Look For (One Page)

| Good ✅ | Bad 🚨 |
|---------|--------|
| Red circles with IDs in most frames | Many white circles, few/no red circles |
| Same ID across frames (track #5 = #5) | IDs suddenly change or disappear |
| Smooth motion | Circles jump erratically |
| Constant ~population | Population varies wildly |

---

## Common Issues & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Few/no track IDs | Detection failed | Check segmentation mask in ImageJ |
| Circles jumping | Registration artifact | Re-run stackreg with different params |
| ID keeps changing | Linking failed | Increase `max_linking_distance` in config |
| Blank frames | Bad image quality | Check original TIFF |

---

## Decision Tree

```
Bad metrics?
    ↓
Generate overlays
    ↓
Do overlays show consistent track IDs?
    ├→ YES: Problem is elsewhere (mask, threshold, registration)
    └→ NO: Fix tracking issue (detection, linking, SEM registration)
    ↓
Re-run metrics
```

---

## File Locations

```
Sperm 14/
├── Mito tracking/
│   └── tracking_overlays/mitochondria_overlays/frame_XXX_overlay.png
└── MO tracking/
    └── tracking_overlays/MO_overlays/frame_XXX_overlay.png
```

---

## Key Principle

**90% of wrong metrics = tracking problem, not code bug.**

Check overlays first. Saves hours of debugging.

---

**For details**: [TRACKING_OVERLAY_GUIDE.md](TRACKING_OVERLAY_GUIDE.md)
