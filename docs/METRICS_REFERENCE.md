# Metrics Reference

This document provides detailed definitions, formulas, and biological significance for all metrics computed by the pipeline.

## Volume
**Definition**: Total voxel count × voxel volume

**Formula**:
```
Volume (µm³) = Number_of_Voxels × (PIXEL_SIZE_UM² × SLICE_THICKNESS_UM²)
```

**Biological significance**: Indicates organelle size.

## Surface Area
**Definition**: Computed via marching cubes algorithm, then mesh surface area calculation.

## Sphericity
**Definition**: Measure of how close an object is to a perfect sphere.

**Formula**:
```
Sphericity = (π^(1/3) × (6V)^(2/3)) / A

Where:
  V = Volume (µm³)
  A = Surface Area (µm²)
  π^(1/3) ≈ 1.612
```

**Biological significance**: Abnormally shaped mitochondria (low sphericity) indicate fusion or fission events.

## Aspect Ratio
**Definition**: Ratio of longest to shortest dimension in bounding box.

**Formula**:
```
Aspect_Ratio = max(depth, width, height) / min(depth, width, height)
```

**Biological significance**: Indicates mitochondrial shape:
- High aspect ratio: Tubular, networked mitochondria
- Low aspect ratio: Round mitochondria 

## Direction Vector (Pseudopod Only)
**Definition**: Principal component from PCA analysis of pseudopod voxel coordinates.

**Method**:
1. Extract all voxels in pseudopod 3D binary mask
2. Apply PCA to compute principal axes
3. First principal component = elongation direction

**Biological significance**: Indicates pseudopod orientation in 3D space:
- Used to calculate angle toward spermathecal valve
- Reveals if sperm is "aimed" toward fertilization site
- 0° = pseudopod pointing directly at valve (favorable)
- 180° = pseudopod pointing away (unfavorable)

## Distances to Reference Structures
**Definition**: Euclidean distance between organelle centroid and reference point.

**Calculation**:
```
Distance = √[(x₁-x₂)² + (y₁-y₂)² + (z₁-z₂)²] × VOXEL_SIZE
```

**Reference points**:
- **Nucleus centroid**: Center of nucleus organelle
- **Pseudopod centroid**: Center of pseudopod structure
- **Spermathecal valve**: User-defined reference point (spermathecal valve center in global image space)
