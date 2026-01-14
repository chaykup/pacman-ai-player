"""
AI Agent module for Pacman game.
Implements three AI strategies:
- A*: Prioritizes avoiding ghosts while collecting pellets (survival focused)
- BFS: Prioritizes getting the highest score (greedy pellet collection)
- DFS: Finds shortest path to single pellet (board contains only one pellet)
"""

from collections import deque
import heapq
from constants import *
from vector import Vector2


class AIAgent:
    """Base class for AI agents that control Pacman."""
    
    DIRECTION_ORDER = [UP, LEFT, DOWN, RIGHT]
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        self.pacman = pacman
        self.nodes = nodes
        self.pellets = pellets
        self.ghosts = ghosts
        self.current_path = []
        self.current_goal = None
        self.last_node = None
    
    def get_node_key(self, node):
        """Get unique key for a node based on its position."""
        return (int(node.position.x), int(node.position.y))
    
    def get_neighbors(self, node):
        """Get all valid neighboring nodes in consistent order."""
        neighbors = []
        for direction in self.DIRECTION_ORDER:
            neighbor = node.neighbors.get(direction)
            if neighbor is not None:
                if PACMAN in node.access.get(direction, []):
                    neighbors.append((neighbor, direction))
        return neighbors
    
    def reconstruct_path(self, came_from, start_key, goal_key):
        """Reconstruct path from came_from dictionary."""
        if goal_key == start_key:
            return []
        
        path = []
        current = goal_key
        
        while current in came_from:
            parent, direction = came_from[current]
            path.append(direction)
            if parent == start_key:
                break
            current = parent
        
        path.reverse()
        return path
    
    def should_replan(self, current_node):
        """Determine if we need to replan the path."""
        # No path - need to plan
        if not self.current_path:
            return True
        
        # If we have a specific goal, check if it still exists
        if self.current_goal is not None:
            goal_exists = False
            for pellet in self.pellets.pelletList:
                if (int(pellet.position.x), int(pellet.position.y)) == self.current_goal:
                    goal_exists = True
                    break
            if not goal_exists:
                return True
        
        # Check if we've moved to a new node
        current_key = self.get_node_key(current_node)
        if current_key != self.last_node:
            self.last_node = current_key
            # We've reached a new node, consume the direction we just used
            if len(self.current_path) > 1:
                self.current_path.pop(0)
            else:
                # Path exhausted after this move - replan for next destination
                self.current_path = []
                return True
        
        return False
    
    def is_at_goal(self, node, target_position):
        """Check if node is close enough to target."""
        dist_sq = (node.position - target_position).magnitudeSquared()
        return dist_sq < (TILEWIDTH * 1.5) ** 2
    
    def get_current_node(self):
        """Get Pacman's current effective node for pathfinding."""
        current_node = self.pacman.node
        if self.pacman.target and self.pacman.target != self.pacman.node:
            current_node = self.pacman.target
        return current_node
    
    def get_direction(self):
        """Get the next direction for Pacman to move."""
        return STOP


