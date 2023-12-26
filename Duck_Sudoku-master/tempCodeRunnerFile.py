class TestHiddenSingel(unittest.TestCase):
#     """Test the Hidden Single tactic, which must be combined with the
#     naked single tactic
#     """

#     def test_hidden_single_example(self):
#         """simple example from Sadman Sudoku. Since 2 is blocked
#         in two columns of the board, it must go into the middle
#         column.
#         """
#         board = Board()
#         board.set_tiles([".........", "...2.....",  ".........",
#                          "....6....", ".........",  "....8....",
#                          ".........", ".........", ".....2..."])
#         board.naked_single()
#         board.hidden_single()
#         self.assertEqual(str(board),
#                          "\n".join(
#                         [".........", "...2.....",  ".........",
#                          "....6....", "....2....",  "....8....",
#                          ".........", ".........", ".....2..."]))
        
#     def test_hidden_singel_solve(self):
#         """This puzzle can be solved with naked single
#         and hidden single together.
#         """
#         board = Board()
#         board.set_tiles(["......12.", "24..1....", "9.1..4...",
#                          "4....365.", "....9....", ".364....1",
#                          "...1..5.6", "....5..43", ".72......"])
#         board.solve()
#         self.assertEqual(str(board),
#                          "\n".join(["687539124", "243718965", "951264387",
#                                     "419873652", "725691438", "836425791",
#                                     "394182576", "168957243", "572346819"]))