"""Tests for ga_triangles.fitness. Owner: representation & fitness."""
from ga_triangles.fitness import pixel_error
import numpy as np

def test_identical_images_have_zero_error():
    img = np.array([[[10, 200, 30], [255, 0, 128]]], dtype=np.uint8)
    assert pixel_error(img, img) == 0.0


def test_fitness_is_monotonic_in_error():
    # TODO: lower error must never produce lower fitness
    pass
