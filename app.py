import pygame
import sys
import os
import random
import copy
import time

# Cores do tabuleiro disponíveis
BOARD_COLORS = {
    "Bege": ((240, 217, 181), (181, 136, 99)),
    "Verde":  ((238, 238, 210), (118, 150, 86)),
    "Azul":   ((230, 230, 255), (80, 120, 185)),    
    "Cinza":  ((220, 220, 220), (120, 120, 120)),
}

# Opções de assistente virtual
ASSISTANTS = [
    "Desligado", "Aleatório", "Agressivo", "Centralizador"
]

BOARD_SIZE = 8
SQUARE_SIZE = 80
MARGIN = 40

pygame.init()
screen = pygame.display.set_mode((BOARD_SIZE * SQUARE_SIZE + MARGIN, BOARD_SIZE * SQUARE_SIZE + MARGIN))
pygame.display.set_caption('Xadrez')

def load_images():
    pieces = ['wK','wQ','wR','wB','wN','wP','bK','bQ','bR','bB','bN','bP']
    images = {}
    for piece in pieces:
        image = pygame.image.load(os.path.join("assets", piece + ".png"))
        images[piece] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
    return images

IMAGES = load_images()

def initial_board():
    return [
        ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
        ["bP"] * 8,
        [""] * 8, [""] * 8, [""] * 8, [""] * 8,
        ["wP"] * 8,
        ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
    ]

def in_board(r, c): return 0 <= r < 8 and 0 <= c < 8

def same_color(p1, p2):
    if not p1 or not p2: return False
    return (p1[0] == p2[0])

def pawn_moves(board, row, col, piece, en_passant, _can_castle):
    moves = []
    direction = -1 if piece[0] == "w" else 1
    start_row = 6 if piece[0] == "w" else 1
    if in_board(row+direction, col) and board[row+direction][col] == "":
        moves.append((row+direction, col))
        if row == start_row and board[row+2*direction][col] == "":
            moves.append((row+2*direction, col))
    for dc in [-1, 1]:
        nr, nc = row+direction, col+dc
        if in_board(nr, nc) and board[nr][nc] and not same_color(piece, board[nr][nc]):
            moves.append((nr, nc))
    if en_passant:
        ep_row, ep_col = en_passant
        if abs(col-ep_col)==1 and row+direction==ep_row:
            moves.append((ep_row, ep_col))
    return moves

def knight_moves(board, row, col, piece, *_):
    moves = []
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = row+dr, col+dc
        if in_board(nr, nc) and (not board[nr][nc] or not same_color(piece, board[nr][nc])):
            moves.append((nr, nc))
    return moves

def bishop_moves(board, row, col, piece, *_):
    moves = []
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        for i in range(1,8):
            nr, nc = row+dr*i, col+dc*i
            if not in_board(nr, nc): break
            if not board[nr][nc]:
                moves.append((nr, nc))
            elif not same_color(piece, board[nr][nc]):
                moves.append((nr, nc))
                break
            else: break
    return moves

def rook_moves(board, row, col, piece, *_):
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        for i in range(1,8):
            nr, nc = row+dr*i, col+dc*i
            if not in_board(nr, nc): break
            if not board[nr][nc]:
                moves.append((nr, nc))
            elif not same_color(piece, board[nr][nc]):
                moves.append((nr, nc))
                break
            else: break
    return moves

def queen_moves(board, row, col, piece, *args):
    return bishop_moves(board, row, col, piece) + rook_moves(board, row, col, piece)

def is_attacked(board, row, col, by_white, en_passant, can_castle):
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and ((p[0]=="w")==by_white):
                moves = get_moves(board, r, c, en_passant, can_castle, ignore_castle=True)
                if (row, col) in moves:
                    return True
    return False

