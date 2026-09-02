"""Rasterize an Individual (list of translucent triangles) onto a canvas.

Owner: whoever picks up "image I/O & rendering".
This is the bridge between the genome (individual.py) and pixel space
(image_io.py) that fitness.py needs to compare against the target.
"""

from __future__ import annotations

import numpy as np

from ga_triangles.individual import Individual
import pygame

#Triangle = dict(vertices=[(x0, y0), (x1, y1), (x2, y2)],color=(r,g,b,a))
#Could probably print best individual from all generations to see how it looks like.
def render(individual: Individual, width: int, height: int,
           background: tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """Draw all triangles of `individual`, in order, onto a blank canvas.

    Later triangles are painted on top of earlier ones; alpha-blend each
    triangle with what's already on the canvas.

    Returns:
        np.ndarray of shape (height, width, 3), dtype uint8.
    """
    pygame.init()
    canvas = pygame.Surface((width, height))
    canvas.fill(background)
    
    for triangle in individual.triangles:
        pixel_colors = tuple(round(channel * 255) for channel in triangle.color)
        pixel_vertices = [(round(x*(width-1)), round(y*(height-1))) for x, y in triangle.vertices]
        layer = pygame.Surface((width, height), pygame.SRCALPHA)
        layer.fill((0, 0, 0, 0))
        pygame.draw.polygon(layer, pixel_colors, pixel_vertices)
        canvas.blit(layer, (0,0))
        
    image = np.array(pygame.surfarray.array3d(canvas)).transpose(1, 0, 2)
    pygame.quit()
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
    """
    # TODO:
    # 1. start from a blank canvas (see image_io.blank_canvas)
    # 2. for each triangle: rasterize it (e.g. matplotlib.path / PIL.ImageDraw
    #    / your own scanline fill) and alpha-composite its RGBA color onto
    #    the canvas region it covers
    # 3. return the final RGB canvas
    raise NotImplementedError
"""