import os
import threading
import time
from queue import Queue

import pygame

import config
from sprites import Spaceship, AbyssTile, FreeTile, ColoredTile
from state import State
from util import TimedFunction, Timeout, Logger


class Quit(Exception):
    pass


class EndGame(Exception):
    pass


class Game:
    def adjust_dimensions(self, lines):
        config.M = len(lines)
        config.N = len(lines[0].strip())
        tile_height = int(config.SCREEN_HEIGHT * 0.9 / config.M)
        tile_width = int(config.SCREEN_WIDTH * 0.9 / config.N)
        if tile_height < config.MIN_TILE_SIZE:
            raise Exception(f'Decrease the number of rows in map! '
                            f'MIN_TILE_SIZE is {config.MIN_TILE_SIZE}px but {tile_height}px occurred.')
        if tile_width < config.MIN_TILE_SIZE:
            raise Exception(f'Decrease the number of columns in map! '
                            f'MIN_TILE_SIZE is {config.MIN_TILE_SIZE}px but {tile_width}px occurred.')
        config.TILE_SIZE = int(min(config.MAX_TILE_SIZE, tile_height, tile_width))
        config.TILE_OFFSET = int(config.TILE_SIZE * config.TILE_STEP)
        self.WIDTH = config.N * config.TILE_SIZE
        self.HEIGHT = config.M * config.TILE_SIZE
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT + config.INFO_HEIGHT), flags=pygame.HIDDEN)

    def load_map(self, map_name):
        try:
            self.sprites_free_tiles = pygame.sprite.Group()
            self.sprites_abyss_tiles = pygame.sprite.Group()
            self.sprites_colored_tiles = pygame.sprite.Group()
            self.sprites_spaceships = pygame.sprite.Group()

            self.colored_map = {}
            self.spaceships_map = {}

            with open(os.path.join(config.MAP_FOLDER, map_name), 'r') as file:
                lines = file.readlines()
                self.adjust_dimensions(lines)

                mask = 1
                all_ones_mask = (1 << (config.M * config.N)) - 1
                abyss_tiles_positions_int = 0 & all_ones_mask
                colored_tiles_positions_dict = {}
                spaceships_positions_dict = {}

                for i, line in enumerate(lines):
                    for j, char in enumerate(line.strip()):
                        tile = FreeTile((i, j))
                        tile.add(self.sprites_free_tiles)
                        if char not in FreeTile.kinds():
                            error_flag = True
                            if char.lower() in ColoredTile.kinds():
                                error_flag = False
                                sprite = ColoredTile(char.lower(), (i, j))
                                sprite.add(self.sprites_colored_tiles)
                                self.colored_map[(i, j)] = sprite
                                if char.lower() not in colored_tiles_positions_dict:
                                    colored_tiles_positions_dict[char.lower()] = 0 & all_ones_mask
                                colored_tiles_positions_dict[char.lower()] |= mask
                                if char in Spaceship.kinds():
                                    sprite = Spaceship(char, (i, j), char)
                                    sprite.add(self.sprites_spaceships)
                                    self.spaceships_map[(i, j)] = sprite
                                    if char not in spaceships_positions_dict:
                                        spaceships_positions_dict[char] = mask
                            if char in AbyssTile.kinds():
                                error_flag = False
                                sprite = AbyssTile((i, j))
                                sprite.add(self.sprites_abyss_tiles)
                                abyss_tiles_positions_int |= mask
                            if error_flag:
                                raise Exception(f'Illegal character {char} in map!')
                        mask <<= 1
            return State(spaceships_positions_dict,
                         colored_tiles_positions_dict,
                         abyss_tiles_positions_int, self.max_rounds)
        except Exception as e:
            raise e

    def get_algorithms(self, algorithms_names):
        num_of_players = self.state.get_num_of_players()
        if len(algorithms_names) >= num_of_players:
            algorithms_names = algorithms_names[:num_of_players]
        else:
            algorithms_names += [algorithms_names[-1]] * (num_of_players - len(algorithms_names))
        module_agents = __import__('agents')
        return [getattr(module_agents, algo_name) for algo_name in algorithms_names]

    def __init__(self, algorithms_names, map_name, max_rounds, max_think_time, max_depth):
        self.logger = Logger()
        pygame.font.init()
        config.INFO_FONT = pygame.font.Font(os.path.join(config.FONT_FOLDER, 'info_font.ttf'), 22)
        pygame.display.set_caption('Pynter')
        self.WIDTH = None
        self.HEIGHT = None
        self.screen = None
        self.sprites_free_tiles = None
        self.sprites_abyss_tiles = None
        self.sprites_colored_tiles = None
        self.sprites_spaceships = None
        self.spaceships_map = None
        self.colored_map = None
        self.running = True  # application running
        self.playing = False  # play/pause
        self.moving = False  # current agent moving
        self.done = False  # reached goal state
        self.max_rounds = max_rounds
        self.think_time = 0
        self.max_think_time = max_think_time
        self.max_depth = max_depth
        self.state = self.load_map(map_name)
        self.algorithms = self.get_algorithms(algorithms_names)
        self.clock = pygame.time.Clock()

    def get_action(self):
        try:
            tf_queue = Queue(1)
            tf = TimedFunction(threading.current_thread().ident,
                               tf_queue, self.max_think_time,
                               self.algorithms[self.state.get_on_move_ord()].get_chosen_action,
                               self.algorithms[self.state.get_on_move_ord()],
                               self.state,
                               self.max_depth)
            tf.daemon = True
            tf.start()
            sleep_time = config.SLEEP_TIME
            while tf_queue.empty():
                time.sleep(sleep_time)
                self.draw_info_text()
                self.events()
            action, elapsed = tf_queue.get(block=False)
            return action, elapsed
        except Timeout:
            print(f'ERROR: Agent action took more than {self.max_think_time} seconds!')
            raise Quit()

    def perform_action(self):
        action, self.think_time = self.get_action()
        current_pos, target_pos = action
        row_diff = target_pos[0] - current_pos[0]
        col_diff = target_pos[1] - current_pos[1]
        loop_step = 1 if row_diff + col_diff > 0 else -1
        path = [
            (current_pos[0], current_pos[1] + x) if row_diff == 0 else (current_pos[0] + x, current_pos[1])
            for x in range(0, col_diff + row_diff + loop_step, loop_step)
        ]
        return action, path

    def print_info(self, action):
        info_text = (f'\nRound {self.state.get_current_round() + 1} / {self.state.get_max_rounds()}\n'
                     f'In state\n'
                     f'{self.state}\n'
                     f'agent {self.state.get_on_move_chr()} chose action {action} '
                     f'from actions {self.state.get_legal_actions()}\n'
                     f'Think time was {self.think_time:.2f} seconds.\n')
        self.logger.log_info(info_text, to_std_out=config.DEBUG)

    def perform_moving(self, current_pos, target_pos, path, action):
        if current_pos != target_pos:
            self.spaceships_map[target_pos] = self.spaceships_map[current_pos]
            del self.spaceships_map[current_pos]
        sprite = ColoredTile(self.state.get_on_move_chr().lower(), target_pos)
        if target_pos in self.colored_map:
            self.colored_map[target_pos].remove(self.sprites_colored_tiles)
        sprite.add(self.sprites_colored_tiles)
        self.colored_map[target_pos] = sprite
        if path:
            current_pos = target_pos
            target_pos = path.pop(0)
        else:
            self.print_info(action)
            self.state = self.state.generate_successor_state(action)
            self.moving = False
        return current_pos, target_pos

    def run(self):
        try:
            self.logger.log_info('Starting simulation ...', to_std_out=config.DEBUG)
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT + config.INFO_HEIGHT),
                                                  flags=pygame.SHOWN)
            action, path, current_pos, target_pos = None, None, None, None
            while self.running:
                try:
                    if self.playing:
                        if self.state.is_goal_state():
                            self.logger.log_info(f'\nFinal state\n{self.state}', to_std_out=config.DEBUG)
                            raise EndGame()
                        if not self.moving:
                            action, path = self.perform_action()
                            current_pos = path.pop(0)
                            target_pos = path.pop(0) if path else current_pos
                            self.moving = True
                        if not self.spaceships_map[current_pos].move_towards(target_pos):
                            current_pos, target_pos = self.perform_moving(current_pos, target_pos, path, action)
                    self.draw()
                    self.events()
                    self.clock.tick(config.FRAMES_PER_SEC)
                except EndGame:
                    self.playing = False
                    self.done = True
                except Quit:
                    self.playing = False
                    self.running = False
        except Exception as e:
            self.logger.log_error(repr(e))
            raise e
        finally:
            self.logger.close()

    def draw_info_text(self):
        self.screen.fill(config.BLACK, [0, self.HEIGHT, self.WIDTH, config.INFO_HEIGHT])
        if self.done:
            text_str = 'DONE'
        elif self.playing:
            text_str = (f'R {self.state.get_current_round() + 1}/{self.state.get_max_rounds()} | '
                        f'on move: {self.state.get_on_move_chr()}')
        else:
            text_str = 'PAUSED'
        text_width, text_height = config.INFO_FONT.size(text_str)
        text = config.INFO_FONT.render(f'{text_str}', True, config.GREEN)
        self.screen.blit(text, (self.WIDTH - text_width - config.INFO_SIDE_OFFSET, self.HEIGHT))

        total_text_width = 0
        for i, (key, val) in enumerate(sorted(self.state.get_scores().items())):
            text_str = f'{"  " if i else ""}{key}: {val:02d}'
            text = config.INFO_FONT.render(f'{text_str}', True, Spaceship.colors()[key])
            text_width, text_height = config.INFO_FONT.size(text_str)
            self.screen.blit(text, (total_text_width + config.INFO_SIDE_OFFSET, self.HEIGHT))
            total_text_width += text_width
        pygame.display.flip()

    def draw(self):
        self.screen.fill(config.WHITE)
        self.sprites_free_tiles.draw(self.screen)
        self.sprites_colored_tiles.draw(self.screen)
        self.sprites_abyss_tiles.draw(self.screen)
        self.sprites_spaceships.draw(self.screen)
        self.draw_info_text()

    def events(self):
        # catch all events here
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.WINDOWCLOSE or \
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise Quit()
            if self.done:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.playing = not self.playing
