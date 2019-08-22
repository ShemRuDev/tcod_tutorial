from enum import Enum

class GameStates(Enum):
    PLAYERS_TURN = 1
    ENEMY_TURN = 2,
    TARGETING = 3,

    SHOW_INVENTORY = 10,
    DROP_INVENTORY = 11,

    PLAYER_DEAD = 100