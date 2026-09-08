"""Target image loading and canvas <-> array conversions."""

from __future__ import annotations

import numpy as np
import PIL.Image as Image


def load_target_image(
    path: str,
    size: tuple[int, int] | None = None,
    max_size: int | None = None,
) -> np.ndarray:
    """Load an image from disk as an RGB(A) array, optionally resized.

    Args:
        path: filesystem path to the source image.
        size: optional exact (width, height) to resize to. If None, keep original.
        max_size: optional cap on the longer side, preserving aspect ratio.
            Ignored if `size` is given. Only ever downscales, never upscales.

    Returns:
        np.ndarray of shape (H, W, 3) dtype uint8.
    """

    image = Image.open(path).convert("RGB")

    if size is not None:
        image = image.resize(size, resample=Image.Resampling.LANCZOS)
    elif max_size is not None:
        scale = max_size / max(image.width, image.height)
        if scale < 1:
            new_size = (round(image.width * scale), round(image.height * scale))
            image = image.resize(new_size, resample=Image.Resampling.LANCZOS)

    array = np.array(image)

    return array


def save_image(array: np.ndarray, path: str) -> None:
    """Save an RGB(A) uint8 array to disk.
    """
    if array.dtype != np.uint8:
        raise TypeError("array must be uint8")
    image = Image.fromarray(array)
    image.save(path)


def blank_canvas(width: int = 720, height: int = 720, background: tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """Create a blank RGB canvas of the given size filled with `background`.

    # TODO: allocate a (height, width, 3) uint8 array filled with `background`.
    """
    raise NotImplementedError


def split_into_chunks(
    image: np.ndarray, chunk_size: int
) -> list[tuple[np.ndarray, tuple[int, int]]]:
    """Split `image` into a grid of chunks at most chunk_size x chunk_size.

    Returns (chunk_array, (row_offset, col_offset)) pairs, offset being the
    chunk's top-left position in `image`, in pixels. Edge chunks along the
    bottom/right may be smaller than chunk_size if the image doesn't divide
    evenly.
    """
    height, width = image.shape[:2]
    chunks: list[tuple[np.ndarray, tuple[int, int]]] = []

    for row_offset in range(0, height, chunk_size):
        for col_offset in range(0, width, chunk_size):
            chunk = image[
                row_offset : row_offset + chunk_size,
                col_offset : col_offset + chunk_size,
            ]
            chunks.append((chunk, (row_offset, col_offset)))

    return chunks


def recombine_chunks(
    chunks: list[tuple[np.ndarray, tuple[int, int]]],
    full_shape: tuple[int, int],
) -> np.ndarray:
    """Paste rendered chunk images back into their original positions.

    Args:
        chunks: (chunk_image, (row_offset, col_offset)) pairs -- same offsets
            split_into_chunks produced, but each chunk_image is now that
            chunk's rendered GA approximation, not the original pixels.
        full_shape: (height, width) of the un-chunked target image.
    """
    height, width = full_shape
    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    for chunk_image, (row_offset, col_offset) in chunks:
        h, w = chunk_image.shape[:2]
        canvas[row_offset : row_offset + h, col_offset : col_offset + w] = chunk_image

    return canvas
