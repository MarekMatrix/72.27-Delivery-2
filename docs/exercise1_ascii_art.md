# Ejercicio 1 — ASCII Art via GA (conceptual only, no implementation required)

Reference: http://www.nicassio.it/daniele/AsciiArtGenetic/

Answer these directly — this is a design discussion, not code:

- Representation: what is an individual? What is a gene (one character
  at one grid cell? the whole NxN grid)?
- Fitness: how do you compare a candidate ASCII grid against the target
  image? (per-cell brightness/coverage of the character glyph vs. the
  corresponding image region?)
- Crossover: what would a sensible crossover look like for a 2D grid
  genome, as opposed to the 1D triangle-list genome in Ejercicio 2?
- Mutation: single-character swap vs. region swap?
- How does this problem differ from Ejercicio 2 in search-space size and
  in how "smooth" the fitness landscape is (does changing one character
  change fitness a little or a lot)?

Write the actual answers in `docs/report`, in your own words.
