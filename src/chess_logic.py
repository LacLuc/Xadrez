import copy
import random
from PIL import Image
import pygame
import os

piece_icons = {}

def load_piece_icons():
    # Initialize a hidden display to allow convert_alpha()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    for color in ['w', 'b']:
        for p in "KQRBNP":
            img = pygame.image.load(os.path.join('assets', f'{color}{p}.png')).convert_alpha()
            piece_icons[f'{color}{p}'] = pygame.transform.smoothscale(img, (80, 80))

load_piece_icons()

class Piece:
    def __init__(self, color, kind):
        self.color = color
        self.kind = kind
        self.has_moved = False

    def __str__(self):
        return f"{self.color}{self.kind}"

class Move:
    def __init__(self, from_row, from_col, to_row, to_col, promotion=None, is_castling=False):
        self.from_row = from_row
        self.from_col = from_col
        self.to_row = to_row
        self.to_col = to_col
        self.promotion = promotion
        self.is_castling = is_castling

    def __repr__(self):
        return f"Move({self.from_row},{self.from_col}->{self.to_row},{self.to_col})"

class ChessBoard:
    def __init__(self):
        # 8x8 board
        # row 0 is top, white at bottom
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.turn = 'w'
        self.history = []
        self._setup_board()
        self.wk_castle = self.bk_castle = self.wq_castle = self.bq_castle = True
        self.en_passant = None
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def _setup_board(self):
        # Place pieces
        for i in range(8):
            self.board[1][i] = Piece('b', 'P')
            self.board[6][i] = Piece('w', 'P')
        setup = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for i, k in enumerate(setup):
            self.board[0][i] = Piece('b', k)
            self.board[7][i] = Piece('w', k)

    def piece_at(self, row, col):
        return self.board[row][col]

    def get_legal_moves(self, row, col):
        piece = self.piece_at(row, col)
        if not piece or piece.color != self.turn:
            return []
        moves = []
        if piece.kind == 'P':
            moves += self._pawn_moves(row, col)
        elif piece.kind == 'N':
            moves += self._knight_moves(row, col)
        elif piece.kind == 'B':
            moves += self._bishop_moves(row, col)
        elif piece.kind == 'R':
            moves += self._rook_moves(row, col)
        elif piece.kind == 'Q':
            moves += self._queen_moves(row, col)
        elif piece.kind == 'K':
            moves += self._king_moves(row, col)
        # Remove moves that leave king in check
        legal = []
        for m in moves:
            board_copy = copy.deepcopy(self)
            board_copy.push(m)
            if not board_copy.in_check(self.turn):
                legal.append(m)
        return legal

    def get_all_legal_moves_for(self, col, row):
        # For UI: get all legal moves for a piece
        return self.get_legal_moves(row, col)

    def _pawn_moves(self, row, col):
        moves = []
        piece = self.piece_at(row, col)
        dir = -1 if piece.color == 'w' else 1
        # Move 1 forward
        if self._on_board(row+dir, col) and not self.piece_at(row+dir, col):
            # Promotion
            if (piece.color == 'w' and row+dir == 0) or (piece.color == 'b' and row+dir == 7):
                moves.append(Move(row, col, row+dir, col, promotion='Q'))
            else:
                moves.append(Move(row, col, row+dir, col))
            # Move 2 forward
            if ((piece.color == 'w' and row == 6) or (piece.color == 'b' and row == 1)) and not self.piece_at(row+2*dir, col):
                moves.append(Move(row, col, row+2*dir, col))
        # Capture
        for dc in [-1, 1]:
            nr, nc = row+dir, col+dc
            if self._on_board(nr, nc):
                target = self.piece_at(nr, nc)
                if target and target.color != piece.color:
                    if (piece.color == 'w' and nr == 0) or (piece.color == 'b' and nr == 7):
                        moves.append(Move(row, col, nr, nc, promotion='Q'))
                    else:
                        moves.append(Move(row, col, nr, nc))
        # En passant
        if self.en_passant:
            er, ec = self.en_passant
            if abs(ec - col) == 1 and er == row+dir:
                moves.append(Move(row, col, er, ec))
        return moves

    def _knight_moves(self, row, col):
        moves = []
        deltas = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        piece = self.piece_at(row, col)
        for dr, dc in deltas:
            nr, nc = row+dr, col+dc
            if self._on_board(nr, nc):
                target = self.piece_at(nr, nc)
                if not target or target.color != piece.color:
                    moves.append(Move(row, col, nr, nc))
        return moves

    def _bishop_moves(self, row, col):
        moves = []
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            moves += self._slide_moves(row, col, dr, dc)
        return moves

    def _rook_moves(self, row, col):
        moves = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            moves += self._slide_moves(row, col, dr, dc)
        return moves

    def _queen_moves(self, row, col):
        return self._rook_moves(row, col)+self._bishop_moves(row, col)

    def _king_moves(self, row, col):
        moves = []
        piece = self.piece_at(row, col)
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                nr, nc = row+dr, col+dc
                if self._on_board(nr, nc):
                    target = self.piece_at(nr, nc)
                    if not target or target.color != piece.color:
                        moves.append(Move(row, col, nr, nc))
        # Castling
        if piece.color == 'w' and row == 7 and col == 4:
            if self.wk_castle and all(self.piece_at(7, c) is None for c in [5,6]):
                if not self.in_check('w') and not self.square_attacked(7,5,'b') and not self.square_attacked(7,6,'b'):
                    moves.append(Move(7,4,7,6,is_castling=True))
            if self.wq_castle and all(self.piece_at(7, c) is None for c in [1,2,3]):
                if not self.in_check('w') and not self.square_attacked(7,2,'b') and not self.square_attacked(7,3,'b'):
                    moves.append(Move(7,4,7,2,is_castling=True))
        if piece.color == 'b' and row == 0 and col == 4:
            if self.bk_castle and all(self.piece_at(0, c) is None for c in [5,6]):
                if not self.in_check('b') and not self.square_attacked(0,5,'w') and not self.square_attacked(0,6,'w'):
                    moves.append(Move(0,4,0,6,is_castling=True))
            if self.bq_castle and all(self.piece_at(0, c) is None for c in [1,2,3]):
                if not self.in_check('b') and not self.square_attacked(0,2,'w') and not self.square_attacked(0,3,'w'):
                    moves.append(Move(0,4,0,2,is_castling=True))
        return moves

    def _slide_moves(self, row, col, dr, dc):
        moves = []
        piece = self.piece_at(row, col)
        nr, nc = row+dr, col+dc
        while self._on_board(nr, nc):
            target = self.piece_at(nr, nc)
            if not target:
                moves.append(Move(row, col, nr, nc))
            else:
                if target.color != piece.color:
                    moves.append(Move(row, col, nr, nc))
                break
            nr += dr
            nc += dc
        return moves

    def _on_board(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8

    def in_check(self, color):
        # Find king
        for row in range(8):
            for col in range(8):
                p = self.piece_at(row, col)
                if p and p.color == color and p.kind == 'K':
                    king_row, king_col = row, col
        opp = 'b' if color == 'w' else 'w'
        return self.square_attacked(king_row, king_col, opp)

    def square_attacked(self, row, col, attacker_color):
        # For each piece of attacker_color, check if can move to (row, col)
        for r in range(8):
            for c in range(8):
                p = self.piece_at(r, c)
                if p and p.color == attacker_color:
                    for m in self._pseudo_moves(r, c):
                        if (m.to_row, m.to_col) == (row, col):
                            return True
        return False

    def _pseudo_moves(self, row, col):
        # Moves without check validation, for attack detection
        piece = self.piece_at(row, col)
        if not piece:
            return []
        if piece.kind == 'P':
            moves = []
            dir = -1 if piece.color == 'w' else 1
            for dc in [-1, 1]:
                nr, nc = row+dir, col+dc
                if self._on_board(nr, nc):
                    moves.append(Move(row, col, nr, nc))
            return moves
        elif piece.kind == 'N':
            return self._knight_moves(row, col)
        elif piece.kind == 'B':
            return self._bishop_moves(row, col)
        elif piece.kind == 'R':
            return self._rook_moves(row, col)
        elif piece.kind == 'Q':
            return self._queen_moves(row, col)
        elif piece.kind == 'K':
            moves = []
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    if dr==0 and dc==0: continue
                    nr, nc = row+dr, col+dc
                    if self._on_board(nr, nc):
                        moves.append(Move(row, col, nr, nc))
            return moves
        return []

    def push(self, move):
        piece = self.piece_at(move.from_row, move.from_col)
        self.history.append((copy.deepcopy(self.board), self.turn, self.wk_castle, self.wq_castle, self.bk_castle, self.bq_castle, self.en_passant))
        # Castling
        if move.is_castling and piece.kind == 'K':
            if move.to_col == 6:
                # king-side
                self.board[move.to_row][4] = None
                self.board[move.to_row][6] = piece
                self.board[move.to_row][7], self.board[move.to_row][5] = None, self.board[move.to_row][7]
            elif move.to_col == 2:
                # queen-side
                self.board[move.to_row][4] = None
                self.board[move.to_row][2] = piece
                self.board[move.to_row][0], self.board[move.to_row][3] = None, self.board[move.to_row][0]
            piece.has_moved = True
            if piece.color == 'w':
                self.wk_castle = self.wq_castle = False
            else:
                self.bk_castle = self.bq_castle = False
        else:
            # Pawn promotion
            if piece.kind == 'P' and move.promotion and (move.to_row == 0 or move.to_row == 7):
                self.board[move.from_row][move.from_col] = None
                self.board[move.to_row][move.to_col] = Piece(piece.color, move.promotion)
            else:
                self.board[move.from_row][move.from_col] = None
                # En passant
                if piece.kind == 'P' and self.en_passant and (move.to_row, move.to_col) == self.en_passant:
                    dir = -1 if piece.color == 'w' else 1
                    self.board[move.to_row-dir][move.to_col] = None
                self.board[move.to_row][move.to_col] = piece
            piece.has_moved = True
            # Update castling rights
            if piece.kind == 'K':
                if piece.color == 'w': self.wk_castle = self.wq_castle = False
                else: self.bk_castle = self.bq_castle = False
            if piece.kind == 'R':
                if move.from_row == 7 and move.from_col == 0: self.wq_castle = False
                if move.from_row == 7 and move.from_col == 7: self.wk_castle = False
                if move.from_row == 0 and move.from_col == 0: self.bq_castle = False
                if move.from_row == 0 and move.from_col == 7: self.bk_castle = False
        # Update en passant
        if piece.kind == 'P' and abs(move.to_row - move.from_row) == 2:
            self.en_passant = ((move.from_row + move.to_row)//2, move.from_col)
        else:
            self.en_passant = None
        self.turn = 'b' if self.turn == 'w' else 'w'

    def is_game_over(self):
        for r in range(8):
            for c in range(8):
                p = self.piece_at(r, c)
                if p and p.color == self.turn and self.get_legal_moves(r, c):
                    return False
        if self.in_check(self.turn):
            return True
        return True

    def get_winner(self):
        if self.in_check(self.turn):
            return 'Brancas' if self.turn == 'b' else 'Pretas'
        else:
            return 'Empate'

class ChessAI:
    def __init__(self, color):
        self.color = color

    def choose_move(self, board):
        # MiniMax 1-ply with capture priority
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.piece_at(r, c)
                if p and p.color == self.color:
                    moves += board.get_legal_moves(r, c)
        if not moves:
            return None
        # Prefer captures
        capture_moves = [m for m in moves if board.piece_at(m.to_row, m.to_col)]
        if capture_moves:
            return random.choice(capture_moves)
        return random.choice(moves)

    def choose_best_move(self, board, row, col):
        # For virtual assist: Suggest best move for piece at (row, col)
        moves = board.get_legal_moves(row, col)
        if not moves:
            return None
        # Prefer captures
        capture_moves = [m for m in moves if board.piece_at(m.to_row, m.to_col)]
        if capture_moves:
            return capture_moves[0]
        return moves[0]