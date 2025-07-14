import pygame
import sys
from chess_logic import ChessBoard, ChessAI, Move, piece_icons
from ui import draw_board, draw_menu, draw_possible_moves, draw_suggestion, draw_end_screen, COLOR_THEMES

pygame.init()
pygame.display.set_caption("Xadrez Completo Python")

WIDTH, HEIGHT = 700, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()
FPS = 60

def main():
    # Menu inicial
    while True:
        player_color, vs_ai, color_theme, assist_mode = draw_menu(SCREEN, WIDTH, HEIGHT)
        if player_color is None:
            pygame.quit()
            sys.exit()

        board = ChessBoard()
        ai = ChessAI('b' if player_color == 'w' else 'w') if vs_ai else None
        running = True
        selected = None
        possible_moves = []
        suggestion = None
        dragging = False
        drag_offset = (0, 0)
        drag_piece = None
        virtual_assist = assist_mode

        current_color = 'w'
        winner = None
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    row, col = screen_to_board(x, y, WIDTH, HEIGHT)
                    if row is not None and col is not None and board.turn == player_color:
                        # Assistente antes do clique
                        if virtual_assist:
                            moves = board.get_all_legal_moves_for(col, row)
                            draw_possible_moves(SCREEN, moves, WIDTH, HEIGHT, color_theme)
                        # Seleção de peça
                        if board.piece_at(row, col) and board.piece_at(row, col).color == player_color:
                            selected = (row, col)
                            possible_moves = board.get_legal_moves(row, col)
                            dragging = True
                            drag_offset = (x - col * (WIDTH // 8), y - row * (HEIGHT // 8))
                            drag_piece = board.piece_at(row, col)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragging and selected:
                        x, y = pygame.mouse.get_pos()
                        to_row, to_col = screen_to_board(x, y, WIDTH, HEIGHT)
                        if (to_row, to_col) in [(m.to_row, m.to_col) for m in possible_moves]:
                            move = [m for m in possible_moves if (m.to_row, m.to_col) == (to_row, to_col)][0]
                            board.push(move)
                            selected = None
                            dragging = False
                            drag_piece = None
                            possible_moves = []
                            if board.is_game_over():
                                winner = board.get_winner()
                                running = False
                            else:
                                if vs_ai:
                                    # Movimento IA
                                    ai_move = ai.choose_move(board)
                                    if ai_move:
                                        board.push(ai_move)
                                        if board.is_game_over():
                                            winner = board.get_winner()
                                            running = False
                        else:
                            dragging = False
                            drag_piece = None
                            selected = None
                            possible_moves = []
                elif event.type == pygame.MOUSEMOTION:
                    pass

            SCREEN.fill((0, 0, 0))
            draw_board(SCREEN, board, WIDTH, HEIGHT, color_theme, selected, possible_moves, dragging, drag_piece, drag_offset)
            if virtual_assist and not dragging and board.turn == player_color:
                mousex, mousey = pygame.mouse.get_pos()
                mrow, mcol = screen_to_board(mousex, mousey, WIDTH, HEIGHT)
                if mrow is not None and mcol is not None and board.piece_at(mrow, mcol) and board.piece_at(mrow, mcol).color == player_color:
                    moves = board.get_legal_moves(mrow, mcol)
                    draw_possible_moves(SCREEN, moves, WIDTH, HEIGHT, color_theme)
                    suggestion = ChessAI(player_color).choose_best_move(board, mrow, mcol)
                    if suggestion:
                        draw_suggestion(SCREEN, suggestion, WIDTH, HEIGHT)
            pygame.display.flip()
            CLOCK.tick(FPS)

        # Tela final
        draw_end_screen(SCREEN, WIDTH, HEIGHT, winner)
        pygame.time.wait(2000)

def screen_to_board(x, y, w, h):
    size = min(w, h)
    offx = (w - size) // 2
    offy = (h - size) // 2
    if offx <= x < offx + size and offy <= y < offy + size:
        col = (x - offx) // (size // 8)
        row = (y - offy) // (size // 8)
        return int(row), int(col)
    return None, None

if __name__ == "__main__":
    main()