class AStarAgent(AIAgent):
    """AI Agent using A* Search - SURVIVAL FOCUSED.
    
    This agent's #1 priority is avoiding ghosts at all costs.
    It will only collect pellets when it's safe to do so.
    """
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        super().__init__(pacman, nodes, pellets, ghosts)
        self.name = "A*"
        self.last_position = None
    
    def heuristic(self, node, target_pos):
        """Calculate Manhattan distance heuristic."""
        return abs(node.position.x - target_pos.x) + abs(node.position.y - target_pos.y)
    
    def get_ghost_danger(self, position):
        """Calculate how dangerous a position is based on ghost proximity.
        
        Returns a high value if any ghost is nearby, 0 if safe.
        """
        danger = 0
        for ghost in self.ghosts:
            # Only consider active ghosts (not respawning)
            if ghost.mode.current == SPAWN:
                continue
            
            dist_sq = (ghost.position - position).magnitudeSquared()
            
            # Extremely high danger when very close
            if dist_sq < (2 * TILEWIDTH) ** 2:
                danger += 100000
            elif dist_sq < (4 * TILEWIDTH) ** 2:
                danger += 50000
            elif dist_sq < (6 * TILEWIDTH) ** 2:
                danger += 10000
            elif dist_sq < (8 * TILEWIDTH) ** 2:
                danger += 1000
            elif dist_sq < (10 * TILEWIDTH) ** 2:
                danger += 100
        
        return danger
    
    def find_safest_direction(self, current_node):
        """Find the direction that moves Pacman away from all ghosts."""
        best_direction = STOP
        lowest_danger = float('inf')
        
        for neighbor, direction in self.get_neighbors(current_node):
            danger = self.get_ghost_danger(neighbor.position)
            if danger < lowest_danger:
                lowest_danger = danger
                best_direction = direction
        
        return best_direction, lowest_danger
    
    def select_safest_pellet(self):
        """Select the pellet that is furthest from all ghosts."""
        if not self.pellets.pelletList:
            return None
        
        best_pellet = None
        lowest_danger = float('inf')
        
        for pellet in self.pellets.pelletList:
            danger = self.get_ghost_danger(pellet.position)
            
            # Also consider distance from Pacman (prefer closer safe pellets)
            dist_to_pacman = (pellet.position - self.pacman.position).magnitudeSquared()
            score = danger + (dist_to_pacman * 0.01)  # Small weight on distance
            
            if score < lowest_danger:
                lowest_danger = score
                best_pellet = pellet
        
        return best_pellet
    
    def find_path(self, start_node, target_position):
        """Find path using A* with ghost avoidance as the primary cost."""
        if start_node is None:
            return []
        
        start_key = self.get_node_key(start_node)
        
        if self.is_at_goal(start_node, target_position):
            return []
        
        counter = 0
        g_scores = {start_key: 0}
        open_set = [(self.heuristic(start_node, target_position), counter, start_node)]
        came_from = {}
        visited = set()
        
        while open_set:
            f_score, _, current_node = heapq.heappop(open_set)
            current_key = self.get_node_key(current_node)
            
            if current_key in visited:
                continue
            visited.add(current_key)
            
            if self.is_at_goal(current_node, target_position):
                return self.reconstruct_path(came_from, start_key, current_key)
            
            for neighbor, direction in self.get_neighbors(current_node):
                neighbor_key = self.get_node_key(neighbor)
                if neighbor_key in visited:
                    continue
                
                # Cost is primarily ghost danger, with small movement cost
                move_cost = TILEWIDTH
                ghost_danger = self.get_ghost_danger(neighbor.position)
                new_g = g_scores[current_key] + move_cost + ghost_danger
                
                if neighbor_key not in g_scores or new_g < g_scores[neighbor_key]:
                    g_scores[neighbor_key] = new_g
                    h = self.heuristic(neighbor, target_position)
                    f = new_g + h
                    counter += 1
                    came_from[neighbor_key] = (current_key, direction)
                    heapq.heappush(open_set, (f, counter, neighbor))
        
        return []
    
    def get_direction(self):
        """Get next direction - ALWAYS prioritize ghost avoidance."""
        current_node = self.get_current_node()
        if current_node is None:
            return STOP
        
        # First, check if we're in immediate danger - always react immediately
        current_danger = self.get_ghost_danger(self.pacman.position)
        
        if current_danger >= 10000:
            # In danger - find safest escape route immediately
            safe_direction, _ = self.find_safest_direction(current_node)
            self.current_path = []  # Clear path, we're in survival mode
            self.last_position = None  # Force replan after escaping
            if safe_direction != STOP:
                return safe_direction
        
        # Get current position to detect movement
        current_pos = (int(self.pacman.position.x), int(self.pacman.position.y))
        
        # Recalculate path when we reach a new position or have no path
        if current_pos != self.last_position or not self.current_path:
            self.last_position = current_pos
            
            if not self.pellets.pelletList:
                # No pellets left - just stay safe
                safe_direction, _ = self.find_safest_direction(current_node)
                return safe_direction
            
            target_pellet = self.select_safest_pellet()
            if target_pellet:
                self.current_path = self.find_path(current_node, target_pellet.position)
        
        # Return next direction from path
        if self.current_path:
            direction = self.current_path.pop(0)
            
            # Double-check this move is safe before committing
            neighbor = current_node.neighbors.get(direction)
            if neighbor:
                next_danger = self.get_ghost_danger(neighbor.position)
                if next_danger >= 10000:
                    # This move leads to danger - escape instead
                    safe_direction, _ = self.find_safest_direction(current_node)
                    self.current_path = []
                    return safe_direction
            
            return direction
        
        # Fallback - move to safest neighbor
        safe_direction, _ = self.find_safest_direction(current_node)
        return safe_direction


