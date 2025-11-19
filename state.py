"""
STATE REPRESENTATION
For instance, for (6 x 7) map dimension and 2 players (A and B)
state is represented with 3 values of 42 (6 x 7) bits and 2 ints representing
first spaceship's colored tiles (a), first spaceship position (A; int),
second spaceship's colored tiles (b), second spaceship position (B; int),
and obstacles (0).
Row numbers increase from top to bottom,
while column numbers increase from left to right.
 0   1   2   3   4   5   6 | column id
 =====================================
 0   1   2   3   4   5   6 | 0th row
 7   8   9  10  11  12  13 | 1st row
14  15  16  17  18  19  20 | 2nd row
21  22  23  24  25  26  27 | 3rd row
28  29  30  31  32  33  34 | 4th row
35  36  37  38  39  40  41 | 5th row

For instance:
STATE            STATE_binary_    first colored     second colored   abyss state
a a a 0 _ b _    1 1 1 1 0 1 0    1 1 1 0 0 0 0     0 0 0 0 0 1 0    0 0 0 1 0 0 0
_ _ a _ _ b _    0 0 1 0 0 1 0    0 0 1 0 0 0 0     0 0 0 0 0 1 0    0 0 0 0 0 0 0
_ _ A _ _ b _    0 0 1 0 0 1 0    0 0 1 0 0 0 0     0 0 0 0 0 1 0    0 0 0 0 0 0 0
_ _ 0 _ _ b _    0 0 1 0 0 1 0    0 0 0 0 0 0 0     0 0 0 0 0 1 0    0 0 1 0 0 0 0
_ _ _ _ _ b _    0 0 0 0 0 1 0    0 0 0 0 0 0 0     0 0 0 0 0 1 0    0 0 0 0 0 0 0
_ _ _ _ 0 b B    0 0 0 0 1 1 1    0 0 0 0 0 0 0     0 0 0 0 0 1 1    0 0 0 0 1 0 0

A position = 2^16
B position = 2^41

"""
import copy
import math
from collections import Counter

import config
from sprites import Spaceship, AbyssTile, ColoredTile


