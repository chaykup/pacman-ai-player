# Pacman AI Agent Demo

A classic Pacman game implemented in Python with Pygame, featuring AI agents that use different pathfinding algorithms to play the game automatically.

![Pacman Game](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)

## Features

- **Classic Pacman Gameplay**: Navigate mazes, collect pellets, avoid ghosts, and eat power pellets to turn the tables
- **Three Play Modes**:
  - **Player Mode**: Control Pacman with arrow keys
  - **A\* Mode**: AI that prioritizes avoiding ghosts and survival
  - **BFS Mode**: AI that prioritizes collecting pellets efficiently

## Requirements

- Python 3.7 or higher
- Pygame

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pacman-ai-player.git
   cd pacman-ai-player
   ```

2. Install dependencies:
   ```bash
   pip install pygame
   ```

## How to Run

```bash
python run.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move Pacman (in Player mode) |
| Enter | Start the game |
| Space | Pause/Unpause |

## Game Modes

Select a mode by clicking one of the three buttons at the bottom of the screen:

### Player Mode
Control Pacman manually using the arrow keys. Classic arcade gameplay!

### A* Mode (Ghost Avoidance)
The AI uses the A* pathfinding algorithm with ghost penalties. It will:
- Actively avoid paths near ghosts
- Take longer routes if they're safer
- Prioritize power pellets when threatened
- Chase frightened ghosts for bonus points

### BFS Mode (High Score)
The AI uses Breadth-First Search to find the shortest path to pellets. It will:
- Always take the shortest path to the nearest pellet
- Efficiently clear the maze
- Not consider ghost positions (lives dangerously!)

## Project Structure

```
pacman-ai/
├── run.py              # Main game loop and UI
├── pacman.py           # Pacman entity and controls
├── ghosts.py           # Ghost entities and behaviors
├── ai_agent.py         # AI pathfinding algorithms (A*, BFS)
├── nodes.py            # Maze node graph structure
├── pellets.py          # Pellet entities
├── constants.py        # Game constants and settings
├── entity.py           # Base entity class
├── vector.py           # 2D vector math
├── sprites.py          # Sprite handling
├── text.py             # Text rendering
├── animation.py        # Animation utilities
├── modes.py            # Ghost mode management
├── pauser.py           # Pause functionality
├── mazedata.py         # Maze configuration
├── fruit.py            # Bonus fruit
├── maze1.txt           # Level 1 layout
├── maze2.txt           # Level 2 layout
└── *.png               # Sprite sheets
```

## How the AI Works

### A* Algorithm
A* finds the optimal path by combining:
- **g(n)**: Actual cost from start to current node
- **h(n)**: Estimated cost from current node to goal (Manhattan distance)
- **Ghost penalties**: Heavy costs added for nodes near ghosts

This makes the AI prefer safer routes even if they're longer.

### BFS Algorithm
Breadth-First Search explores all neighbors at the current depth before moving deeper. This guarantees finding the shortest path (by number of steps) to the nearest pellet, but doesn't account for dangers along the way.

## License

This project is for educational purposes.

## Acknowledgments

- Original Pacman game by Namco
- Pygame community for the excellent game library