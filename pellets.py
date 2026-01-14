import pygame
from vector import Vector2
from constants import *
import numpy as np

class Pellet(object):
    def __init__(self, row, column):
        self.name = PELLET
        self.position = Vector2(column*TILEWIDTH, row*TILEHEIGHT)
        self.color = WHITE
        self.radius = int(2 * TILEWIDTH / 16)
        self.collideRadius = 2 * TILEWIDTH / 16
        self.points = 10
        self.visible = True
        
    def render(self, screen):
        if self.visible:
            adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2
            p = self.position + adjust
            pygame.draw.circle(screen, self.color, p.asInt(), self.radius)


class PowerPellet(Pellet):
    def __init__(self, row, column):
        Pellet.__init__(self, row, column)
        self.name = POWERPELLET
        self.radius = int(8 * TILEWIDTH / 16)
        self.points = 50
        self.flashTime = 0.2
        self.timer= 0
        
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.flashTime:
            self.visible = not self.visible
            self.timer = 0


class PelletGroup(object):
    def __init__(self, pelletfile):
        self.pelletList = []
        self.powerpellets = []
        self.pelletfile = pelletfile  # Store filename for restoration
        self.createPelletList(pelletfile)
        self.numEaten = 0
        self.originalPelletList = []  # Store original pellets for DFS mode
        self.originalPowerPellets = []
        self.originalNumEaten = 0
        self.is_dfs_mode = False  # Track if we're in DFS mode

    def update(self, dt):
        for powerpellet in self.powerpellets:
            powerpellet.update(dt)
                
    def createPelletList(self, pelletfile):
        data = self.readPelletfile(pelletfile)        
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                if data[row][col] in ['.', '+']:
                    self.pelletList.append(Pellet(row, col))
                elif data[row][col] in ['P', 'p']:
                    pp = PowerPellet(row, col)
                    self.pelletList.append(pp)
                    self.powerpellets.append(pp)
                    
    def readPelletfile(self, textfile):
        return np.loadtxt(textfile, dtype='<U1')
    
    def isEmpty(self):
        if len(self.pelletList) == 0:
            return True
        return False
    
    def render(self, screen):
        for pellet in self.pelletList:
            pellet.render(screen)
    
    def store_original_pellets(self):
        """Store the current state before reducing pellets for DFS mode."""
        # Store references to current lists and state
        self.originalPelletList = list(self.pelletList)
        self.originalPowerPellets = list(self.powerpellets)
        self.originalNumEaten = self.numEaten
    
    def reduce_to_one_pellet(self):
        """Reduce pellets to just one pellet for DFS mode."""
        if not self.is_dfs_mode:
            self.store_original_pellets()
            self.is_dfs_mode = True
        
        # Keep only the first regular pellet (prefer regular over power pellet)
        if self.pelletList:
            # Find first regular pellet
            single_pellet = None
            for pellet in self.pelletList:
                if pellet.name == PELLET:
                    single_pellet = pellet
                    break
            
            # If no regular pellet, use first power pellet
            if single_pellet is None and self.pelletList:
                single_pellet = self.pelletList[0]
            
            if single_pellet:
                self.pelletList = [single_pellet]
                # Update powerpellets list - only include if it's a power pellet
                if single_pellet.name == POWERPELLET:
                    self.powerpellets = [single_pellet]
                else:
                    self.powerpellets = []
    
    def restore_original_pellets(self):
        """Restore the original pellets when switching away from DFS mode."""
        if self.is_dfs_mode and self.originalPelletList:
            # Recreate pellets from the original file to ensure clean state
            self.pelletList = []
            self.powerpellets = []
            self.createPelletList(self.pelletfile)
            # Restore the number eaten (though this might not be perfect if pellets were eaten)
            self.numEaten = self.originalNumEaten
            self.is_dfs_mode = False