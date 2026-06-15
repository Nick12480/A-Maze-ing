*This project has been created as part of the 42 curriculum by mverzilo, mimeyer.*

---

# A-Maze-ing

> A terminal-based maze generator and solver — built for the 42 curriculum.

---

## Description

**A-Maze-ing** is a Python command-line application that procedurally generates perfect and imperfect mazes in the terminal. Mazes are carved using classic graph algorithms and rendered in-place with ANSI escape codes, including a live step-by-step animation of the generation process.

### Goal

The project demonstrates multiple maze-generation algorithms, a clean separation between generation logic and rendering, and a reusable algorithm package that can be imported into other projects.

### Key Features

- Three interchangeable generation algorithms: **Sidewinder**, **Kruskal**, and **DFS**
- Live ANSI animation with configurable step delay
- Four switchable colour palettes
- Perfect (tree) and imperfect (looped) maze modes
- Built-in BFS solver that highlights the shortest path
- Hidden **"42" digit pattern** embedded as blocked cells in larger mazes
- Interactive terminal menu (regenerate, toggle path, cycle colours)
- Text output file with wall encoding and solution directions

---

## Instructions

### Requirements

- Python **3.9** or later
- No external runtime dependencies (stdlib only)
- Optional dev dependency: `flake8 >= 7.0`

### Installation

```bash
git clone <repo-url>
cd A-Maze-ing
pip install -e .            # editable install (optional)
```

### Running the maze

```bash
# One-shot render (no animation)
python3 -m A_Maze_ing.a_maze_ing config.txt

# With live generation animation
python3 -m A_Maze_ing.a_maze_ing config.txt          # ANIMATE=true in config

# Interactive menu
python3 -m A_Maze_ing.a_maze_ing config.txt --interactive
```

