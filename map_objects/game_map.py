import tcod as libtcod
from random import randint

from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item

from map_objects.tile import Tile
from map_objects.rectangle import RL_Rect

from entity import Entity
from render_functions import RenderOrder
from item_functions import itm_heal, cast_lightning, cast_fireball, cast_confusion
from game_messages import Message

class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size, player, 
                entities, max_monsters_per_room, max_items_per_room):
        rooms = []
        num_rooms = 0
        
        for r in range(max_rooms):
            rand_w = randint(room_min_size, room_max_size)
            rand_h = randint(room_min_size, room_max_size)
            rand_x = randint(0, self.width - rand_w - 1)
            rand_y = randint(0, self.height - rand_h - 1)

            new_room = RL_Rect(rand_x, rand_y, rand_w, rand_h)

            for other_room in rooms:
                if new_room.is_intersect(other_room):
                    break
            else:
                self.create_room(new_room)

                #center of new room
                (new_x, new_y) = new_room.center()

                # place player in first room
                if num_rooms == 0:
                    player.x = new_x
                    player.y = new_y
                else:
                    # all remained rooms. connect'em to previous
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()
                    # flip a coin for tunnel directions order
                    if randint(0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                
                self.place_entities(new_room, entities, max_monsters_per_room, max_items_per_room)

                rooms.append(new_room)
                num_rooms += 1

    def create_room(self, room):
        # Make room space passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities, max_monsters_per_room, max_items_per_room):
        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_items = randint(0, max_items_per_room)

        # Monsters
        for i in range(number_of_monsters):
            rand_x = randint(room.x1 + 1, room.x2 - 1)
            rand_y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == rand_x and entity.y == rand_y]):
                if randint(0, 100) < 80:
                    o_f_comp = Fighter(10, 0, 3)
                    o_ai_comp = BasicMonster()
                    monster = Entity(rand_x, rand_y, 'o', libtcod.desaturated_green, 'Orc', True, RenderOrder.ACTOR, o_f_comp, o_ai_comp)
                else:
                    t_f_comp = Fighter(16, 1, 4)
                    t_ai_comp = BasicMonster()
                    monster = Entity(rand_x, rand_y, 'T', libtcod.darker_green, 'Troll', True, RenderOrder.ACTOR, t_f_comp, t_ai_comp)

                entities.append(monster)

        # Items
        for i in range(number_of_items):
            rand_x = randint(room.x1 + 1, room.x2 - 1)
            rand_y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == rand_x and entity.y == rand_y]):
                item_chance = randint(0, 100)

                if item_chance < 60:
                    item_heal_comp = Item(use_function=itm_heal, amount=4)
                    item = Entity(rand_x, rand_y, '!', libtcod.violet, 'Healing Potion', render_order = RenderOrder.ITEM, item=item_heal_comp)
                elif item_chance < 75:
                    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
                        'Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan),
                                          damage=12, radius=3)
                    item = Entity(rand_x, rand_y, '#', libtcod.red, 'Fireball Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)
                elif item_chance < 90:
                    item_component = Item(use_function=cast_confusion, targeting=True, targeting_message=Message(
                        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan))
                    item = Entity(rand_x, rand_y, '#', libtcod.light_pink, 'Confusion Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)
                else:
                    item_scroll_lightning_comp = Item(use_function=cast_lightning, damage=20, maximum_range=5)
                    item = Entity(rand_x, rand_y, '#', libtcod.yellow, 'Lightning Scroll', render_order = RenderOrder.ITEM, item=item_scroll_lightning_comp)

                entities.append(item)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True

        return False