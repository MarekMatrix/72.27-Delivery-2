"""Target image loading and canvas <-> array conversions.

Owner: whoever picks up "image I/O & rendering".
External image libraries (Pillow, numpy) ARE allowed for this module --
the TP only forbids external libs for the GA itself.
"""

from __future__ import annotations

import numpy as np


def load_target_image(path: str, size: tuple[int, int] | None = None) -> np.ndarray:
    """Load an image from disk as an RGB(A) array, optionally resized.

    Args:
        path: filesystem path to the source image.
        size: optional (width, height) to resize to. If None, keep original.

    Returns:
        np.ndarray of shape (H, W, 3) or (H, W, 4), dtype uint8.
    """
    # TODO: open with Pillow, convert to RGB or RGBA, resize if requested,
    # return as a numpy array.
    raise NotImplementedError


def save_image(array: np.ndarray, path: str) -> None:
    """Save an RGB(A) uint8 array to disk.

    # TODO: convert array back to a Pillow Image and write to `path`.
    """
    raise NotImplementedError


def blank_canvas(width: int, height: int, background: tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """Create a blank RGB canvas of the given size filled with `background`.

    # TODO: allocate a (height, width, 3) uint8 array filled with `background`.
    """
    raise NotImplementedError
