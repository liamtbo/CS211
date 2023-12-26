"""
CIS 211
Calculator Project
Feb 6, 2023
Liam Bouffard
"""


import math

"""One global enviroment (scope) for
the calculator"""

ENV: dict[str, "IntConst"] = dict()

def env_clear():
    """Clear all variables in calculator memory"""
    global ENV
    ENV = dict()

class Expr(object):
    """Abstract base class of all expressions."""

    def eval(self) -> "IntConst":
        """Implementations of eval should return an integer constant."""
        raise NotImplementedError(
            f"'eval' not implemented in {self.__class__.__name__}\n"
            "Each concrete Expr class must define 'eval'")

    def __str__(self) -> str:
        """Implementations of __str__ should return the expression in algebraic notation"""
        raise NotImplementedError(
            f"'__str__' not implemented in {self.__class__.__name__}\n"
            "Each concrete Expr class must define '__str__'")

    def __repr__(self) -> str:
        """Implementations of __repr__ should return a string that looks like
        the constructor, e.g., Plus(IntConst(5), IntConst(4))
        """
        raise NotImplementedError(
            f"'__repr__' not implemented in {self.__class__.__name__}\n"
            "Each concrete Expr class must define '__repr__'")

class IntConst(Expr):

    def __init__(self, value: int):
        self.value = value
    
    def eval(self) -> "IntConst":
        return self

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"IntConst({self.value})"

    def __eq__(self, other: Expr):
        return isinstance(other, IntConst) and self.value == other.value


class BinOp(Expr):
    """Abstract base class for binary operations"""
    def __init__(self, left: Expr, right: Expr, symbol: str="?Operational symbol undefine"):
        self.left = left
        self.right = right
        self.symbol = symbol

    def __str__(self) -> str:
        return f"({self.left} {self.symbol} {self.right})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"
    
    def _apply(self, left_val: int, right_val: int) -> int:
        """Each concrete BinOp subclass provides the appropriate method"""
        raise NotImplementedError(
            f"'_apply' not implemented in {self.__class__.__name__}\n"
            "Each concrete BinOP class must define '_apply'")

    def eval(self) -> "IntConst":
        """Each concrete subclass must define _apply(int, int) -> int"""
        left_val = self.left.eval()
        right_val = self.right.eval()
        return IntConst(self._apply(left_val.value, right_val.value))

class Plus(BinOp):
    """left + right"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__(left, right, symbol="+")

    def _apply(self, left: int, right: int) -> int:
        return left + right

class Times(BinOp):
    """left * right"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__(left, right, symbol="*")

    def _apply(self, left: int, right: int) -> int:
        return left * right
    
class Div(BinOp):
    """left // right"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__(left, right, symbol="/")

    def _apply(self, left: int, right: int) -> int:
        return left // right
    
class Minus(BinOp):
    """left - right"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__(left, right, symbol="-")
    
    def _apply(self, left: int, right: int) -> int:
        return left - right


class Unop:
    """Abstract base class for unary operations"""
    def __init__(self, left: Expr, symbol: str="?Operational symbol undefined"):
        self.left = left
        self.symbol = symbol

    def __str__(self) -> str:
        return f"({self.symbol} {self.left})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)})"
    
    def _apply(self, left_val: int) -> int:
        """Each concrete Unop subclass provides the appropriate method"""
        raise NotImplementedError(
            f"'_apply' not implemented in {self.__class__.__name__}\n"
            "Each concrete BinOP class must define '_apply'")
    
    def eval(self) -> "IntConst":
        """Each concrete subclass must define _apply(int) -> int"""
        left_val = self.left.eval()
        return IntConst(self._apply(left_val.value))
    

class Abs(Unop):
    """@x"""
    def __init__(self, left: Expr):
        super().__init__(left, symbol="@")

    def _apply(self, left: int) -> int:
        return abs(left)

class Neg(Unop):
    """~x"""
    def __init__(self, left: Expr):
        super().__init__(left, symbol ="~")

    def _apply(self, left: int) -> int:
        return -(left)
    
class UndefinedVariable(Exception):
    """Raised when expression tries to use a variable
    that is not in ENV"""
    pass

class Var(Expr):
    """for creating a variable"""
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Var({self.name})"

    def eval(self):
        global ENV
        if self.name in ENV:
            return ENV[self.name]
        else:
            raise UndefinedVariable(f"{self.name} has not been assigned a value")
        
    def assign(self, value: IntConst):
        ENV[self.name] = value

class Assign(Expr):
    """Assignment:  x = E represented as Assign(x, E)"""
    
    def __init__(self, left: Var, right: Expr):
        assert isinstance(left, Var)  # Can only assign to variables! 
        self.left = left
        self.right = right

    def eval(self) -> IntConst: 
        r_val = self.right.eval()
        self.left.assign(r_val)
        return r_val
    
    def __str__(self) -> str:
        return f"({self.left} = {self.right})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"

# v = Var("v")
# w = Var("w")
# exp = Assign(v, Plus(IntConst(5), w))
# print(exp)
# print(repr(exp))
