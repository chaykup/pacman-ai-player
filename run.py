import pygame
from pygame.locals import *
from constants import *
from pacman import Pacman
from nodes import NodeGroup
from pellets import PelletGroup
from ghosts import GhostGroup
from fruit import Fruit
from pauser import Pause
from text import TextGroup
from sprites import LifeSprites
from sprites import MazeSprites
from mazedata import MazeData
from ai_agent import create_agent, AStarAgent, BFSAgent, DFSAgent


class Button:
    """A simple button class for the AI selection interface."""
    
    def __init__(self, x, y, width, height, text, color, hover_color, selected_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.selected_color = selected_color
        self.is_hovered = False
        self.is_selected = False
        self.font = pygame.font.Font("PressStart2P-Regular.ttf", 10)
    
    def draw(self, screen):
        # Determine button color
        if self.is_selected:
            current_color = self.selected_color
        elif self.is_hovered:
            current_color = self.hover_color
        else:
            current_color = self.color
        
        # Draw button background with border
        pygame.draw.rect(screen, current_color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)  # Border
        
        # Draw text centered on button
        text_surface = self.font.render(self.text, True, WHITE if not self.is_selected else BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def check_click(self, pos):
        return self.rect.collidepoint(pos)


class GameController(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
        pygame.display.set_caption("Pacman - AI Agent Demo")
        self.background = None
        self.background_norm = None
        self.background_flash = None
        self.clock = pygame.time.Clock()
        self.fruit = None
        self.pause = Pause(True)
        self.level = 0
        self.lives = 5
        self.score = 0
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.flashBG = False
        self.flashTime = 0.2
        self.flashTimer = 0
        self.fruitCaptured = []
        self.fruitNode = None
        self.mazedata = MazeData()
        
        # AI related attributes
        self.ai_mode = AI_NONE
        self.ai_agent = None
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self):
        """Create the AI selection buttons."""
        button_width = 80
        button_height = 35
        button_spacing = 10
        total_width = 4 * button_width + 3 * button_spacing
        start_x = (SCREENWIDTH - total_width) // 2
        # Position buttons lower in the panel to leave room for mode text
        button_y = GAME_HEIGHT + 28
        
        # Define colors that match Pacman aesthetic
        base_color = (20, 20, 80)       # Dark blue
        hover_color = (40, 40, 120)     # Lighter blue
        
        # PLAYER Button - White theme
        self.player_button = Button(
            start_x, button_y, button_width, button_height,
            "PLAYER", base_color, hover_color, WHITE
        )
        self.player_button.is_selected = True  # Start with player selected
        
        # A* Button - Red theme (danger/avoidance)
        self.astar_button = Button(
            start_x + button_width + button_spacing, button_y, button_width, button_height,
            "A*", base_color, hover_color, RED
        )
        
        # BFS Button - Yellow theme (Pacman/score)
        self.bfs_button = Button(
            start_x + 2 * (button_width + button_spacing), button_y, button_width, button_height,
            "BFS", base_color, hover_color, YELLOW
        )
        
        # DFS Button - Green theme
        self.dfs_button = Button(
            start_x + 3 * (button_width + button_spacing), button_y, button_width, button_height,
            "DFS", base_color, hover_color, GREEN
        )
        
        self.buttons = [self.player_button, self.astar_button, self.bfs_button, self.dfs_button]

    def setBackground(self):
        self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_norm.fill(BLACK)
        self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_flash.fill(BLACK)
        self.background_norm = self.mazesprites.constructBackground(self.background_norm, self.level%5)
        self.background_flash = self.mazesprites.constructBackground(self.background_flash, 5)
        self.flashBG = False
        self.background = self.background_norm

    def startGame(self):      
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites(self.mazedata.obj.name+".txt", self.mazedata.obj.name+"_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup(self.mazedata.obj.name+".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)
        self.mazedata.obj.connectHomeNodes(self.nodes)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart))
        self.pellets = PelletGroup(self.mazedata.obj.name+".txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)

        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(0, 3)))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(4, 3)))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 0)))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.mazedata.obj.denyGhostsAccess(self.ghosts, self.nodes)
        
        # Reduce pellets to one if in DFS mode
        if self.ai_mode == AI_DFS:
            self.pellets.reduce_to_one_pellet()
        
        # Update AI agent with new game objects
        self.update_ai_agent()
        
        # Set AI controlled state based on current mode
        self.pacman.ai_controlled = (self.ai_mode != AI_NONE)

    def startGame_old(self):      
        self.mazedata.loadMaze(self.level)#######
        self.mazesprites = MazeSprites("maze1.txt", "maze1_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup("maze1.txt")
        self.nodes.setPortalPair((0,17), (27,17))
        homekey = self.nodes.createHomeNodes(11.5, 14)
        self.nodes.connectHomeNodes(homekey, (12,14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15,14), RIGHT)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.pellets = PelletGroup("maze1.txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 0+14))
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0+11.5, 3+14))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4+11.5, 3+14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)

    def update_ai_agent(self):
        """Create or update the AI agent based on current mode."""
        if self.ai_mode != AI_NONE and hasattr(self, 'pacman'):
            self.ai_agent = create_agent(
                self.ai_mode, 
                self.pacman, 
                self.nodes, 
                self.pellets, 
                self.ghosts
            )
        else:
            self.ai_agent = None

    def set_ai_mode(self, mode):
        """Set the AI mode and update button states."""
        old_mode = self.ai_mode
        self.ai_mode = mode
        
        # Update button selection states
        self.player_button.is_selected = (mode == AI_NONE)
        self.astar_button.is_selected = (mode == AI_ASTAR)
        self.bfs_button.is_selected = (mode == AI_BFS)
        self.dfs_button.is_selected = (mode == AI_DFS)
        
        # Handle pellet reduction/restoration for DFS mode
        if hasattr(self, 'pellets'):
            if mode == AI_DFS and old_mode != AI_DFS:
                # Switching to DFS mode - reduce pellets to one
                self.pellets.reduce_to_one_pellet()
            elif old_mode == AI_DFS and mode != AI_DFS:
                # Switching away from DFS mode - restore original pellets
                self.pellets.restore_original_pellets()
        
        # Update pacman control mode
        if hasattr(self, 'pacman'):
            self.pacman.ai_controlled = (self.ai_mode != AI_NONE)
        
        # Update AI agent
        self.update_ai_agent()

    def update(self):
        dt = self.clock.tick(30) / 1000.0
        self.textgroup.update(dt)
        self.pellets.update(dt)
        if not self.pause.paused:
            self.ghosts.update(dt)      
            if self.fruit is not None:
                self.fruit.update(dt)
            self.checkPelletEvents()
            self.checkGhostEvents()
            self.checkFruitEvents()

        if self.pacman.alive:
            if not self.pause.paused:
                # Update AI agent direction if in AI mode
                if self.ai_mode != AI_NONE and self.ai_agent is not None:
                    # Update agent's references (pellets may have changed)
                    self.ai_agent.pellets = self.pellets
                    direction = self.ai_agent.get_direction()
                    self.pacman.setAIDirection(direction)
                
                self.pacman.update(dt)
        else:
            self.pacman.update(dt)

        if self.flashBG:
            self.flashTimer += dt
            if self.flashTimer >= self.flashTime:
                self.flashTimer = 0
                if self.background == self.background_norm:
                    self.background = self.background_flash
                else:
                    self.background = self.background_norm

        afterPauseMethod = self.pause.update(dt)
        if afterPauseMethod is not None:
            afterPauseMethod()
        self.checkEvents()
        self.render()

    def checkEvents(self):
        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.player_button.check_click(mouse_pos):
                        self.set_ai_mode(AI_NONE)
                    elif self.astar_button.check_click(mouse_pos):
                        self.set_ai_mode(AI_ASTAR)
                    elif self.bfs_button.check_click(mouse_pos):
                        self.set_ai_mode(AI_BFS)
                    elif self.dfs_button.check_click(mouse_pos):
                        self.set_ai_mode(AI_DFS)
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                elif event.key == K_RETURN:
                    # Enter key starts/unpauses the game in any mode
                    if self.pause.paused:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()

    def checkPelletEvents(self):
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)
            if self.pellets.numEaten == 30:
                self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            if self.pellets.numEaten == 70:
                self.ghosts.clyde.startNode.allowAccess(LEFT, self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.flashBG = True
                self.hideEntities()
                self.pause.setPause(pauseTime=3, func=self.nextLevel)

    def checkGhostEvents(self):
        for ghost in self.ghosts:
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)                  
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -=  1
                        self.lifesprites.removeImage()
                        self.pacman.die()               
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.textgroup.showText(GAMEOVERTXT)
                            self.pause.setPause(pauseTime=3, func=self.restartGame)
                        else:
                            self.pause.setPause(pauseTime=3, func=self.resetLevel)
    
    def checkFruitEvents(self):
        if self.pellets.numEaten == 50 or self.pellets.numEaten == 140:
            if self.fruit is None:
                self.fruit = Fruit(self.nodes.getNodeFromTiles(9, 20), self.level)
                print(self.fruit)
        if self.fruit is not None:
            if self.pacman.collideCheck(self.fruit):
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(self.fruit.points), WHITE, self.fruit.position.x, self.fruit.position.y, 8, time=1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image)
                self.fruit = None
            elif self.fruit.destroy:
                self.fruit = None

    def showEntities(self):
        self.pacman.visible = True
        self.ghosts.show()

    def hideEntities(self):
        self.pacman.visible = False
        self.ghosts.hide()

    def nextLevel(self):
        self.showEntities()
        self.level += 1
        self.pause.paused = True
        self.startGame()
        self.textgroup.updateLevel(self.level)

    def restartGame(self):
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.fruit = None
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []

    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)
        
        # Reset AI direction
        if hasattr(self.pacman, 'ai_direction'):
            self.pacman.ai_direction = STOP

    def updateScore(self, points):
        self.score += points
        self.textgroup.updateScore(self.score)

    def render(self):
        self.screen.blit(self.background, (0, 0))
        #self.nodes.render(self.screen)
        self.pellets.render(self.screen)
        if self.fruit is not None:
            self.fruit.render(self.screen)
        self.pacman.render(self.screen)
        self.ghosts.render(self.screen)
        self.textgroup.render(self.screen)

        for i in range(len(self.lifesprites.images)):
            x = self.lifesprites.images[i].get_width() * i
            y = GAME_HEIGHT - self.lifesprites.images[i].get_height()
            self.screen.blit(self.lifesprites.images[i], (x, y))

        for i in range(len(self.fruitCaptured)):
            x = SCREENWIDTH - self.fruitCaptured[i].get_width() * (i+1)
            y = GAME_HEIGHT - self.fruitCaptured[i].get_height()
            self.screen.blit(self.fruitCaptured[i], (x, y))

        # Draw button panel background
        panel_rect = pygame.Rect(0, GAME_HEIGHT, SCREENWIDTH, BUTTON_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, (10, 10, 40), panel_rect)
        pygame.draw.line(self.screen, (50, 50, 150), (0, GAME_HEIGHT), (SCREENWIDTH, GAME_HEIGHT), 2)
        
        # Draw mode indicator text at the top of the panel
        mode_font = pygame.font.Font("PressStart2P-Regular.ttf", 8)
        if self.ai_mode == AI_NONE:
            mode_text = "PLAYER: Use arrow keys to play"
        elif self.ai_mode == AI_ASTAR:
            mode_text = "A*: Avoids ghosts, survives longer"
        elif self.ai_mode == AI_BFS:
            mode_text = "BFS: Prioritizes highest score"
        elif self.ai_mode == AI_DFS:
            mode_text = "DFS: Depth-first search strategy"
        else:
            mode_text = ""
        
        text_surface = mode_font.render(mode_text, True, (180, 180, 180))
        text_rect = text_surface.get_rect(centerx=SCREENWIDTH // 2, top=GAME_HEIGHT + 8)
        self.screen.blit(text_surface, text_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        pygame.display.update()


if __name__ == "__main__":
    game = GameController()
    game.startGame()
    while True:
        game.update()