def king_moves(board, row, col, piece, en_passant, can_castle, ignore_castle=False):
    moves = []
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0: continue
            nr, nc = row+dr, col+dc
            if in_board(nr, nc) and (not board[nr][nc] or not same_color(piece, board[nr][nc])):
                moves.append((nr, nc))
    if not ignore_castle and can_castle:
        side = piece[0]
        if can_castle[side]["K"]:
            if side=="w" and row==7 and col==4 and board[7][5]=="" and board[7][6]=="":
                if not is_attacked(board, 7, 4, False, en_passant, can_castle) and \
                   not is_attacked(board, 7, 5, False, en_passant, can_castle) and \
                   not is_attacked(board, 7, 6, False, en_passant, can_castle):
                    moves.append((7,6))
            if side=="b" and row==0 and col==4 and board[0][5]=="" and board[0][6]=="":
                if not is_attacked(board, 0, 4, True, en_passant, can_castle) and \
                   not is_attacked(board, 0, 5, True, en_passant, can_castle) and \
                   not is_attacked(board, 0, 6, True, en_passant, can_castle):
                    moves.append((0,6))
        if can_castle[side]["Q"]:
            if side=="w" and row==7 and col==4 and board[7][3]=="" and board[7][2]=="" and board[7][1]=="":
                if not is_attacked(board, 7, 4, False, en_passant, can_castle) and \
                   not is_attacked(board, 7, 3, False, en_passant, can_castle) and \
                   not is_attacked(board, 7, 2, False, en_passant, can_castle):
                    moves.append((7,2))
            if side=="b" and row==0 and col==4 and board[0][3]=="" and board[0][2]=="" and board[0][1]=="":
                if not is_attacked(board, 0, 4, True, en_passant, can_castle) and \
                   not is_attacked(board, 0, 3, True, en_passant, can_castle) and \
                   not is_attacked(board, 0, 2, True, en_passant, can_castle):
                    moves.append((0,2))
    return moves

def get_moves(board, row, col, en_passant, can_castle, ignore_castle=False):
    piece = board[row][col]
    if not piece: return []
    if piece[1] == "P":
        return pawn_moves(board, row, col, piece, en_passant, can_castle)
    if piece[1] == "N":
        return knight_moves(board, row, col, piece)
    if piece[1] == "B":
        return bishop_moves(board, row, col, piece)
    if piece[1] == "R":
        return rook_moves(board, row, col, piece)
    if piece[1] == "Q":
        return queen_moves(board, row, col, piece)
    if piece[1] == "K":
        return king_moves(board, row, col, piece, en_passant, can_castle, ignore_castle)
    return []

def is_in_check(board, white_turn, en_passant, can_castle):
    king = "wK" if white_turn else "bK"
    king_pos = None
    for r in range(8):
        for c in range(8):
            if board[r][c]==king:
                king_pos = (r, c)
                break
    if not king_pos:
        return True
    return is_attacked(board, king_pos[0], king_pos[1], not white_turn, en_passant, can_castle)

def is_checkmate(board, white_turn, en_passant, can_castle):
    if not is_in_check(board, white_turn, en_passant, can_castle): return False
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and (piece[0]=="w")==white_turn:
                for mr, mc in get_moves(board, r, c, en_passant, can_castle):
                    temp_board = [row[:] for row in board]
                    temp_enp = en_passant
                    temp_castle = copy.deepcopy(can_castle)
                    if valid_move(temp_board, r, c, mr, mc, white_turn, temp_enp, temp_castle):
                        return False
    return True

def valid_move(board, sr, sc, dr, dc, white_turn, en_passant, can_castle):
    piece = board[sr][sc]
    if not piece or (piece[0]=="w")!=white_turn: return False
    if (dr, dc) not in get_moves(board, sr, sc, en_passant, can_castle): return False
    temp_board = [row[:] for row in board]
    temp_enp = en_passant
    temp_castle = copy.deepcopy(can_castle)
    do_move(temp_board, sr, sc, dr, dc, piece, temp_enp, temp_castle)
    if is_in_check(temp_board, white_turn, temp_enp, temp_castle): return False
    return True

