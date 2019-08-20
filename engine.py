import tcod as libtcod
import tcod.event as libevent

from map_objects.game_map import GameMap

from components.fighter import Fighter
from components.inventory import Inventory

from game_states import GameStates
from game_messages import MessageLog, Message
from entity import Entity, get_blocking_entities_at_location
from input_handlers import handle_keys
from render_functions import clear_all, render_all, RenderOrder
from fov_functions import initialize_fov, recompute_fov
from death_functions import kill_player, kill_monster

def main():
    # console props
    screen_width = 80
    screen_height = 50

    # UI settings
    bar_width = 20
    ui_panel_height = 7
    ui_panel_y = screen_height - ui_panel_height
    ## Message system
    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = ui_panel_height - 1
    message_log = MessageLog(message_x, message_width, message_height)

    # map props
    map_width = 80
    map_height = 43
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30
    max_monsters_per_room = 3
    max_items_per_room = 2

    # FOV settings
    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 10
    fov_recompute = True # we don't need to recompute FOV everytime (wait, fight, use item)

    # Colors dictionary
    colors = {
        'dark_wall': libtcod.Color(0, 0, 100),
        'dark_ground': libtcod.Color(50, 50, 150),
        'light_wall': libtcod.Color(130, 110, 50),
        'light_ground': libtcod.Color(200, 180, 50)
    }

    # Entities setup
    player_fighter_comp = Fighter(30, 2, 5)
    player_inventory_comp = Inventory(12)
    player = Entity(0, 0, '@', libtcod.white, 'Player', True, RenderOrder.ACTOR, 
                    player_fighter_comp, inventory=player_inventory_comp)
    entities = [player]
    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state

    # Consoles setup
    libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GRAYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(screen_width, screen_height, 'First Shem RL. Thanks Tutorial', False)
    con = libtcod.console.Console(screen_width, screen_height)
    ui_panel = libtcod.console.Console(screen_width, ui_panel_height)

    # Gamemap setup
    game_map = GameMap(map_width, map_height)
    game_map.make_map(max_rooms, room_min_size, room_max_size, player, entities, max_monsters_per_room, max_items_per_room)

    fov_map = initialize_fov(game_map)

    # Input setup
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    # WARN Check tcod.event for QUIT events
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)        

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_radius, fov_light_walls, fov_algorithm)

        render_all(con, entities, player, game_map, fov_map, fov_recompute, screen_width, screen_height, 
                    ui_panel, bar_width, ui_panel_height, ui_panel_y, message_log, mouse, game_state, colors)

        fov_recompute = False

        libtcod.console_flush()

        clear_all(con, entities)

        # Input handling
        action = handle_keys(key, game_state)

        move = action.get('move')
        exit = action.get('exit')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        fullscreen = action.get('fullscreen')

        player_turn_results = []

        # Movement handling
        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            dest_x = player.x + dx
            dest_y = player.y + dy

            if not game_map.is_blocked(dest_x, dest_y):
                target = get_blocking_entities_at_location(entities, dest_x, dest_y)

                if target:
                    attack_results = player.fighter.attack(target)
                    player_turn_results.extend(attack_results)
                else:
                    player.move(dx, dy)
                    fov_recompute = True

            game_state = GameStates.ENEMY_TURN
        # Pickup handling
        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)

                    break
            else:
                message_log.add_message(Message('There is nothing here to pickup', libtcod.yellow))

        # Menus display handling
        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY
        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        # Items usage handling
        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]
            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if exit:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
                game_state = previous_game_state
            else:
                return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)

        # Print turn results
        for p_t_result in player_turn_results:
            message = p_t_result.get('message')
            dead_entity = p_t_result.get('dead')
            item_added =p_t_result.get('item_added')
            item_consumed = p_t_result.get('item_consumed')
            item_dropped = p_t_result.get('item_dropped')

            if message:
                message_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)
                message_log.add_message(message)

            if item_added:
                entities.remove(item_added)
                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)
                game_state = GameStates.ENEMY_TURN

        # ENEMIES TURN
        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

                    for e_t_result in enemy_turn_results:
                        message = e_t_result.get('message')
                        dead_entity = e_t_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break
                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                game_state = GameStates.PLAYERS_TURN

if __name__ == "__main__":
    main()