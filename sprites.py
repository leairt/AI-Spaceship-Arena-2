import os
from random import randint

import pygame

import config


class BaseSprite(pygame.sprite.Sprite):
    images_dict = {}

    def __init__(self, position, size, kind, image_name=None, offset=(0, 0)):
        super().__init__()
        self.kind = kind
        if image_name is None:
            image_name = f'{self.__class__.__name__.lower()}.png'
        if image_name in BaseSprite.images_dict:
            image = BaseSprite.images_dict[image_name]
        else:
            image = pygame.image.load(os.path.join(config.IMG_FOLDER, image_name)).convert()
            image = pygame.transform.scale(image, size)
            image.set_colorkey(config.WHITE)
            BaseSprite.images_dict[image_name] = image
        self.image = image.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = (position[1] * config.TILE_SIZE + offset[1], position[0] * config.TILE_SIZE + offset[0])

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def my_kind(self):
        return self.kind

    @classmethod
    def kinds(cls):
        raise NotImplementedError('Subclasses must implement .kinds()')


class Spaceship(BaseSprite):
    def __init__(self, kind, position, spaceship_name):
        super().__init__(position, (config.TILE_SIZE, config.TILE_SIZE),
                         kind, f'{self.__class__.__name__.lower()}_{spaceship_name}.png')

    def move_towards(self, destination):
        dy = destination[0] * config.TILE_SIZE - self.rect.y
        dx = destination[1] * config.TILE_SIZE - self.rect.x

        if abs(dy) > config.TILE_OFFSET:
            self.rect.y += config.TILE_OFFSET if dy > 0 else -config.TILE_OFFSET
        elif abs(dx) > config.TILE_OFFSET:
            self.rect.x += config.TILE_OFFSET if dx > 0 else -config.TILE_OFFSET
        else:
            self.rect.y, self.rect.x = destination[0] * config.TILE_SIZE, destination[1] * config.TILE_SIZE
            return False
        return True

    def place_to(self, destination):
        self.rect.y, self.rect.x = destination[0] * config.TILE_SIZE, destination[1] * config.TILE_SIZE

    @classmethod
    def kinds(cls):
        return ['A', 'B', 'C', 'D']

    @staticmethod
    def colors():
        return {
            'A': config.CYAN,
            'B': config.YELLOW,
            'C': config.LIGHT_GREEN,
            'D': config.PINK
        }

    def chr_to_ord(self):
        return ord(self.kind) - ord('A')


class ColoredTile(BaseSprite):
    def __init__(self, kind, position):
        super().__init__(position, (config.TILE_SIZE, config.TILE_SIZE),
                         kind, f'{self.__class__.__name__.lower()}_{kind}.png')

    @classmethod
    def kinds(cls):
        return ['a', 'b', 'c', 'd']


class AbyssTile(BaseSprite):
    DIFFERENT_ABYSS_TYPES = 7

    def __init__(self, position):
        super().__init__(position, (config.TILE_SIZE, config.TILE_SIZE),
                         '0', f'{self.__class__.__name__.lower()}{randint(0, AbyssTile.DIFFERENT_ABYSS_TYPES - 1)}.png')

    @classmethod
    def kinds(cls):
        return ['0']


class FreeTile(BaseSprite):
    def __init__(self, position):
        super().__init__(position, (config.TILE_SIZE, config.TILE_SIZE), '_')

    @classmethod
    def kinds(cls):
        return ['_']
