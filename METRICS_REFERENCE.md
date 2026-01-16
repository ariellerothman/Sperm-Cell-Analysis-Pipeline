# Metrics Reference

This document provides detailed definitions, formulas, and biological significance for all metrics computed by the pipeline.

## Volume
**Definition**: Total voxel count × voxel volume

**Formula**:
```
Volume (µm³) = Number_of_Voxels × (PIXEL_SIZE_UM² × SLICE_THICKNESS_UM)
```

**Biological significance**: Indicates organelle size and metabolic capacity.

## Surface Area
**Definition**: Computed via marching cubes algorithm, then mesh surface area calculation.

**Biological significance**: Combined with volume (see SA:V ratio below), indicates surface-to-volume efficiency.

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

**Range**: 0 to 1
- 1.0 = Perfect sphere
- 0.5 = Rod-like structure
- Values < 0.5 = Highly elongated or irregular

**Biological significance**: Abnormally shaped mitochondria (low sphericity) indicate fusion events or incomplete fission.

**Reference**: Hammerquist et al. (2021). Mitochondrial morphology as indicator of metabolic state.

## Surface Area-to-Volume Ratio (SA:V)
**Definition**: Surface area divided by volume.

**Biological significance**: Indicates capacity for molecular exchange with environment:
- **High SA:V**: Greater surface for nutrient uptake and waste removal → increased metabolic efficiency
- **Low SA:V**: Less surface area → potentially reduced metabolic efficiency

**Interpretation**: Spherical mitochondria have higher SA:V than elongated ones with same volume.

## Aspect Ratio
**Definition**: Ratio of longest to shortest dimension in bounding box.

**Formula**:
```
Aspect_Ratio = max(depth, width, height) / min(depth, width, height)
```

**Range**: ≥ 1.0
- 1.0 = Cube (equal dimensions)
- > 2.0 = Highly elongated structure
- Very high (>10) = Rod or tubular structure

**Biological significance**: Indicates mitochondrial shape changes:
- High aspect ratio (>3): Tubular, networked mitochondria
- Low aspect ratio (≈1): Fragmented, round mitochondria (indicates fission)

## Density
**Definition**: Ratio of object volume to bounding box volume.

**Formula**:
```
Density = Organelle_Volume / BoundingBox_Volume
```

**Range**: 0 to 1
- 1.0 = Object perfectly fills bounding box (compact)
- 0.5 = Object fills 50% of bounding box (loose/sparse)

**Biological significance**: Indicates structural compactness and presence of internal voids.

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