class BFSAgent(AIAgent):
    """AI Agent using BFS - SCORE FOCUSED.
    
    This agent's only goal is to collect as many pellets as possible.
    It completely ignores ghosts and always takes the shortest path
    to the nearest pellet.
    """
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        super().__init__(pacman, nodes, pellets, ghosts)
        self.name = "BFS"
        self.last_position = None
    
    def find_path_to_nearest_pellet(self, start_node):
        """Use BFS to find the shortest path to the nearest pellet.
        
        BFS guarantees the shortest path. We expand outward from Pacman's
        position and return immediately when we find any pellet.
        """
        if start_node is None:
            return []
        
        start_key = self.get_node_key(start_node)
        
        queue = deque()
        # Start by exploring all neighbors of the start node
        for neighbor, direction in self.get_neighbors(start_node):
            neighbor_key = self.get_node_key(neighbor)
            # Check if this neighbor has a pellet
            for pellet in self.pellets.pelletList:
                if self.is_at_goal(neighbor, pellet.position):
                    return [direction]  # One step to pellet
            queue.append((neighbor, [direction], neighbor_key))
        
        visited = {start_key}
        
        while queue:
            current_node, path, current_key = queue.popleft()
            
            if current_key in visited:
                continue
            visited.add(current_key)
            
            # Expand neighbors
            for neighbor, direction in self.get_neighbors(current_node):
                neighbor_key = self.get_node_key(neighbor)
                if neighbor_key in visited:
                    continue
                
                new_path = path + [direction]
                
                # Check if there's a pellet at this neighbor
                for pellet in self.pellets.pelletList:
                    if self.is_at_goal(neighbor, pellet.position):
                        return new_path  # Found nearest pellet!
                
                queue.append((neighbor, new_path, neighbor_key))
        
        return []
    
    def get_direction(self):
        """Get next direction - always go straight for the nearest pellet.
        
        Simple approach: recalculate path every time we're at a new node position.
        This is efficient for BFS and ensures we always have the optimal path.
        """
        if not self.pellets.pelletList:
            return STOP
        
        current_node = self.get_current_node()
        if current_node is None:
            return STOP
        
        # Get current position to detect when we've moved
        current_pos = (int(self.pacman.position.x), int(self.pacman.position.y))
        
        # Recalculate path when we reach a new position or have no path
        if current_pos != self.last_position or not self.current_path:
            self.last_position = current_pos
            self.current_path = self.find_path_to_nearest_pellet(current_node)
        
        # Return the first direction in our path
        if self.current_path:
            direction = self.current_path.pop(0)
            return direction
        
        # Fallback: if no path found, move in any valid direction
        for neighbor, direction in self.get_neighbors(current_node):
            return direction
        
        return STOP


class DFSAgent(AIAgent):
    """AI Agent using DFS mode - finds shortest path to single pellet.
    
    In DFS mode, the board contains only one pellet.
    This agent finds the shortest path to that pellet using BFS
    (which guarantees shortest path).
    """
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        super().__init__(pacman, nodes, pellets, ghosts)
        self.name = "DFS"
        self.last_position = None
    
    def find_shortest_path_to_pellet(self, start_node):
        """Use BFS to find the shortest path to the single pellet.
        
        Since DFS mode has only one pellet, we use BFS to guarantee
        the shortest path to it.
        """
        if start_node is None:
            return []
        
        if not self.pellets.pelletList:
            return []
        
        # Get the single pellet
        target_pellet = self.pellets.pelletList[0]
        target_position = target_pellet.position
        
        start_key = self.get_node_key(start_node)
        
        # Check if we're already at the goal
        if self.is_at_goal(start_node, target_position):
            return []
        
        queue = deque()
        queue.append((start_node, [], start_key))
        visited = set()
        
        while queue:
            current_node, path, current_key = queue.popleft()
            
            if current_key in visited:
                continue
            visited.add(current_key)
            
            # Check if we've reached the target
            if self.is_at_goal(current_node, target_position):
                return path
            
            # Expand neighbors
            for neighbor, direction in self.get_neighbors(current_node):
                neighbor_key = self.get_node_key(neighbor)
                if neighbor_key in visited:
                    continue
                
                new_path = path + [direction]
                queue.append((neighbor, new_path, neighbor_key))
        
        return []
    
    def get_direction(self):
        """Get next direction - find shortest path to the single pellet."""
        if not self.pellets.pelletList:
            return STOP
        
        current_node = self.get_current_node()
        if current_node is None:
            return STOP
        
        # Get current position to detect when we've moved
        current_pos = (int(self.pacman.position.x), int(self.pacman.position.y))
        
        # Recalculate path when we reach a new position or have no path
        if current_pos != self.last_position or not self.current_path:
            self.last_position = current_pos
            self.current_path = self.find_shortest_path_to_pellet(current_node)
        
        # Return the first direction in our path
        if self.current_path:
            direction = self.current_path.pop(0)
            return direction
        
        # Fallback: if no path found, move in any valid direction
        for neighbor, direction in self.get_neighbors(current_node):
            return direction
        
        return STOP


def create_agent(ai_mode, pacman, nodes, pellets, ghosts):
    """Factory function to create the appropriate AI agent."""
    if ai_mode == AI_ASTAR:
        return AStarAgent(pacman, nodes, pellets, ghosts)
    elif ai_mode == AI_BFS:
        return BFSAgent(pacman, nodes, pellets, ghosts)
    elif ai_mode == AI_DFS:
        return DFSAgent(pacman, nodes, pellets, ghosts)
    return None