import tcod as libtcod

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
            'consumed': False,
            'message': Message('You already at full health!', libtcod.yellow)
        })
    else:
        entity.fighter.heal(amount)
        results.append({
            'consumed': True,
            'message': Message('Your wounds start to feel better', libtcod.green)
        })

    return results