class State:
    def __init__(self, spaceships_positions_dict, colored_tiles_positions_dict, abyss_tiles_positions_int, max_rounds):
        self.all_ones_mask = (1 << (config.M * config.N)) - 1
        self.row_masks = [((1 << config.N) - 1) << (i * config.N) for i in range(config.M)]
        self.num_of_players = len(spaceships_positions_dict)
        self.spaceships_positions_dict = spaceships_positions_dict
        self.colored_tiles_positions_dict = colored_tiles_positions_dict
        self.abyss_tiles_positions_int = abyss_tiles_positions_int
        self.on_move = 0
        self.legal_actions = {}
        self.max_rounds = max_rounds
        self.current_round = 0

    def __str__(self):
        char_matrix = [['_'] * config.N for _ in range(config.M)]
        for i in range(config.M):
            for j in range(config.N):
                mask_set_bit = 1 << (i * config.N + j)
                for kind, position in self.spaceships_positions_dict.items():
                    if mask_set_bit == position:
                        char_matrix[i][j] = kind
                        break
                    elif kind.lower() in self.colored_tiles_positions_dict and (
                            mask_set_bit & self.colored_tiles_positions_dict[kind.lower()]):
                        char_matrix[i][j] = kind.lower()
                        break
                else:
                    if mask_set_bit & self.abyss_tiles_positions_int:
                        char_matrix[i][j] = '0'
        return '\n'.join(' '.join(row) for row in char_matrix)

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return (self.get_state(Spaceship.kinds()) == other.get_state(Spaceship.kinds()) and
                self.get_state(ColoredTile.kinds()) == other.get_state(ColoredTile.kinds()) and
                self.get_state(AbyssTile.kinds()) == other.get_state(AbyssTile.kinds()) and
                self.on_move == other.on_move)

    def __hash__(self):
        return hash((
            self.get_state(Spaceship.kinds()),
            self.get_state(ColoredTile.kinds()),
            self.get_state(AbyssTile.kinds()),
            self.on_move
        ))

    def __lt__(self, other):
        return self.get_state(Spaceship.kinds()) < other.get_state(Spaceship.kinds())

    def get_num_of_players(self):
        return self.num_of_players

    def get_current_round(self):
        return self.current_round

    def get_max_rounds(self):
        return self.max_rounds

    def get_scores(self):
        result = {}
        for kind, color in self.colored_tiles_positions_dict.items():
            result[kind.upper()] = self.get_score(kind)
        return result

    def get_score(self, kind):
        color = self.colored_tiles_positions_dict[kind.lower()]
        score = color.bit_count() if hasattr(color, 'bit_count') else bin(color).count('1')
        return score

    def get_state(self, kind=None):
        if kind is None:
            state = 0
            for val in self.spaceships_positions_dict.values():
                state |= val
            for val in self.colored_tiles_positions_dict.values():
                state |= val
            state |= self.abyss_tiles_positions_int
            return state
        elif type(kind) is list and Counter(kind) == Counter(self.spaceships_positions_dict.keys()):
            state = 0
            for val in self.spaceships_positions_dict.values():
                state |= val
            return state
        elif type(kind) is list and Counter(kind) == Counter(self.colored_tiles_positions_dict.keys()):
            state = 0
            for val in self.colored_tiles_positions_dict.values():
                state |= val
            return state
        elif kind in Spaceship.kinds():
            return self.spaceships_positions_dict[kind]
        elif kind in ColoredTile.kinds():
            return self.colored_tiles_positions_dict[kind]
        elif kind in AbyssTile.kinds():
            return self.abyss_tiles_positions_int
        raise ValueError(f'ERROR: No such kind: {kind}')

    def is_goal_state(self):
        return (self.get_state() == self.all_ones_mask) or (self.current_round == self.max_rounds)

    @staticmethod
    def get_action_cost(action):
        return int(abs(action[0][0] - action[1][0]) + abs(action[0][1] - action[1][1]))

    def get_legal_actions(self):
        if self.is_goal_state():
            return []

        if self.get_on_move_chr() in self.legal_actions:
            return self.legal_actions[self.get_on_move_chr()]

        obstacles = 0
        for pos in self.spaceships_positions_dict.values():
            obstacles |= pos
        obstacles |= self.abyss_tiles_positions_int

        position = self.spaceships_positions_dict[self.get_on_move_chr()]
        obs = obstacles & ~position

        pos_idx = int(math.log2(position))

        actions = []

        # up all the way
        new_b = position
        while (val := (new_b >> config.N)) and not (val & obs):
            new_b = val
        end_idx = int(math.log2(new_b))
        if pos_idx != end_idx:
            actions.append((pos_idx, end_idx))

        # right all the way
        m = self.row_masks[pos_idx // config.N]
        new_b = position
        while (val := (new_b << 1)) & m and not (val & obs):
            new_b = val
        end_idx = int(math.log2(new_b))
        if pos_idx != end_idx:
            actions.append((pos_idx, end_idx))

        # down all the way
        new_b = position
        while (val := (new_b << config.N)) <= self.all_ones_mask and not (val & obs):
            new_b = val
        end_idx = int(math.log2(new_b))
        if pos_idx != end_idx:
            actions.append((pos_idx, end_idx))

        # left all the way
        new_b = position
        while (val := (new_b >> 1)) & m and not (val & obs):
            new_b = val
        end_idx = int(math.log2(new_b))
        if pos_idx != end_idx:
            actions.append((pos_idx, end_idx))

        def bit_to_coord(idx):
            return idx // config.N, idx % config.N

        actions = [(bit_to_coord(a[0]), bit_to_coord(a[1])) for a in actions]

        # one tile movement actions
        one_tile_actions = []
        for src, dst in actions:
            diff_row = dst[0] - src[0]
            diff_col = dst[1] - src[1]
            if abs(diff_row) > 1:
                nr = src[0] + (1 if diff_row > 0 else -1)
                nc = src[1]
                dst_bit = 1 << (nr * config.N + nc)
                if not (dst_bit & obs):
                    one_tile_actions.append((src, (nr, nc)))
            elif abs(diff_col) > 1:
                nr = src[0]
                nc = src[1] + (1 if diff_col > 0 else -1)
                dst_bit = 1 << (nr * config.N + nc)
                if not (dst_bit & obs):
                    one_tile_actions.append((src, (nr, nc)))

        actions.extend(one_tile_actions)

        # stay on tile action
        actions.append((bit_to_coord(pos_idx), bit_to_coord(pos_idx)))
        self.legal_actions[self.get_on_move_chr()] = actions

        return actions

    def get_on_move_ord(self):
        return self.on_move

    def get_on_move_chr(self):
        return chr(ord('A') + self.on_move)

    def move_to_next_player(self):
        self.on_move = (self.on_move + 1) % self.num_of_players
        if self.on_move == 0:
            self.current_round += 1

    def generate_successor_state(self, action):
        if self.is_goal_state():
            raise Exception(f'ERROR: State is goal!\n{self}')

        current_spaceship = self.get_on_move_chr()
        legal_actions = self.get_legal_actions()
        if action not in legal_actions:
            raise Exception(f'ERROR: Illegal action {action}!')

        # shallow copy
        copy_state = copy.copy(self)
        # deep copy
        copy_state.spaceships_positions_dict = self.spaceships_positions_dict.copy()
        copy_state.colored_tiles_positions_dict = self.colored_tiles_positions_dict.copy()
        copy_state.legal_actions = {}

        src, dst = action
        src_mask = (1 << (src[0] * config.N + src[1])) & self.all_ones_mask
        dst_mask = (1 << (dst[0] * config.N + dst[1])) & self.all_ones_mask
        # clear spaceship from current position
        copy_state.spaceships_positions_dict[current_spaceship] &= ~src_mask
        # set spaceship to next position
        copy_state.spaceships_positions_dict[current_spaceship] |= dst_mask

        # coloring tiles
        diff_row = dst[0] - src[0]
        diff_col = dst[1] - src[1]
        if diff_row:
            step = 1 if diff_row > 0 else -1
            for i in range(0, diff_row + step, step):
                pos = src[0] + i
                bit = 1 << (pos * config.N + src[1])
                for key in copy_state.colored_tiles_positions_dict:
                    if key == current_spaceship.lower():
                        copy_state.colored_tiles_positions_dict[key] |= bit
                    else:
                        copy_state.colored_tiles_positions_dict[key] &= ~bit
        elif diff_col != 0:
            step = 1 if diff_col > 0 else -1
            for i in range(0, diff_col + step, step):
                pos = src[1] + i
                bit = 1 << (src[0] * config.N + pos)
                for key in copy_state.colored_tiles_positions_dict:
                    if key == current_spaceship.lower():
                        copy_state.colored_tiles_positions_dict[key] |= bit
                    else:
                        copy_state.colored_tiles_positions_dict[key] &= ~bit
        else:
            pass

        copy_state.move_to_next_player()
        return copy_state