The program reads its settings from a plain-text config file (see [Configuration](#configuration)) and writes the solved maze to the path set by `OUTPUT_FILE`.

---

## Configuration

The config file uses simple `KEY=VALUE` pairs. Lines beginning with `#` are treated as comments.

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `WIDTH` | integer ≥ 2 | ✅ | — | Number of maze columns |
| `HEIGHT` | integer ≥ 2 | ✅ | — | Number of maze rows |
| `ENTRY` | `x,y` | ✅ | — | Start cell (0-indexed) |
| `EXIT` | `x,y` | ✅ | — | End cell (0-indexed) |
| `ALGORITHM` | string | ❌ | `sidewinder` | `sidewinder`, `kruskal`, or `dfs` |
| `SEED` | integer ≥ 0 | ❌ | random | RNG seed for reproducibility |
| `WEIGHT` | integer 1–10 | ❌ | `1` | Sidewinder run-closing probability (1 = short runs) |
| `ANIMATE` | bool | ❌ | `true` | Show step-by-step ANSI animation |
| `PERFECT` | bool | ❌ | `false` | If `false`, extra loops are added |
| `OUTPUT_FILE` | string | ❌ | `output_maze.txt` | Path for the text output |

**Accepted boolean values:** `true / false`, `1 / 0`, `yes / no`, `on / off`

### Example `config.txt`

```
WIDTH=5
HEIGHT=5
WEIGHT=5
SEED=1848570372
ANIMATE=true
ENTRY=1,0
EXIT=4,4
OUTPUT_FILE=output_maze.txt
PERFECT=true
ALGORITHM=kruskal
```

### Output file format

```
<hex wall-bits per row, one row per line>
                          ← blank separator line
<entry_x>,<entry_y>
<exit_x>,<exit_y>
<solution directions as N/E/S/W string>
```

Wall bits follow the convention `N=1, E=2, S=4, W=8` (additive).

---

## Maze Generation Algorithms

### Sidewinder (`sidewinder`)

Sidewinder processes the grid row by row. For each cell it either extends the current run eastward or closes the run by carving a passage north from a randomly chosen run member. This produces mazes with a slight horizontal bias. After the initial pass a disjoint-set repair phase reconnects any components that were split by the optional "42" obstacle pattern.

**Why we chose it as the default:** Sidewinder is deterministic row by row, which made it an ideal starting point for building and debugging the shared `Algorithm` base class. Its `WEIGHT` parameter also gives users an easy knob for tuning the visual style of the maze without changing the algorithm.

### Kruskal (`kruskal`)

Randomized Kruskal shuffles all internal grid edges and then greedily adds each edge if it connects two previously disconnected components (tracked with a disjoint-set / union–find structure). This guarantees a uniform spanning tree with no directional bias.

### DFS (`dfs`)

Randomized depth-first search uses a stack and visits cells recursively, backtracking whenever it reaches a dead end. It tends to produce mazes with long winding corridors and fewer short branches, giving a very different visual character from the other two algorithms.

---

## Reusable Components

### `algorithm/` package

The `algorithm/` sub-package is fully self-contained and can be imported into any Python project:

```python
from algorithm import Dfs, Kruskal, Sidewinder

config = {
    "WIDTH": 20, "HEIGHT": 15,
    "ENTRY": (0, 0), "EXIT": (19, 14),
    "SEED": 42, "PERFECT": True,
    "OUTPUT_FILE": "",
}
algo = Dfs(config)
algo.run()
print(algo.path_directions())   # e.g. "EESSWN..."
```

Key public surface:

| Symbol | Purpose |
|--------|---------|
| `Algorithm` (ABC) | Base class; override `generate()` to add new algorithms |
| `GenerationStep` | Dataclass yielded by each algorithm step |
| `LogicError` | Raised when generation produces an invalid state |
| `Dfs`, `Kruskal`, `Sidewinder` | Ready-to-use algorithm classes |

Adding a new algorithm requires only subclassing `Algorithm` and registering it in `maze.py`.

### `A_Maze_ing/animate.py` — `AnsiAnimator`

`AnsiAnimator` is decoupled from generation: it accepts any `Algorithm` instance and an iterable of `GenerationStep` objects. It can be reused for any grid-based terminal visualization.

```python
from A_Maze_ing.animate import AnsiAnimator
animator = AnsiAnimator(delay=0.05)
animator.play(algorithm, algorithm.steps())
```

---

## Team & Project Management

### Roles

| Member | Contributions |
|--------|--------------|
| **mverzilo** | Initial config parsing & validation skeleton; Sidewinder algorithm implementation; Kruskal algorithm implementation |
| **mimeyer** | Improved config parsing & validation; DFS algorithm implementation; ANSI animation layer (added during merge) |

### Planning

We started by agreeing on a shared data model (`passages` grid, `GenerationStep`, `Algorithm` ABC) so both members could work in parallel without conflicts. The initial plan was to implement one algorithm each and then integrate. During the merge we realized the project would benefit significantly from live animation, so we added `AnsiAnimator` as a third collaborative phase.

What evolved from the plan:

- The "42" pattern and the imperfect-maze loop-adding logic were not in the original scope — both were added late as enhancements.
- The interactive menu (`--interactive`) was a late addition that came out of wanting a better demo experience.

### What worked well

- The strict separation between the `algorithm/` package and the `A_Maze_ing/` rendering layer meant both members could work without blocking each other.
- The disjoint-set (`_DisjointSet`) helper written for Sidewinder was cleanly reused in Kruskal with no modification.
- Using a shared `SEED` made bugs fully reproducible during review.

### What could be improved

- Integration testing between the two packages was done manually; automated pytest coverage would have caught several late-stage issues earlier.
- The `WEIGHT` parameter currently only affects Sidewinder; a per-algorithm configuration system would be cleaner.
- The interactive menu rebuilds the entire algorithm object on each regeneration, which is slightly wasteful for large mazes.

### Tools used

- **Python 3.12** (development), target **3.9+**
- **flake8** for linting
- **Git** for version control and merging
- **AI assistance** (Claude / ChatGPT): used to catch syntax errors during development and for spelling and grammar corrections in documentation and comments — not for writing algorithmic logic

---

## Resources

### Maze generation

- [Buckblog — Maze Generation: An Overview](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap) — the canonical reference for the algorithms used here
- [Wikipedia — Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Wikipedia — Kruskal's algorithm](https://en.wikipedia.org/wiki/Kruskal%27s_algorithm)
- [Wikipedia — Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)

### Data structures

- [Wikipedia — Disjoint-set / Union–Find](https://en.wikipedia.org/wiki/Disjoint-set_data_structure) — used in both Kruskal and the Sidewinder repair phase
- [Wikipedia — Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search) — used for the BFS solver and bridge-finding

### Terminal rendering

- [ANSI escape codes reference](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [XTerm Control Sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html) — synchronized output (`?2026`) and alternate screen buffer (`?1049h`)

### AI usage

AI tools (Claude, ChatGPT) were used exclusively for:

1. **Syntax error detection** — catching typos and minor Python syntax mistakes during development
2. **Documentation corrections** — proofreading docstrings, comments, and this README for grammar and spelling

No algorithmic logic, data structures, or architectural decisions were generated by AI.
