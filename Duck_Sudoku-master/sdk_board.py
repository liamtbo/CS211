"""
CIS 211
Feb 12, 2023
Project sudoku
Liam Bouffard
"""

"""
A Sudoku board holds a matrix of tiles.
Each row and column and also sub-blocks
are treated as a group (sometimes calles
a 'nonet'); when solved, each group must 
contain exactly one occurrence of each of 
the symbol choices
"""

from sdk_config import CHOICES, UNKNOWN, ROOT
from sdk_config import NROWS, NCOLS
import enum
from typing import List, Sequence, Set

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# log.setLevel(logging.INFO) # if we don't want so many messages

# --------------------------------
#  The events for MVC
# --------------------------------

class Event(object):
    """Abstract base class of all events, both for MVC
    and for other purposes.
    """
    pass

# ---------------------
# Listerners (base class)
# ---------------------

class Listener(object):
    """Abstract base class for listeners.
    Subclass this to make the notification do
    something useful.
    """

    def __init__(self):
        """Default constructor for simple listeners without state"""
        pass

    def notify(self, event: Event):
        """The 'notify' method of the base class must be
        overridden in concrete classes.
        """
        raise NotImplementedError("You must override Listener.notify")


# -------------------------
# Events and listeners for Tile objects
# -------------------------

class EventKind(enum.Enum):
    TileChanged = 1
    TileGuessed = 2

class TileEvent(Event):
    """Abstract base class for things that happen to tiles.
    We always indicate the tile. Concrete subclasses indicate
    the nature of the event"""

    def __init__(self, tile: 'Tile', kind: EventKind):
        self.tile = tile
        self.kind = kind
        # Note 'Tile' type is a forward reference;
        # Tile class is defined below

    def __str__(self):
        """Printed representation includes name of concrete subclass"""
        return f"{repr(self.tile)}"
    

class TileListener(Listener):
    def notify(self, event: TileEvent):
        raise NotImplementedError(
            "TileListener subclass needs to override notify(TileEvent)")
    

class Listenable:
    """Objects to which listerners (like a view component) can be attached"""

    def __init__(self):
        self.listeners = []

    def add_listener(self,listener: Listener):
        self.listeners.append(listener)

    def notify_all(self, event: Event):
        for listener in self.listeners:
            listener.notify(event)

# ---------------------------------------------
#   Tile class
# ---------------------------------------------

class Tile(Listenable):
    """One tile on the Sodoku grid.
    Public attributes (read-only): value, which will be either
    UNKNOWN or an element of CHOICES; candidates, which will
    be a set drawn from CHOICES. If the value is an element of
    CHOICES, then candidates will be the singleton containing
    value. If candidates is empty, then no tile value can
    be consistent with other tile values in the grid.
    value is a public read-only attribute; change it
    only through the acess method set_value of indirectly
    through method remove_candidates.
    """

    def __init__(self, row: int, col: int, value=UNKNOWN):
        super().__init__()
        assert value == UNKNOWN or value in CHOICES
        self.row = row
        self.col = col
        self.value = value
        if self.value == UNKNOWN:
            self.candidates = set(CHOICES)
        else:
            self.candidates = { value }

    def __hash__(self) -> int:
        """Hash on position only (not value)"""
        return hash((self.row, self.col))
    
    def set_value(self, value: str):
        """sets the value of the tile"""
        if value in CHOICES:
            self.value = value
            self.candidates = {value}
        else:
            self.value = UNKNOWN
            self.candidates = set(CHOICES)
        self.notify_all(TileEvent(self, EventKind.TileChanged))

    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Tile({self.row}, {self.col}, '{self.value}')"
    
    def could_be(self, value: str) -> bool:
        """True if value is a candidate value for this tile"""
        return value in self.candidates
    
    def remove_candidates(self, used_values: Set[str]) -> bool:
        """The used values cannot be a value of this unknown tile.
        We removes those possibilities from the list of candidates.
        If there is exactly one candidate left, we set the
        value of the tile.
        Returns: True means we eliminated at least oone candidate,
        False mean nothing changed (none of the 'used_values' was
        in out candidates set).
        """
        # difference returns the values from the first set thatt aren't in the second.
        new_candidates = self.candidates.difference(used_values) # problem is im passing tile objects for used_values
        if new_candidates == self.candidates:
            # Didn't remove any candidates
            return False
        self.candidates = new_candidates
        if len(self.candidates) == 1:
            self.set_value(new_candidates.pop())
        self.notify_all(TileEvent(self, EventKind.TileChanged))
        return True
    
    

# ------------------------------
# Board class
# ------------------------------

