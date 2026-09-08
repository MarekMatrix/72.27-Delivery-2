"""Rasterize an Individual (list of translucent triangles) onto a canvas.

This is the bridge between the genome (individual.py) and pixel space
(image_io.py) that fitness.py needs to compare against the target.
"""

from __future__ import annotations

import numpy as np

from ga_triangles.individual import Individual
import pygame

def render(individual: Individual, width: int, height: int,
           background: tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """Draw all triangles of `individual`, in order, onto a blank canvas.

    Later triangles are painted on top of earlier ones; alpha-blend each
    triangle with what's already on the canvas.

    Returns:
        np.ndarray of shape (height, width, 3), dtype uint8.
    """
    canvas = pygame.Surface((width, height))
    canvas.fill(background)

    for triangle in individual.triangles:
        pixel_colors = tuple(round(channel * 255) for channel in triangle.color)
        pixel_vertices = [(round(x*(width-1)), round(y*(height-1))) for x, y in triangle.vertices]

        xs = [x for x, _ in pixel_vertices]
        ys = [y for _, y in pixel_vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Work on the triangle's bounding box, not the whole canvas -- much
        # cheaper when the triangles are small.
        bbox_width = max_x - min_x + 1
        bbox_height = max_y - min_y + 1

        layer = pygame.Surface((bbox_width, bbox_height), pygame.SRCALPHA)
        layer.fill((0, 0, 0, 0))
        local_vertices = [(x - min_x, y - min_y) for x, y in pixel_vertices]
        pygame.draw.polygon(layer, pixel_colors, local_vertices)
        canvas.blit(layer, (min_x, min_y))

    image = np.array(pygame.surfarray.array3d(canvas)).transpose(1, 0, 2)
    return image

def display_image(image: np.ndarray) -> None:
    """Display an RGB image in a window until the user closes it."""
    pygame.init()
    pygame.display.set_caption("Rendered Image")
    height, width, _ = image.shape
    screen = pygame.display.set_mode((width, height))
    pygame.surfarray.blit_array(screen, image.transpose(1,0,2))
    pygame.display.flip()
    while True: 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
