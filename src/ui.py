import pygame
import os
from chess_logic import piece_icons

COLOR_THEMES = [
    ((238,238,210),(118,150,86)),  # padrão
    ((255,255,255),(0,0,0)),       # alto contraste
    ((160,110,70),(64,48,32)),     # marrom
    ((210,210,210),(70,70,70)),    # cinza
    ((200,230,255),(60,180,240)),  # azul
]

def draw_board(screen, board, w, h, color_theme, selected, possible_moves, dragging, drag_piece, drag_offset):
    size = min(w, h)
    sq = size//8
    offx = (w-size)//2
    offy = (h-size)//2
    light, dark = COLOR_THEMES[color_theme]
    font = pygame.font.SysFont("Arial", sq//5, True)
    # Draw squares
    for row in range(8):
        for col in range(8):
            rect = pygame.Rect(offx+col*sq, offy+row*sq, sq, sq)
            color = light if (row+col)%2==0 else dark
            pygame.draw.rect(screen, color, rect)
            # Highlight selection
            if selected == (row, col):
                pygame.draw.rect(screen, (255,255,0,128), rect, 4)
            # Draw possible moves
    # Draw pieces
    for row in range(8):
        for col in range(8):
            p = board.piece_at(row, col)
            if p and (not dragging or (row,col) != selected):
                icon = piece_icons[f"{p.color}{p.kind}"]
                screen.blit(pygame.transform.smoothscale(icon, (sq, sq)), (offx+col*sq, offy+row*sq))
    # Draw dragging piece
    if dragging and drag_piece:
        x, y = pygame.mouse.get_pos()
        icon = piece_icons[f"{drag_piece.color}{drag_piece.kind}"]
        screen.blit(pygame.transform.smoothscale(icon, (sq, sq)), (x-drag_offset[0], y-drag_offset[1]))
    # Draw row/col numbers
    for i in range(8):
        # Row numbers (1-8)
        label = font.render(str(8-i), True, (0,0,0))
        screen.blit(label, (offx-18, offy+i*sq+sq//2-10))
        # Col letters (a-h)
        label = font.render(chr(ord('a')+i), True, (0,0,0))
        screen.blit(label, (offx+i*sq+sq//2-8, offy+size+2))

def draw_possible_moves(screen, moves, w, h, color_theme):
    size = min(w, h)
    sq = size//8
    offx = (w-size)//2
    offy = (h-size)//2
    for m in moves:
        x = offx + m.to_col*sq + sq//2
        y = offy + m.to_row*sq + sq//2
        pygame.draw.circle(screen, (0,255,0,180), (x, y), sq//5)

def draw_suggestion(screen, move, w, h):
    size = min(w, h)
    sq = size//8
    offx = (w-size)//2
    offy = (h-size)//2
    fx = offx + move.from_col*sq + sq//2
    fy = offy + move.from_row*sq + sq//2
    tx = offx + move.to_col*sq + sq//2
    ty = offy + move.to_row*sq + sq//2
    pygame.draw.line(screen, (255,0,0), (fx,fy), (tx,ty), 7)
    # Arrowhead
    pygame.draw.circle(screen, (255,0,0), (tx, ty), sq//8)

def draw_menu(screen, w, h):
    menu_font = pygame.font.SysFont("Arial", 40, True)
    small_font = pygame.font.SysFont("Arial", 24, False)
    clock = pygame.time.Clock()
    color_theme = 0
    player_color = 'w'
    vs_ai = True
    assist_mode = True
    state = 0
    while True:
        screen.fill((50,50,50))
        txt = menu_font.render("Jogo de Xadrez em Python", True, (255,255,255))
        screen.blit(txt, (w//2-txt.get_width()//2, 60))
        y = 170
        # Escolher cor das peças
        coltxt = small_font.render(f"Escolha sua cor: [{'Brancas' if player_color=='w' else 'Pretas'}] (A/D)", True, (255,255,255))
        screen.blit(coltxt, (w//2-coltxt.get_width()//2, y))
        y += 50
        # Vs AI ou Humano
        aitxt = small_font.render(f"Modo: [{'vs IA' if vs_ai else '2 Jogadores'}] (W/S)", True, (255,255,255))
        screen.blit(aitxt, (w//2 - aitxt.get_width()//2, y))
        y += 50
        # Escolher tema do tabuleiro
        themetxt = small_font.render(f"Tema do Tabuleiro: {color_theme+1}/{len(COLOR_THEMES)} (Q/E)", True, (255,255,255))
        screen.blit(themetxt, (w//2 - themetxt.get_width()//2, y))
        y += 50
        # Assistência virtual
        asstxt = small_font.render(f"Assistência Virtual: [{'Ativa' if assist_mode else 'Desativada'}] (Z/X)", True, (255,255,255))
        screen.blit(asstxt, (w//2 - asstxt.get_width()//2, y))
        y += 70
        playtxt = menu_font.render("Pressione ENTER para jogar", True, (0,255,0))
        screen.blit(playtxt, (w//2-playtxt.get_width()//2, y))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None, None, None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return player_color, vs_ai, color_theme, assist_mode
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    player_color = 'w'
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    player_color = 'b'
                elif event.key == pygame.K_w or event.key == pygame.K_UP:
                    vs_ai = True
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    vs_ai = False
                elif event.key == pygame.K_q:
                    color_theme = (color_theme - 1) % len(COLOR_THEMES)
                elif event.key == pygame.K_e:
                    color_theme = (color_theme + 1) % len(COLOR_THEMES)
                elif event.key == pygame.K_z:
                    assist_mode = True
                elif event.key == pygame.K_x:
                    assist_mode = False
        clock.tick(30)

def draw_end_screen(screen, w, h, winner):
    font = pygame.font.SysFont("Arial", 50, True)
    txt = font.render(f"Vencedor: {winner}", True, (0,255,0))
    screen.blit(txt, (w//2-txt.get_width()//2, h//2-txt.get_height()//2))
    pygame.display.flip()