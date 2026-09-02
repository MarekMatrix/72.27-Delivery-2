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

def render(individual: Individual, width: int, height: int,
           background: tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """Draw all triangles of `individual`, in order, onto a blank canvas.

    Later triangles are painted on top of earlier ones; alpha-blend each
    triangle with what's already on the canvas.

    Returns:
        np.ndarray of shape (height, width, 3), dtype uint8.
    """
    pygame.init()
    pygame.display.set_caption("Rendering Individual")
    screen = pygame.display.set_mode((width, height)); screen.fill(background)
    transparent_layer = pygame.Surface((width, height), pygame.SRCALPHA); transparent_layer.fill((0, 0, 0, 0))
    
    for triangle in individual.triangles:
        pygame.draw.polygon(transparent_layer, triangle.color, triangle.vertices)
    
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