def do_move(board, sr, sc, dr, dc, piece, en_passant, can_castle):
    if piece[1]=="K" and abs(dc-sc)==2:
        if dc==6:
            board[dr][dc] = piece; board[sr][sc] = ""
            board[dr][5] = board[dr][7]; board[dr][7] = ""
        elif dc==2:
            board[dr][dc] = piece; board[sr][sc] = ""
            board[dr][3] = board[dr][0]; board[dr][0] = ""
        can_castle[piece[0]]["K"] = False
        can_castle[piece[0]]["Q"] = False
        return
    if piece[1]=="P" and en_passant and (dr, dc)==en_passant:
        board[dr][dc] = piece; board[sr][sc] = ""
        if piece[0]=="w": board[dr+1][dc] = ""
        else: board[dr-1][dc] = ""
        return
    board[dr][dc] = piece; board[sr][sc] = ""
    if piece[1]=="P" and (dr==0 or dr==7):
        board[dr][dc] = piece[0]+"Q"
    if piece[1]=="K":
        can_castle[piece[0]]["K"] = False
        can_castle[piece[0]]["Q"] = False
    if piece[1]=="R":
        if sr==7 and sc==0:
            can_castle["w"]["Q"] = False
        if sr==7 and sc==7:
            can_castle["w"]["K"] = False
        if sr==0 and sc==0:
            can_castle["b"]["Q"] = False
        if sr==0 and sc==7:
            can_castle["b"]["K"] = False

def get_en_passant(sr, sc, dr, dc, piece, board):
    if piece[1]=="P" and abs(dr-sr)==2:
        direction = -1 if piece[0]=="w" else 1
        return (sr+direction, sc)
    return None

def all_legal_moves(board, white_turn, en_passant, can_castle):
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and (piece[0]=="w")==white_turn:
                for mr, mc in get_moves(board, r, c, en_passant, can_castle):
                    if valid_move(board, r, c, mr, mc, white_turn, en_passant, can_castle):
                        moves.append((r, c, mr, mc))
    return moves

def ai_move(board, white_turn, en_passant, can_castle, assistant):
    moves = all_legal_moves(board, white_turn, en_passant, can_castle)
    if not moves: return None
    if assistant == "Desligado":
        return random.choice(moves)
    elif assistant == "Aleatório":
        return random.choice(moves)
    elif assistant == "Agressivo":
        captures = []
        for sr, sc, dr, dc in moves:
            if board[dr][dc] != "":
                captures.append((sr, sc, dr, dc))
        if captures:
            return random.choice(captures)
        return random.choice(moves)
    elif assistant == "Centralizador":
        center = [(3,3),(3,4),(4,3),(4,4)]
        center_moves = [m for m in moves if (m[2],m[3]) in center]
        if center_moves:
            return random.choice(center_moves)
        return random.choice(moves)
    return random.choice(moves)

def assistant_move_suggestion(board, white_turn, en_passant, can_castle, assistant):
    if assistant == "Desligado": return []
    moves = all_legal_moves(board, white_turn, en_passant, can_castle)
    if not moves: return []
    if assistant == "Aleatório":
        return [random.choice(moves)]
    elif assistant == "Agressivo":
        captures = []
        for sr, sc, dr, dc in moves:
            if board[dr][dc] != "":
                captures.append((sr, sc, dr, dc))
        if captures:
            return [random.choice(captures)]
        return [random.choice(moves)]
    elif assistant == "Centralizador":
        center = [(3,3),(3,4),(4,3),(4,4)]
        center_moves = [m for m in moves if (m[2],m[3]) in center]
        if center_moves:
            return [random.choice(center_moves)]
        return [random.choice(moves)]
    # Clássico: destaque todas as jogadas possíveis
    return moves