class Board(object):
    """A board has a matrix of tiles"""

    def __init__(self):
        """The empty board"""
        # Row/Column structure: Each row contains columns
        self.tiles: List[List[Tile]] = [ ]
        for row in range(NROWS):
            cols = [ ]
            for col in range(NCOLS):
                cols.append(Tile(row, col))
            self.tiles.append(cols)

        # building groups
        self.groups: List[List[Tile]] = [ ]
        for row in self.tiles:
            self.groups.append(row)
        # col groups
        for col_i in range(len(self.tiles[0])):
            sub_group = []
            for row_i in range(len(self.tiles)):
                sub_group.append(self.tiles[row_i][col_i])
            self.groups.append(sub_group)
        # for blocks with width and height of root value
        for block_row in range(ROOT):
            for block_col in range(ROOT):
                group = [ ]
                for row in range(ROOT):
                    for col in range(ROOT):
                        row_addr = (ROOT * block_row) + row
                        col_addr = (ROOT * block_col) + col
                        group.append(self.tiles[row_addr][col_addr])
                self.groups.append(group)
        

    def set_tiles(self, tile_values: Sequence[Sequence[str]]):
        """Set the tile values a list of lists or a list of string"""
        for row_num in range(NROWS):
            for col_num in range(NCOLS):
                tile = self.tiles[row_num][col_num]
                tile.set_value(tile_values[row_num][col_num])

    def __str__(self) -> str:
        """In Sadmn Sudoku format"""
        return "\n".join(self.as_list())
    
    def as_list(self) -> List[str]:
        """Tile values in a format compatible with
        set_tiles.
        """
        row_syms = []
        for row in self.tiles:
            values = [tile.value for tile in row]
            row_syms.append("".join(values))
        return row_syms
    
    def is_consistent(self) -> bool:
        """detects duplicate values in rows, columns, or blocks"""
        for group in self.groups:
            used_symbols = set()
            for tile in group:
                if tile.value in CHOICES:
                    if tile.value in used_symbols:
                        return False
                    else:
                        used_symbols.add(tile.value)
        return True
    
    def naked_single(self) -> bool:
        """Eliminate candidates and check for sole remaining possibilities.
        Return value True means we crossed off at least one candidate.
        Return value False means we made no progress.
        """
        t_or_f = []
        for group in self.groups:
            used_values = set()
            for tile in group:
                if tile.value in CHOICES:
                    used_values.add(tile.value)
            for tile in group:
                if tile.value == UNKNOWN:
                    t_or_f.append(tile.remove_candidates(used_values))
        if True in t_or_f:
            return True
        return False

    def hidden_single(self) -> bool:
        """if a candidate for a tile in group can't be anywhere
        else, the tile.value is set to that candidate"""
        t_f = []
        for group in self.groups:
            leftovers = set(CHOICES)
            for tile in group:
                if tile.value in CHOICES:
                    leftovers.discard(tile.value)
            for num in leftovers:
                num_count = 0
                tile_tracker = []
                for tile in group:
                    if num in tile.candidates:
                        num_count += 1
                        tile_tracker.append(tile)
                if num_count == 1: 
                    tile_tracker[0].set_value(num)
                    t_f.append(True)
        if True in t_f:
            return True
        return False
    
    def min_choice_tile(self) -> Tile:
        """Returns a tile with value UNKNOWN and
        minimum number of candidates.
        Precondition: There is at least one tile
        with value UKNOWN.
        """
        candidate_count = 99999999
        lowest_count_tile = None
        for row_i in range(len(self.tiles)):
            for col_i in range(len(self.tiles[0])):
                cur_tile = self.tiles[row_i][col_i]
                if cur_tile.value == UNKNOWN:
                    if len(cur_tile.candidates) < candidate_count:
                        candidate_count = len(cur_tile.candidates)
                        lowest_count_tile = cur_tile
        if lowest_count_tile != None:
            return lowest_count_tile

    def propogate(self):
        """Repeat solution tactics until we
        don't make any progrerss, whether"""
        progress = True
        while progress:
            progress = self.naked_single()
            self.hidden_single()
        return

    def is_complete(self) -> bool:
        """None of the tiles are UNKNOWN.
        Note: Does not check consistency; do that
        separetely with is_consistent"""
        for row in self.tiles:
            for tile in row:
                if tile.value not in CHOICES:
                    return False
        return True

    def solve(self):
        """General solver; guess-and-check
        combined with constaint propogation.
        """
        self.propogate()
        if self.is_complete():
            return True
        elif not self.is_consistent():
            return False
        else:
            saved = self.as_list()
            guess_tile = self.min_choice_tile()
            for candidate in guess_tile.candidates:
                guess_tile.set_value(candidate)
                if self.solve():
                    return True
                else:
                    self.set_tiles(saved)
            return False
                
    


