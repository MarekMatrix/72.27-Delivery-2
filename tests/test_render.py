"""Tests for ga_triangles.render. Owner: image I/O & rendering."""

from ga_triangles.render import render
from ga_triangles.individual import Individual, Triangle

def test_render_output_shape_matches_canvas_size():
    
    Triangle1 = Triangle(vertices=[(0, 0), (1, 0), (0.5, 1)], color=(255, 0, 0, 128))
    Triangle2 = Triangle(vertices=[(0.5, 0), (1, 0), (0.75, 1)], color=(0, 255, 0, 128))
    individual = Individual(triangles=[Triangle1, Triangle2])

    rendered_image = render(individual, width=400, height=400)
    # TODO: render(individual, w, h).shape == (h, w, 3)


def test_empty_triangle_list_returns_background_color():
    individual = Individual(triangles=[])
    
    rendered_image = render(individual, width=400, height=400)
    # TODO: an individual with 0 triangles renders as a flat background canvas
    
test_render_output_shape_matches_canvas_size()
test_empty_triangle_list_returns_background_color()
