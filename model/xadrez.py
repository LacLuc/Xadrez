import pygame
import chess
import os
import sys
import threading
import time
import threading

# CONFIGURAÇÕES
WIDTH, HEIGHT = 640, 640
BOARD_SIZE = 8
SQ_SIZE = WIDTH // BOARD_SIZE
FPS = 60

PIECE_NAMES = ['K', 'Q', 'R', 'B', 'N', 'P']
COLORS = {
    "Bege": ((240, 217, 181), (181, 136, 99)),
    "Cinza": ((200, 200, 200), (100, 100, 100)),
    "Verde": ((118, 150, 86), (238, 238, 210))
}
COLUMN_LETTERS = 'abcdefgh'

# CARREGAMENTO DAS PEÇAS
def load_piece_images():
    images = {}
    for color in ['w', 'b']:
        for name in PIECE_NAMES:
            path = os.path.join('assets', f'{color}{name}.png')
            images[f'{color}{name}'] = pygame.transform.smoothscale(
                pygame.image.load(path), (SQ_SIZE, SQ_SIZE))
    return images

# MENU
def draw_menu(screen, selected_options):
    screen.fill((50, 50, 50))
    font = pygame.font.SysFont(None, 48)
    smallfont = pygame.font.SysFont(None, 32)
    midfont = pygame.font.SysFont(None, 40)
    y = 70

    screen.blit(font.render('Jogo de Xadrez', True, (255, 255, 255)), (WIDTH//2-160, 20))

    # Escolha IA ou 2 jogadores
    screen.blit(midfont.render('Modo de Jogo:', True, (200,255,255)), (70, y))
    pygame.draw.rect(screen, (100,100,255) if selected_options['mode'] == 'vs_ai' else (60,60,60), (350, y, 160, 40))
    screen.blit(smallfont.render('VS IA', True, (255,255,255)), (370, y+5))
    pygame.draw.rect(screen, (100,100,255) if selected_options['mode'] == '2p' else (60,60,60), (520, y, 90, 40))
    screen.blit(smallfont.render('2 Jog.', True, (255,255,255)), (530, y+5))

    y += 60
    # Escolha cor das peças do jogador
    screen.blit(midfont.render('Jogar com:', True, (255,200,200)), (70, y))
    pygame.draw.rect(screen, (100,100,255) if selected_options['side'] == 'white' else (60,60,60), (350, y, 100, 40))
    screen.blit(smallfont.render('Brancas', True, (255,255,255)), (355, y+5))
    pygame.draw.rect(screen, (100,100,255) if selected_options['side'] == 'black' else (60,60,60), (460, y, 100, 40))
    screen.blit(smallfont.render('Pretas', True, (255,255,255)), (475, y+5))

    y += 60
    # Escolha cor do tabuleiro
    screen.blit(midfont.render('Cor do Tabuleiro:', True, (255,255,200)), (70, y))
    for i, (cname, _) in enumerate(COLORS.items()):
        pygame.draw.rect(screen, (100,255,100) if selected_options['board_color'] == cname else (60,60,60), (350+110*i, y, 100, 40))
        screen.blit(smallfont.render(cname, True, (255,255,255)), (360+110*i, y+5))

    y += 60
    # Assistência virtual
    screen.blit(midfont.render('Assistência Virtual:', True, (200,255,200)), (70, y))
    pygame.draw.rect(screen, (100,255,100) if selected_options['assist'] else (60,60,60), (420, y, 160, 40))
    screen.blit(smallfont.render('Ativar' if selected_options['assist'] else 'Desativar', True, (0,0,0)), (445, y+5))

    y += 90
    # Botão iniciar
    pygame.draw.rect(screen, (200,200,0), (WIDTH//2-80, y, 160, 50))
    screen.blit(font.render('JOGAR', True, (40,40,40)), (WIDTH//2-55, y+5))

    pygame.display.flip()

def menu_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Menu Xadrez')
    clock = pygame.time.Clock()
    selected_options = {
        'mode': 'vs_ai',
        'side': 'white',
        'board_color': list(COLORS)[0],
        'assist': True
    }
    while True:
        draw_menu(screen, selected_options)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Modo de jogo
                if 350 <= mx <= 510 and 70 <= my <= 110:
                    selected_options['mode'] = 'vs_ai'
                if 520 <= mx <= 610 and 70 <= my <= 110:
                    selected_options['mode'] = '2p'
                # Lado
                if 350 <= mx <= 450 and 130 <= my <= 170:
                    selected_options['side'] = 'white'
                if 460 <= mx <= 560 and 130 <= my <= 170:
                    selected_options['side'] = 'black'
                # Cor do tabuleiro
                for i, cname in enumerate(COLORS.keys()):
                    if (350+110*i) <= mx <= (450+110*i) and 190 <= my <= 230:
                        selected_options['board_color'] = cname
                # Assistência
                if 420 <= mx <= 580 and 250 <= my <= 290:
                    selected_options['assist'] = not selected_options['assist']
                # Jogar
                if WIDTH//2-80 <= mx <= WIDTH//2+80 and 340 <= my <= 390:
                    return selected_options
        clock.tick(FPS)

# ASSISTENTE VIRTUAL (DICA DE JOGADA)
def get_ai_hint(board, depth=3):
    try:
        # Usa Stockfish se disponível, com profundidade configurável
        import chess.engine
        with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
            result = engine.play(board, chess.engine.Limit(depth=depth))
            return result.move
    except Exception:
        # fallback: escolha a melhor captura (maior valor), senão o primeiro lance legal
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        best_capture = None
        best_value = -1
        for move in board.legal_moves:
            if board.is_capture(move):
                captured = board.piece_at(move.to_square)
                if captured:
                    value = piece_values.get(captured.piece_type, 0)
                    if value > best_value:
                        best_value = value
                        best_capture = move
        if best_capture:
            return best_capture
        return next(iter(board.legal_moves), None)

# DESENHO DO TABULEIRO E PEÇAS
def draw_board(screen, board, images, selected_sq, moves, board_colors, assist_moves=None, last_move=None, orientation='white'):
    light, dark = board_colors
    font = pygame.font.SysFont(None, 24)
    # Desenhar casas
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rank = 7 - r if orientation == 'white' else r
            file = c if orientation == 'white' else 7-c
            color = light if (r+c)%2==0 else dark
            pygame.draw.rect(screen, color, (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            # Destacar casa selecionada
            if selected_sq == (file, rank):
                pygame.draw.rect(screen, (255,255,0,80), (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            # Destacar casas de movimento possível
            if moves:
                for move in moves:
                    if move.to_square == chess.square(file, rank):
                        pygame.draw.circle(screen, (50,200,50), (c*SQ_SIZE+SQ_SIZE//2, r*SQ_SIZE+SQ_SIZE//2), 15, 0)
            # Assistência virtual (antes de clicar)
            if assist_moves:
                for move in assist_moves:
                    if move.from_square == chess.square(file, rank):
                        pygame.draw.rect(screen, (0,255,255,120), (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            # Destacar último lance
            if last_move and (chess.square(file, rank) in [last_move.from_square, last_move.to_square]):
                pygame.draw.rect(screen, (255,120,0,80), (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
    # Desenhar peças
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            rank = chess.square_rank(square)
            file = chess.square_file(square)
            c = file if orientation == 'white' else 7-file
            r = 7-rank if orientation == 'white' else rank
            imgname = f"{'w' if piece.color else 'b'}{piece.symbol().upper()}"
            screen.blit(images[imgname], (c*SQ_SIZE, r*SQ_SIZE))
    # Números e letras
    for i in range(BOARD_SIZE):
        # Linhas
        r = 7-i if orientation == 'white' else i
        num = str(i+1) if orientation == 'white' else str(8-i)
        txt = font.render(num, True, (0,0,0))
        screen.blit(txt, (5, r*SQ_SIZE+5))
        # Colunas
        c = i if orientation == 'white' else 7-i
        txt = font.render(COLUMN_LETTERS[c], True, (0,0,0))
        screen.blit(txt, (c*SQ_SIZE+SQ_SIZE-18, HEIGHT-28))

# JANELA PRINCIPAL DO JOGO
def main():
    options = menu_loop()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Xadrez')
    clock = pygame.time.Clock()
    images = load_piece_images()
    board = chess.Board()
    orientation = options['side']
    running = True
    selected_sq = None
    legal_moves = []
    last_move = None
    message = ""
    ai_thinking = False
    ai_hint = None
    board_colors = COLORS[options['board_color']]
    ai_side = 'black' if options['side'] == 'white' else 'white'
    assist_moves = None

    def ai_play():
        nonlocal board, last_move, ai_thinking
        ai_thinking = True
        move = get_ai_hint(board)
        if move:
            board.push(move)
            last_move = move
        ai_thinking = False

    def update_assist_moves():
        nonlocal assist_moves
        if options['assist'] and not board.is_game_over() and \
            ((board.turn and orientation=='white') or 
             (not board.turn and orientation=='black')):
            # Dica: todas as casas de origem dos melhores lances
            best_move = get_ai_hint(board)
            if best_move:
                assist_moves = [best_move]
            else:
                assist_moves = []
        else:
            assist_moves = []

    update_assist_moves()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and not ai_thinking and not board.is_game_over():
                mx, my = event.pos
                c = mx // SQ_SIZE
                r = my // SQ_SIZE
                file = c if orientation == 'white' else 7-c
                rank = 7-r if orientation == 'white' else r
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if selected_sq is None:
                    if piece and ((piece.color and board.turn) or (not piece.color and not board.turn)):
                        selected_sq = (file, rank)
                        legal_moves = [m for m in board.legal_moves if m.from_square == square]
                else:
                    # Jogar se possível
                    move_valid = [m for m in legal_moves if m.to_square == square]
                    if move_valid:
                        board.push(move_valid[0])
                        last_move = move_valid[0]
                        selected_sq = None
                        legal_moves = []
                        update_assist_moves()
                        continue
                    else:
                        selected_sq = None
                        legal_moves = []
                update_assist_moves()
        # IA joga automaticamente se for sua vez       
        if options['mode'] == 'vs_ai' and not ai_thinking and not board.is_game_over():
            if (board.turn and ai_side=='white') or (not board.turn and ai_side=='black'):
                threading.Thread(target=ai_play).start()
                time.sleep(0.15)
                update_assist_moves()
          
        # Assistência virtual (antes de clicar)
        if options['assist']:
            update_assist_moves()
        # Desenhar tudo
        draw_board(screen, board, images, selected_sq, legal_moves, board_colors, assist_moves=assist_moves, last_move=last_move, orientation=orientation)
        # Mensagem de vitória
        if board.is_game_over():
            font = pygame.font.SysFont(None, 80)
            result = board.result()
            txt = "Empate" if result=='1/2-1/2' else ("Brancas vencem!" if result=='1-0' else "Pretas vencem!")
            pygame.draw.rect(screen, (0,0,0), (WIDTH//2-180, HEIGHT//2-60, 360, 120))
            screen.blit(font.render(txt, True, (255, 255, 0)), (WIDTH//2-150, HEIGHT//2-40))
            pygame.draw.rect(screen, (220,160,60), (WIDTH//2-90, HEIGHT//2+30, 180, 50))
            font2 = pygame.font.SysFont(None, 50)
            screen.blit(font2.render("Menu", True, (0,0,0)), (WIDTH//2-37, HEIGHT//2+37))
            pygame.display.flip()
            wait_menu = True
            while wait_menu:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = event.pos
                        if WIDTH//2-90 <= mx <= WIDTH//2+90 and HEIGHT//2+30 <= my <= HEIGHT//2+80:
                            return main()
                time.sleep(0.05)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == '__main__':
    main()