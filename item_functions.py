import tcod as libtcod

from components.ai import ConfusedMonster

from game_messages import Message

def itm_heal(*args, **kwargs):
    """
    0 - Entity to heal \n
    kwargs:\n
    'amount' - integer value to heal
    """
    entity = args[0]
    amount = kwargs.get('amount')

    results = []

    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({
            'item_consumed': False,
            'message': Message('You already at full health!', libtcod.yellow)
        })
    else:
        entity.fighter.heal(amount)
        results.append({
            'item_consumed': True,
            'message': Message('Your wounds start to feel better', libtcod.green)
        })

    return results

def cast_lightning(*args, **kwargs):
    """
    0 - caster\n
    kwargs:\n
    'entities' - entities to find closest\n
    'fov_map' - we need only those who in FOV\n
    'damage' - cast damage\n
    'maximum_range' - cast range
    """
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')

    results = []

    target = None
    closest_distance = maximum_range + 1

    for entity in entities:
        if entity.fighter and entity != caster and libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
            distance = caster.distance_to(entity)

            if distance < closest_distance:
                target = entity
                closest_distance = distance

    if target:
        results.append({
            'item_consumed': True,
            'target': target,
            'message': Message('A lightning bolt strikes {0}. Damage is {1}'.format(target.name, damage))
        })
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({
            'item_consumed': False,
            'target': None,
            'message': Message('No enemy is close enough to strike', libtcod.yellow)
        })

    return results

def cast_fireball(*args, **kwargs):
    """
    kwargs:\n
    'entities' - all entities\n
    'fov_map' - we need only those who in FOV\n
    'damage' - cast damage\n
    'radius' - explosion radius\n
    'target_x' - target x coord
    'target_y' - target y coord
    """
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({
            'item_consumed': False,
            'message': Message('You cannot target a tile outside view', libtcod.yellow)
        })

    results.append({
        'item_consumed': True,
        'message': Message('The Fireball explodes, burning everything within {0} radius!'.format(radius), libtcod.orange)
    })

    for entity in entities:
        if entity.distance(target_x, target_y) <= radius and entity.fighter:
            results.append({
                'message': Message('The {0} gets burned for {1} hit points'.format(entity.name, damage), libtcod.orange)
            })
            results.extend(entity.fighter.take_damage(damage))

    return results

def cast_confusion(*args, **kwargs):
    """
    kwargs:\n
    'entities' - all entities\n
    'fov_map' - we need only those who in FOV\n
    'target_x' - target x coord
    'target_y' - target y coord
    """
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({
            'item_consumed': False,
            'message': Message('You cannot target a tile outside your field of view.', libtcod.yellow)
        })

    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai_comp = ConfusedMonster(entity.ai, 10)

            confused_ai_comp.owner = entity
            entity.ai = confused_ai_comp

            results.append({
                'item_consumed': True,
                'message': Message('The eyes of the {0} look vacant, as he starts to stumble around!'.format(entity.name), libtcod.light_green)
            })

            break
    else:
        results.append({'item_consumed': False, 'message': Message('There is no targetable enemy at that location.', libtcod.yellow)})

    return results