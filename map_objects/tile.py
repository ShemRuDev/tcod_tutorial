class Tile:
    """
    A tile on a map. May block movement, may block sight
    """
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # by default it is also block sight
        if block_sight == None:
            block_sight = blocked

        self.block_sight = block_sight

        self.explored = False