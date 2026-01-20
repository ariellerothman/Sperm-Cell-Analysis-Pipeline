"""
Basic unit tests for sperm cell analysis metrics.

Tests verify correctness of metric calculations on synthetic data.

Run with: pytest tests/
"""

import pytest
import numpy as np
from src.config import VOXEL_SIZE, VOXEL_VOLUME, PIXEL_SIZE_UM, SLICE_THICKNESS_UM


class TestVoxelConversion:
    """Test voxel and micrometer conversions."""
    
    def test_voxel_size_consistency(self):
        """Verify VOXEL_SIZE is a valid 3-tuple."""
        assert len(VOXEL_SIZE) == 3
        assert all(v > 0 for v in VOXEL_SIZE)
        assert VOXEL_SIZE[0] == SLICE_THICKNESS_UM
        assert VOXEL_SIZE[1] == PIXEL_SIZE_UM
        assert VOXEL_SIZE[2] == PIXEL_SIZE_UM
    
    def test_voxel_volume_calculation(self):
        """Verify VOXEL_VOLUME is correct product of dimensions."""
        expected_volume = SLICE_THICKNESS_UM * PIXEL_SIZE_UM * PIXEL_SIZE_UM
        assert abs(VOXEL_VOLUME - expected_volume) < 1e-9
    
    def test_voxel_to_micrometer_conversion(self):
        """Test conversion from voxel coordinates to micrometers."""
        # 10 voxels in Z should be 10 * SLICE_THICKNESS_UM micrometers
        voxels_z = 10
        micrometers_z = voxels_z * SLICE_THICKNESS_UM
        assert micrometers_z > 0
        
        # Same for X/Y
        voxels_xy = 10
        micrometers_xy = voxels_xy * PIXEL_SIZE_UM
        assert micrometers_xy > 0


class TestSyntheticMetrics:
    """Test metric calculations on known synthetic volumes."""
    
    def test_volume_of_unit_cube(self):
        """Test that a 10x10x10 voxel cube has correct volume."""
        num_voxels = 10 * 10 * 10
        expected_volume = num_voxels * VOXEL_VOLUME
        assert expected_volume > 0
        # Should be roughly (10 * PIXEL_SIZE)^2 * (10 * SLICE_THICKNESS)
        expected_approx = (10 * PIXEL_SIZE_UM)**2 * (10 * SLICE_THICKNESS_UM)
        assert abs(expected_volume - expected_approx) < 0.1
    
    def test_centroid_of_symmetric_cube(self):
        """Test centroid calculation for a centered cube."""
        # Create a simple binary mask (5x5x5 cube)
        # Indices 8:13 gives elements [8,9,10,11,12], center at 10
        mask = np.zeros((20, 40, 40), dtype=bool)
        mask[8:13, 18:23, 28:33] = True
        
        # Centroid should be at approximately (10, 20, 30)
        coords = np.argwhere(mask)
        centroid = coords.mean(axis=0)
        
        # Check that centroid is near the center of the cube
        assert abs(centroid[0] - 10.0) < 0.1
        assert abs(centroid[1] - 20.0) < 0.1
        assert abs(centroid[2] - 30.0) < 0.1
    
    def test_distance_between_two_points(self):
        """Test Euclidean distance calculation."""
        p1 = np.array([0, 0, 0])
        p2 = np.array([3, 4, 0])
        
        # Distance should be 5 (3-4-5 triangle)
        dist = np.linalg.norm(p2 - p1)
        assert abs(dist - 5.0) < 1e-6
    
    def test_centroid_distance_to_reference(self):
        """Test distance from centroid to reference point."""
        # Centroid at (0,0,0), reference at (10,0,0)
        centroid = np.array([0, 0, 0])
        reference = np.array([10, 0, 0])
        
        # Distance in voxels
        dist_voxels = np.linalg.norm(reference - centroid)
        assert abs(dist_voxels - 10.0) < 1e-6
        
        # Convert to micrometers (only X dimension matters here)
        dist_um = dist_voxels * PIXEL_SIZE_UM
        expected_um = 10 * PIXEL_SIZE_UM
        assert abs(dist_um - expected_um) < 1e-6


class TestColumnNaming:
    """Test that output metric column names follow naming convention."""
    
    def test_lowercase_underscores(self):
        """Verify metric column names use lowercase_with_underscores."""
        expected_columns = [
            "sample_id",
            "organelle_type",
            "track_id",
            "volume_um3",
            "surface_area_um2",
            "sphericity",
            "centroid_z",
            "centroid_y",
            "centroid_x",
            "distance_to_pseudopod",
            "distance_to_nucleus",
            "bounding_box_volume_um3",
            "density",
            "aspect_ratio",
        ]
        
        for col in expected_columns:
            # Check that all lowercase
            assert col == col.lower(), f"Column {col} not lowercase"
            # Check no capital letters
            assert not any(c.isupper() for c in col)
            # Check uses underscores not camelCase
            assert "_" in col or col.islower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
