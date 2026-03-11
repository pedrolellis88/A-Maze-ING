*This project has been created as part of the 42 curriculum by *pdiniz-l*, *mabarret*

# A-Maze-ing

![Maze rendering](maze_example.png)

## Description

**A-Maze-ing** is a Python project that generates mazes from a configuration file, exports them using a hexadecimal wall representation, and provides a visual representation of the generated maze.

The program reads a configuration file defining maze parameters (size, entry/exit coordinates, output file, and generation options), generates a valid maze, and writes it to an output file. Each maze cell is encoded using a hexadecimal value that represents the presence of walls on its four sides.

The project also includes a reusable maze generation module that can be packaged and installed as a Python package (`mazegen-*`). This allows the maze generation logic to be reused in future projects.

Key objectives of the project include:

- Generate valid mazes with configurable parameters
- Support reproducibility through deterministic random seeds
- Encode maze structure using hexadecimal wall representation
- Provide visual rendering of the maze
- Structure the maze generator as a reusable Python module
- Follow Python best practices (type hints, linting, packaging)

---

# Instructions

## Requirements

The project requires:

- Python **3.10 or later**
- flake8
- mypy
- Python build tools

Dependencies are listed in:

```
requirements.txt
```

---

## Installation

Create the virtual environment and install dependencies:

```bash
make install
```

This command installs all required dependencies for the project.

---

## Run the program

The program must be executed using:

```bash
python3 a_maze_ing.py config.txt
```

Where:

- `a_maze_ing.py` is the main program file
- `config.txt` is the configuration file defining the maze parameters

Example using the default configuration:

```bash
make run
```

---

## Debug mode

To run the program with Python's debugger:

```bash
make debug
```

---

## Linting and type checking

To verify code quality and type correctness:

```bash
make lint
```

This runs:

```bash
flake8 .
mypy .
```

---

## Clean project artifacts

Remove temporary files and caches:

```bash
make clean
```

Remove additional build artifacts:

```bash
make distclean
```

---

## Build the reusable module

The maze generator can be packaged as a reusable Python module:

```bash
make build
```

The generated package will be placed inside the `dist/` directory.

---

# Configuration File Format

The maze is configured through a **plain text configuration file** containing one key-value pair per line.

Lines starting with `#` are treated as comments and ignored.

Example configuration file:

```
WIDTH=30
HEIGHT=10
ENTRY=0,0
OUTPUT_FILE=maze.txt
PERFECT=TRUE
EXIT=29,9
SEED=20
COLOR=TRUE
COLORS=WALL:WHITE,PATH:BLUE,ENTRY:GREEN,EXIT:RED,PATTERN_42:MAGENTA
```

---

## Mandatory keys

| Key | Description |
|-----|-------------|
| WIDTH | Maze width (number of cells) |
| HEIGHT | Maze height |
| ENTRY | Entry coordinates `(x,y)` |
| EXIT | Exit coordinates `(x,y)` |
| OUTPUT_FILE | Output filename |
| PERFECT | Indicates whether the maze must be perfect |

A **perfect maze** contains exactly one valid path between the entry and the exit.

---

## Optional keys

| Key | Description |
|-----|-------------|
| SEED | Allows deterministic generation of the maze (default = 0) |
| COLORS | Customizes maze colors (default = True) |

Example:

```
COLORS=WALL:WHITE,PATH:BLUE,ENTRY:GREEN,EXIT:RED,PATTERN_42:MAGENTA
```

---

# Output File Format

The generated maze is written to the output file using **one hexadecimal digit per cell**.

Each digit encodes which walls are closed.

| Bit | Direction |
|-----|-----------|
| 0 | North |
| 1 | East |
| 2 | South |
| 3 | West |

Example values:

```
3  -> 0011
A  -> 1010
```

Cells are stored row by row, with **one row per line**.

After the maze grid, the file contains:

1. Entry coordinates  
2. Exit coordinates  
3. The shortest path between them using the letters `N`, `E`, `S`, `W`

All lines end with `\n`.

---

# Maze Generation Algorithm

The project generates a random maze while ensuring that:

- Entry and exit exist and are valid
- All cells remain connected
- Neighboring cells maintain consistent walls
- Corridors never exceed the allowed width constraints
- The maze structure remains coherent and valid

When the `PERFECT` flag is enabled, the maze must contain **exactly one valid path** between entry and exit.

---

# Visual Representation

The project includes a visual representation of the maze.

The visualization was implemented using:

- ASCII rendering in the terminal

The visual representation clearly shows:

- Maze walls
- Entry point
- Exit point
- The solution path

Possible interactions include:

- Generating a new maze
- Showing or hiding the shortest path
- Changing wall colors

---

# Reusable Module

Maze generation logic is implemented in a reusable module.

The module provides a class responsible for generating mazes:

```
MazeGenerator
```

This module is packaged as a Python package located at the root of the repository and can be installed using standard Python packaging tools.

Example package output:

```
mazegen-1.0.0-py3-none-any.whl
```

This reusable module allows future projects to import and reuse the maze generation logic.

---

# Example Usage

Example usage of the generator module:

```python
from mazegen import MazeGenerator

generator = MazeGenerator(width=20, height=15)
maze = generator.generate()

solution = generator.solve()
```

The module allows:

- Instantiating a maze generator
- Passing parameters such as size or seed
- Accessing the generated maze structure
- Retrieving a valid solution path

---

# Repository Structure

Example repository structure:

```
A-Maze-ING-main
│
├── a_maze_ing.py
├── mazegen.py
├── config_default.txt
├── maze_example.png
├── requirements.txt
├── pyproject.toml
├── Makefile
│
├── src
│   ├── app.py
│   ├── model.py
│   └── render
│       ├── ascii_renderer.py
│       └── palette.py

```

---

## Main components

| File | Purpose |
|-----|--------|
| a_maze_ing.py | Main entry point of the application |
| mazegen.py | Reusable maze generator module |
| config_default.txt | Default configuration file |
| src/ | Application logic |
| Makefile | Development automation |

---

# Team and Project Management

## Roles

The project was developed by a team of two members, with the following responsibilities:

* **pdiniz-l** – Implemented the maze generator module.
* **mabarret** – Implemented the configuration system and user interaction features.

The work was divided to separate the core maze generation logic from the user-facing controls and configuration.


## Project Planning

Due to issues with the original team formations, both members initially developed separate implementations of the maze project.

When forming the final team, the contributors decided to combine their individual work and knowledge into a unified codebase.

Although developed independently at first, both implementations followed similar logic and algorithmic approaches for maze generation, which made it possible to merge and refactor the code into a consistent final project.

The final repository represents the result of integrating these implementations and improving the overall structure of the project.

## Retrospective

### What worked well

- Reusing experience from previous individual implementations

- Clear separation between generation logic and user interface

- Incremental testing during integration

- Modular structure that simplifies debugging and improvements

### What could be improved

- Earlier documentation of architectural decisions

- Better planning and tracking of development stages

- More detailed technical documentation during development

# Resources

Classic references on maze generation and graph algorithms:

- https://en.wikipedia.org/wiki/Maze_generation_algorithm
- https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking
- Graph theory resources on spanning trees

---

# AI Usage

AI tools were used to assist with:

- Documentation drafting
- Structuring the README
- Formatting explanations

All generated content was reviewed and validated before inclusion.
