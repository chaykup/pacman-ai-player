"""
AI Agent module for Pacman game.
Implements two AI strategies:
- A*: Prioritizes avoiding ghosts while collecting pellets (survival focused)
- BFS: Prioritizes getting the highest score (greedy pellet collection)
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
        
        # Replan when we reach a new node for responsiveness
        current_key = self.get_node_key(current_node)
        if current_key != self.last_node:
            self.last_node = current_key
            # Consume the first step of the path since we've moved
            if len(self.current_path) > 0:
                self.current_path.pop(0)
            # Replan if path is now empty
            if not self.current_path:
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
    """AI Agent using A* Search - prioritizes AVOIDING GHOSTS.
    
    This agent focuses on survival by heavily penalizing paths near ghosts.
    It will take longer routes to avoid danger.
    """
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        super().__init__(pacman, nodes, pellets, ghosts)
        self.name = "A*"
    
    def heuristic(self, node, target_pos):
        """Calculate Manhattan distance heuristic."""
        return abs(node.position.x - target_pos.x) + abs(node.position.y - target_pos.y)
    
    def ghost_penalty(self, node):
        """Calculate heavy penalty for being near ghosts."""
        penalty = 0
        for ghost in self.ghosts:
            if ghost.mode.current == FREIGHT:
                # Bonus for going toward frightened ghosts
                dist = (ghost.position - node.position).magnitudeSquared()
                if dist < (6 * TILEWIDTH) ** 2:
                    penalty -= 100
            elif ghost.mode.current != SPAWN:
                dist = (ghost.position - node.position).magnitudeSquared()
                if dist < (3 * TILEWIDTH) ** 2:
                    penalty += 1000  # Very heavy penalty - almost avoid at all costs
                elif dist < (5 * TILEWIDTH) ** 2:
                    penalty += 500
                elif dist < (8 * TILEWIDTH) ** 2:
                    penalty += 100
        return penalty
    
    def select_goal(self):
        """Select safest pellet to target."""
        if not self.pellets.pelletList:
            return None
        
        pacman_pos = self.pacman.position
        best_pellet = None
        best_score = float('inf')
        
        for pellet in self.pellets.pelletList:
            # Base score is distance
            dist_sq = (pellet.position - pacman_pos).magnitudeSquared()
            score = dist_sq
            
            # Heavy penalty for pellets near ghosts
            for ghost in self.ghosts:
                if ghost.mode.current != FREIGHT and ghost.mode.current != SPAWN:
                    ghost_dist = (ghost.position - pellet.position).magnitudeSquared()
                    if ghost_dist < (6 * TILEWIDTH) ** 2:
                        score += 50000  # Avoid pellets near ghosts
            
            # Power pellets are valuable when threatened
            if pellet.name == POWERPELLET:
                for ghost in self.ghosts:
                    if ghost.mode.current != FREIGHT and ghost.mode.current != SPAWN:
                        ghost_dist = (ghost.position - pacman_pos).magnitudeSquared()
                        if ghost_dist < (10 * TILEWIDTH) ** 2:
                            score -= 100000  # Strongly prefer power pellets when threatened
            
            if score < best_score:
                best_score = score
                best_pellet = pellet
        
        return best_pellet
    
    def find_path(self, start_node, target_position):
        """Find path using A* with ghost avoidance."""
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
                
                move_cost = TILEWIDTH
                ghost_cost = self.ghost_penalty(neighbor)
                new_g = g_scores[current_key] + move_cost + ghost_cost
                
                if neighbor_key not in g_scores or new_g < g_scores[neighbor_key]:
                    g_scores[neighbor_key] = new_g
                    h = self.heuristic(neighbor, target_position)
                    f = new_g + h
                    counter += 1
                    came_from[neighbor_key] = (current_key, direction)
                    heapq.heappush(open_set, (f, counter, neighbor))
        
        return []
    
    def get_direction(self):
        """Get next direction using A* with ghost avoidance."""
        if not self.pellets.pelletList:
            return STOP
        
        current_node = self.get_current_node()
        
        if self.should_replan(current_node):
            target_pellet = self.select_goal()
            if target_pellet is None:
                return STOP
            
            self.current_goal = (int(target_pellet.position.x), int(target_pellet.position.y))
            self.current_path = self.find_path(current_node, target_pellet.position)
        
        if self.current_path:
            return self.current_path[0]
        
        return STOP


class BFSAgent(AIAgent):
    """AI Agent using BFS - prioritizes HIGHEST SCORE.
    
    This agent focuses on collecting pellets efficiently to maximize score.
    It targets the highest-value pellets (power pellets > regular pellets)
    and takes the shortest path to them.
    """
    
    def __init__(self, pacman, nodes, pellets, ghosts):
        super().__init__(pacman, nodes, pellets, ghosts)
        self.name = "BFS"
    
    def select_goal(self):
        """Select highest value pellet to target.
        
        Priority:
        1. Power pellets (50 points) - always prefer these
        2. Closest regular pellet (10 points)
        """
        if not self.pellets.pelletList:
            return None
        
        pacman_pos = self.pacman.position
        
        # First, look for power pellets
        best_power_pellet = None
        best_power_dist = float('inf')
        
        # Also track closest regular pellet
        best_regular_pellet = None
        best_regular_dist = float('inf')
        
        for pellet in self.pellets.pelletList:
            dist_sq = (pellet.position - pacman_pos).magnitudeSquared()
            
            if pellet.name == POWERPELLET:
                if dist_sq < best_power_dist:
                    best_power_dist = dist_sq
                    best_power_pellet = pellet
            else:
                if dist_sq < best_regular_dist:
                    best_regular_dist = dist_sq
                    best_regular_pellet = pellet
        
        # Prefer power pellets unless a regular pellet is much closer
        if best_power_pellet is not None:
            # Only skip power pellet if regular is less than 1/4 the distance
            if best_regular_pellet is None or best_regular_dist > best_power_dist * 0.25:
                return best_power_pellet
        
        return best_regular_pellet if best_regular_pellet else best_power_pellet
    
    def find_path_to_nearest_pellet(self, start_node):
        """Use BFS to find the shortest path to ANY pellet.
        
        Instead of pathfinding to a specific target, this searches outward
        and returns the path to the first pellet encountered (shortest path).
        """
        if start_node is None:
            return []
        
        start_key = self.get_node_key(start_node)
        
        # Check if there's a pellet at start position
        for pellet in self.pellets.pelletList:
            if self.is_at_goal(start_node, pellet.position):
                return []  # Already at a pellet
        
        queue = deque()
        queue.append((start_node, []))
        visited = {start_key}
        
        while queue:
            current_node, path = queue.popleft()
            
            # Check if there's a pellet at this node
            for pellet in self.pellets.pelletList:
                if self.is_at_goal(current_node, pellet.position):
                    return path  # Found a pellet, return the path to it
            
            # Expand neighbors
            for neighbor, direction in self.get_neighbors(current_node):
                neighbor_key = self.get_node_key(neighbor)
                if neighbor_key not in visited:
                    visited.add(neighbor_key)
                    new_path = path + [direction]
                    queue.append((neighbor, new_path))
        
        return []
    
    def get_direction(self):
        """Get next direction using BFS to find nearest pellet."""
        if not self.pellets.pelletList:
            return STOP
        
        current_node = self.get_current_node()
        
        if self.should_replan(current_node):
            # BFS to find shortest path to any pellet
            self.current_path = self.find_path_to_nearest_pellet(current_node)
            
            if self.current_path:
                # Set current goal for replan tracking (approximate)
                self.current_goal = None  # We don't target a specific pellet
        
        if self.current_path:
            return self.current_path[0]
        
        return STOP


def create_agent(ai_mode, pacman, nodes, pellets, ghosts):
    """Factory function to create the appropriate AI agent."""
    if ai_mode == AI_ASTAR:
        return AStarAgent(pacman, nodes, pellets, ghosts)
    elif ai_mode == AI_BFS:
        return BFSAgent(pacman, nodes, pellets, ghosts)
    return None