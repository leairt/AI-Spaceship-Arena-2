import os

import screeninfo

monitor = screeninfo.get_monitors()[0]

# parameters
MAX_PLAYERS = 4
M = None
N = None
SCREEN_WIDTH = monitor.width
SCREEN_HEIGHT = monitor.height
MIN_TILE_SIZE = 32
TILE_SIZE = 64
MAX_TILE_SIZE = 128
TILE_STEP = 0.05
TILE_OFFSET = None
INFO_FONT = None
INFO_HEIGHT = 30
INFO_SIDE_OFFSET = 10
FRAMES_PER_SEC = 120
SLEEP_TIME = 0.001
DEBUG = True

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (192, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 128, 0)
YELLOW = (220, 210, 150)
PINK = (228, 180, 180)
CYAN = (128, 180, 210)
LIGHT_GREEN = (160, 210, 130)

# paths
GAME_FOLDER = os.path.dirname(__file__)
MAP_FOLDER = os.path.join(GAME_FOLDER, 'maps')
IMG_FOLDER = os.path.join(GAME_FOLDER, 'img')
LOG_FOLDER = os.path.join(GAME_FOLDER, 'logs')
FONT_FOLDER = os.path.join(GAME_FOLDER, 'fonts')
