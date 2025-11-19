import sys
import traceback

import pygame

import config
from game import Game

try:
    algorithms_names = sys.argv[1].split(',') if len(sys.argv) > 1 else ['RandomAgent']
    if len(algorithms_names) > config.MAX_PLAYERS:
        raise Exception('Too many agents!')
    map_filename = sys.argv[2] if len(sys.argv) > 2 else 'example_map.txt'
    max_rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    max_elapsed_time = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    max_depth = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    config.DEBUG = bool(sys.argv[6]) if len(sys.argv) > 6 else True
    g = Game(algorithms_names, map_filename, max_rounds, max_elapsed_time, max_depth)
    g.run()
except (Exception,):
    traceback.print_exc()
    input()
finally:
    pygame.display.quit()
    pygame.quit()