def draw_board(board, selected=None, moves=[], color1=(238,238,210), color2=(118,150,86), assistant_moves=None):
    font = pygame.font.SysFont(None, 32)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = color1 if (row+col)%2==0 else color2
            rect = pygame.Rect(col*SQUARE_SIZE + MARGIN, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)
            if selected == (row, col):
                pygame.draw.rect(screen, (186,202,43), rect, 5)
            piece = board[row][col]
            if piece:
                screen.blit(IMAGES[piece], (col*SQUARE_SIZE + MARGIN, row*SQUARE_SIZE))
    for mr, mc in moves:
        cx = mc*SQUARE_SIZE + MARGIN + SQUARE_SIZE//2
        cy = mr*SQUARE_SIZE + SQUARE_SIZE//2
        pygame.draw.circle(screen, (90,180,60), (cx, cy), 15)
    # Desenhar sugestões do assistente (em laranja)
    if assistant_moves:
        for sr, sc, dr, dc in assistant_moves:
            cx = dc*SQUARE_SIZE + MARGIN + SQUARE_SIZE//2
            cy = dr*SQUARE_SIZE + SQUARE_SIZE//2
            pygame.draw.circle(screen, (255,128,0), (cx, cy), 17, 4)
    for row in range(BOARD_SIZE):
        num = font.render(str(8-row), True, (0,0,0))
        screen.blit(num, (5, row*SQUARE_SIZE + SQUARE_SIZE//2 - 10))
    for col in range(BOARD_SIZE):
        letter = font.render(chr(ord('a')+col), True, (0,0,0))
        screen.blit(letter, (col*SQUARE_SIZE + MARGIN + SQUARE_SIZE//2 - 10, BOARD_SIZE*SQUARE_SIZE + 5))

def draw_menu(selected_ai, selected_color, board_color, assistant_index):
    screen.fill((50, 50, 50))
    bigfont = pygame.font.SysFont(None, 50)
    font = pygame.font.SysFont(None, 36)
    title = bigfont.render("Xadrez - Menu Inicial", True, (255, 255, 255))
    screen.blit(title, (MARGIN+40, 20))
    ai_txt = "Com IA" if selected_ai else "Dois Jogadores"
    ai_surf = font.render(f"Modo: {ai_txt}", True, (255, 255, 255))
    screen.blit(ai_surf, (MARGIN+40, 90))
    ai_btn_rect = pygame.Rect(MARGIN+40, 85, 270, 45)
    pygame.draw.rect(screen, (150,180,255), ai_btn_rect, 2)
    color_txt = "Brancas" if selected_color=="white" else "Pretas"
    color_surf = font.render(f"Jogar com: {color_txt}", True, (255, 255, 255))
    screen.blit(color_surf, (MARGIN+40, 150))
    color_btn_rect = pygame.Rect(MARGIN+40, 145, 270, 45)
    pygame.draw.rect(screen, (150,180,255), color_btn_rect, 2)
    board_surf = font.render(f"Cor Tabuleiro: {board_color}", True, (255, 255, 255))
    screen.blit(board_surf, (MARGIN+40, 210))
    board_btn_rect = pygame.Rect(MARGIN+40, 205, 270, 45)
    pygame.draw.rect(screen, (150,180,255), board_btn_rect, 2)
    assistant_surf = font.render(f"Assistente: {ASSISTANTS[assistant_index]}", True, (255, 255, 255))
    screen.blit(assistant_surf, (MARGIN+40, 270))
    assistant_btn_rect = pygame.Rect(MARGIN+40, 265, 270, 45)
    pygame.draw.rect(screen, (150,180,255), assistant_btn_rect, 2)
    play_surf = bigfont.render("JOGAR", True, (0,128,0))
    play_btn_rect = pygame.Rect(MARGIN+40, 340, 200, 60)
    pygame.draw.rect(screen, (90,255,90), play_btn_rect)
    screen.blit(play_surf, (MARGIN+70, 350))
    pygame.display.flip()
    return ai_btn_rect, color_btn_rect, board_btn_rect, assistant_btn_rect, play_btn_rect

def menu():
    selected_ai = True
    selected_color = "white"
    board_color = list(BOARD_COLORS.keys())[0]
    assistant_index = 0
    while True:
        ai_btn_rect, color_btn_rect, board_btn_rect, assistant_btn_rect, play_btn_rect = draw_menu(
            selected_ai, selected_color, board_color, assistant_index
        )
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if ai_btn_rect.collidepoint(x,y):
                    selected_ai = not selected_ai
                elif color_btn_rect.collidepoint(x,y):
                    selected_color = "black" if selected_color=="white" else "white"
                elif board_btn_rect.collidepoint(x,y):
                    colors = list(BOARD_COLORS.keys())
                    board_color = colors[(colors.index(board_color)+1)%len(colors)]
                elif assistant_btn_rect.collidepoint(x,y):
                    assistant_index = (assistant_index+1)%len(ASSISTANTS)
                elif play_btn_rect.collidepoint(x,y):
                    return selected_ai, selected_color, board_color, assistant_index

def game_loop(selected_ai, selected_color, board_color, assistant_index):
    board = initial_board()
    selected = None
    moves = []
    running = True
    turn = True # True=white, False=black
    winner = None
    can_castle = {"w":{"K":True,"Q":True},"b":{"K":True,"Q":True}}
    en_passant = None
    play_vs_ai = selected_ai
    ai_color = None
    if play_vs_ai:
        ai_color = "black" if selected_color=="white" else "white"
    color1, color2 = BOARD_COLORS[board_color]
    assistant = ASSISTANTS[assistant_index]
    assistant_moves = []
    assistant_timer = 0
    assistant_piece = None

    while running:
        now = pygame.time.get_ticks()
        # Se uma peça está selecionada, só mostra as dicas depois de 1 segundo
        if assistant != "Desligado" and selected and ((not play_vs_ai) or 
                                                      (play_vs_ai and 
                                                       ((ai_color == 'white' and turn) or 
                                                        (ai_color == 'black' and not turn)) is False)):
            if assistant_piece != selected:
                assistant_timer = now
                assistant_piece = selected
                assistant_moves = []
            elif now - assistant_timer > 10 and not assistant_moves:
                row, col = selected
                # Sugere apenas as dicas para a peça selecionada
                all_moves = []
                for mr, mc in get_moves(board, row, col, en_passant, can_castle):
                    if valid_move(board, row, col, mr, mc, turn, en_passant, can_castle):
                        all_moves.append((row, col, mr, mc))
                assistant_moves = all_moves
        else:
            assistant_moves = []
            assistant_piece = None

        screen.fill((220,220,220))
        draw_board(board, selected, moves, color1, color2, assistant_moves)
        pygame.display.flip()

        if winner:
            font = pygame.font.SysFont(None, 70)
            msg = f"Vencedor: {'Branco' if winner == 'white' else 'Preto'}"
            text = font.render(msg, True, (200, 0, 0))
            screen.blit(text, (MARGIN + 40, 280))
            pygame.display.flip()
            pygame.time.wait(2500)
            break
        if is_checkmate(board, turn, en_passant, can_castle):
            winner = 'white' if not turn else 'black'
            continue

        if play_vs_ai and ((ai_color == 'white' and turn) or (ai_color == 'black' and not turn)):
            pygame.time.wait(350)
            mov = ai_move(board, turn, en_passant, can_castle, assistant)
            if mov is None:
                winner = 'white' if not turn else 'black'
                continue
            sr, sc, dr, dc = mov
            piece = board[sr][sc]
            do_move(board, sr, sc, dr, dc, piece, en_passant, can_castle)
            en_passant = get_en_passant(sr, sc, dr, dc, piece, board)
            selected = None
            moves = []
            turn = not turn
            assistant_moves = []
            assistant_piece = None
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False; pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and not winner:
                x, y = event.pos
                if x < MARGIN or y > BOARD_SIZE*SQUARE_SIZE: continue
                row, col = y//SQUARE_SIZE, (x-MARGIN)//SQUARE_SIZE
                if not in_board(row, col): continue
                if selected:
                    sr, sc = selected
                    if valid_move(board, sr, sc, row, col, turn, en_passant, can_castle):
                        piece = board[sr][sc]
                        do_move(board, sr, sc, row, col, piece, en_passant, can_castle)
                        en_passant = get_en_passant(sr, sc, row, col, piece, board)
                        selected = None
                        moves = []
                        turn = not turn
                        assistant_moves = []
                        assistant_piece = None
                    else:
                        selected = None
                        moves = []
                        assistant_moves = []
                        assistant_piece = None
                elif board[row][col] != "" and ((board[row][col][0] == "w" and turn) or 
                                                (board[row][col][0] == "b" and not turn)):
                    selected = (row, col)
                    moves = []
                    for mr, mc in get_moves(board, row, col, en_passant, can_castle):
                        if valid_move(board, row, col, mr, mc, turn, en_passant, can_castle):
                            moves.append((mr, mc))
                    assistant_moves = []
                    assistant_piece = None

    pygame.time.wait(800)
    return

def main():
    while True:
        selected_ai, selected_color, board_color, assistant_index = menu()
        game_loop(selected_ai, selected_color, board_color, assistant_index)

if __name__ == "__main__":
    main()