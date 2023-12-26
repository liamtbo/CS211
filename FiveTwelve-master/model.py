"""
CIS 211
FIVETWELVE project
Liam Bouffard
Jan 22, 2023"""

"""
The game state and logic (model component) of 512, 
a game based on 2048 with a few changes. 
This is the 'model' part of the model-view-controller
construction plan.  It must NOT depend on any
particular view component, but it produces event 
notifications to trigger view updates. 
"""

from game_element import GameElement, GameEvent, EventKind
from typing import List, Tuple, Optional
import random

# Configuration constants
GRID_SIZE = 4

class Vec():
    """A Vec is an (x,y) or (row, column) pair that
    represents distance along two orthogonal axes.
    Interpreted as a position, a Vec represents
    distance from (0,0).  Interpreted as movement,
    it represents distance from another position.
    Thus we can add two Vecs to get a Vec.
    """
    #Fixme:  We need a constructor, and __add__ method, and __eq__.
    def __init__(self, x:int, y:int) -> None: 
        self.x = x
        self.y = y

    def __add__(self, other: "Vec") -> "Vec":
        add_x = self.x + other.x
        add_y = self.y + other.y
        return Vec(add_x, add_y)

    def __eq__(self, other: "Vec") -> bool:
        return self.x == other.x and self.y == other.y



class Tile(GameElement):
    """A slidy numbered thing."""

    def __init__(self, pos: Vec, value: int):
        super().__init__()
        self.row = pos.x
        self.col = pos.y
        self.value = value
    
    def __repr__(self):
        """Not like constructorr --- more useful for debugging"""
        return f"Tile[{self.row},{self.col}]:{self.value}"
    
    def __str__(self):
        return str(self.value)

    def move_to(self, new_pos: Vec):
        self.row = new_pos.x
        self.col = new_pos.y
        self.notify_all(GameEvent(EventKind.tile_updated, self))

    def __eq__(self, other: "Tile"):
        return self.value == other.value

    def merge(self, other: "Tile"):
        # This tile incorporates the value of the other tile
        self.value = self.value + other.value
        self.notify_all(GameEvent(EventKind.tile_updated, self))
        # The other tile has been absorbed.  Resistance was futile.
        other.notify_all(GameEvent(EventKind.tile_removed, other))



class Board(GameElement):
    """The game grid.  Inherits 'add_listener' and 'notify_all'
    methods from game_element.GameElement so that the game
    can be displayed graphically.
    """

    def __init__(self, rows=4, cols=4):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.tiles = []
        for row in range(rows):
            row_tiles = []
            for col in range(cols):
                row_tiles.append(None)
            self.tiles.append(row_tiles)

    def __getitem__(self, pos: Vec) -> Tile:
        return self.tiles[pos.x][pos.y]
    
    def __setitem__(self, pos: Vec, tile: Tile):
        self.tiles[pos.x][pos.y] = tile

    def _empty_positions(self) -> List[Vec]: # leading underscore means this is a priate method only to be used by board class
        """Return a list of positions of None values,
        i.e., unoccupied spaces."""
        empties = []
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles[row])):
                if self.tiles[row][col] is None:
                    empties.append(Vec(row, col))
        return empties


    def has_empty(self) -> bool:
        """Is there at least one grid element without a tile?"""
        if len(self._empty_positions()) > 0:
            return True
        return False

    def place_tile(self, value=None):
        """Place a tile on a randomly chosen empty square."""
        empties = self._empty_positions()
        assert len(empties) > 0
        choice = random.choice(empties)
        row, col = choice.x, choice.y
        if value is None:
            # 0.1 probability of 4
            if random.random() > 0.1:
                value = 2
            else:
                value = 4
        # update tile with new value
        # notifying the view component that the display needs to update
        new_tile = Tile(Vec(row, col), value)
        self.tiles[row][col] = new_tile
        self.notify_all(GameEvent(EventKind.tile_created, new_tile))

    def to_list(self) -> List[List[int]]:
        """Test scaffolding: represent each Tile by its
        interger value and empty positions as 0"""
        result = []
        for row in self.tiles:
            row_values = []
            for col in row:
                if col is None:
                    row_values.append(0)
                else:
                    row_values.append(col.value)
            result.append(row_values)
        return result

    def from_list(self, values: List[List[int]]):
        """Test scaffolding: set board tiles to the given values,
        where 0 represents an empty space"""
        for row_i in range(len(values)):
            for col_i in range(len(values[0])):
                v = Vec(row_i, col_i)
                values_cur_val = values[row_i][col_i]
                if values_cur_val == 0:
                    self.tiles[row_i][col_i] = None
                else:
                    t = Tile(v, values_cur_val)
                    self.__setitem__(v, t)

    def in_bounds(self, pos: Vec) -> bool:
        """Is position (pos.x, pos.y) a legal position on the board?"""
        x_inside = pos.x >= 0 and pos.x <= self.rows - 1
        y_inside = pos.y >= 0 and pos.y <= self.cols - 1
        return x_inside and y_inside

    def slide(self, pos: Vec,  dir: Vec):
        """Slide tile at row,col (if any)
        in direction (dx,dy) until it bumps into
        another tile or the edge of the board.
        """
        if self[pos] is None: #the [] works here bc we redefined the magic methods __getitem__ and __setitem__ above
            return
        while True:
            new_pos = pos + dir
            if not self.in_bounds(new_pos):
                break
            if self[new_pos] is None:
                self._move_tile(pos, new_pos)
            elif self[pos] == self[new_pos]:
                self[pos].merge(self[new_pos])
                self._move_tile(pos, new_pos)
                break  # Stop moving when we merge with another tile
            else:
                # Stuck against another tile
                break
            pos = new_pos
        
    def _move_tile(self, old_pos: Vec, new_pos: Vec):
        if self[new_pos] is not None:
            self[old_pos].move_to(new_pos)
            self.__setitem__(new_pos, self[old_pos])
            self.tiles[old_pos.x][old_pos.y] = None

        else:
            self.__setitem__(new_pos, self[old_pos])
            self.tiles[old_pos.x][old_pos.y] = None
            self[new_pos].row = new_pos.x
            self[new_pos].col = new_pos.y
            self[new_pos].notify_all(GameEvent(EventKind.tile_updated, self[new_pos]))


    def right(self):
        """move the tiles to the right starting with
        the rightmost"""
        for row_i in range(len(self.tiles)):
            for col_i in reversed(range(len(self.tiles))):
                self.slide(Vec(row_i, col_i), Vec(0, 1))

    def left(self):
        """move the tiles to the left starting with
        the leftmost"""
        for row_i in range(len(self.tiles)):
            for col_i in range(len(self.tiles)):
                self.slide(Vec(row_i, col_i), Vec(0, -1))

    def up(self):
        """move the tiles up starting with
        the upmost"""
        for col_i in range(self.cols):
            for row_i in range(len(self.tiles)):
                self.slide(Vec(row_i, col_i), Vec(-1, 0))
      
            
    def down(self):
        """move the tiles down starting with
        the downmost"""
        for col_i in range(self.cols):
            for row_i in reversed(range(len(self.tiles))):
                self.slide(Vec(row_i, col_i), Vec(1, 0))
            

    def score(self) -> int: # potentially not done
        """Calculate a score from the board.
        (Differs from classic 1024, which calculates score
        based on sequence of moves rather than state of
        board.
        """
        score_sum = 0
        b_list = self.to_list()
        for row in b_list:
            for val in row:
                score_sum += val
        return score_sum
        # return 0


