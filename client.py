

from pygame import *
import socket
import json
from threading import Thread
from random import randint
import random

# ================== PYGAME ==================
WIDTH, HEIGHT = 800, 600
init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг // BREAKCORE")

# ================== МУЗЫКА ==================
mixer.music.load("music/BlksmiithSr20Det.ogg")
mixer.music.set_volume(0.5)

# ================== ШРИФТЫ ==================
font_win = font.Font(None, 72)
font_main = font.Font(None, 28)
font_big = font.Font(None, 36)

# ================== ФОН ==================
background = image.load("photos/52.png").convert()
background = transform.scale(background, (WIDTH, HEIGHT))

# ================== BREAKCORE FX ==================
GLITCH_CHANCE = 0.03
GLITCH_TIME = 0
shake = 0

ball_trail = []
MAX_TRAIL = 15
particles = []

# ================== FX ==================
def spawn_particles(x, y, color):
    for _ in range(14):
        particles.append({
            "x": x,
            "y": y,
            "vx": randint(-4, 4),
            "vy": randint(-4, 4),
            "life": 25,
            "color": color
        })

def glitch_effect():
    global GLITCH_TIME
    if GLITCH_TIME > 0:
        GLITCH_TIME -= 1
        slice_y = random.randint(0, HEIGHT - 20)
        slice_h = random.randint(5, 25)
        offset = random.randint(-30, 30)
        area = Rect(0, slice_y, WIDTH, slice_h)
        screen.blit(screen, (offset, slice_y), area)
        if random.random() < 0.3:
            screen.fill((255, 0, 0), special_flags=BLEND_ADD)
    elif random.random() < GLITCH_CHANCE:
        GLITCH_TIME = random.randint(1, 3)

def glitch_text(text, font, x, y):
    base = font.render(text, True, (255, 255, 255))
    screen.blit(base, (x, y))
    if random.random() < 0.15:
        for _ in range(2):
            off = random.randint(-3, 3)
            color = random.choice([(255, 0, 77), (0, 246, 255)])
            ghost = font.render(text, True, color)
            screen.blit(ghost, (x + off, y + off))

# ================== МЕНЮ ==================
def menu():
    btn_w, btn_h = 320, 60
    btn_classic = Rect(WIDTH // 2 - btn_w // 2, 300, btn_w, btn_h)
    btn_training = Rect(WIDTH // 2 - btn_w // 2, 380, btn_w, btn_h)

    while True:
        clock.tick(60)
        screen.fill((0, 0, 0))

        glitch_text("PING PONG", font_win, WIDTH//2 - 160, 160)

        draw.rect(screen, (40, 40, 40), btn_classic, border_radius=10)
        draw.rect(screen, (40, 40, 40), btn_training, border_radius=10)

        glitch_text("Онлайн", font_big, btn_classic.x + 110, btn_classic.y + 15)
        glitch_text("Тренування", font_big, btn_training.x + 90, btn_training.y + 15)

        glitch_effect()
        display.update()

        for e in event.get():
            if e.type == QUIT:
                quit()
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if btn_classic.collidepoint(e.pos):
                    return "classic"
                if btn_training.collidepoint(e.pos):
                    return "training"

# ================== ПОПЕРЕДЖЕННЯ ==================
def warning_screen():
    while True:
        clock.tick(60)
        screen.fill((0, 0, 0))

        glitch_text("ПОПЕРЕДЖЕННЯ", font_win, WIDTH//2 - 220, 120)

        lines = [
            "Ця гра містить візуальні глітч-ефекти,",
            "різкі спалахи та динамічні рухи екрана.",
            "",
            "Не рекомендовано людям з фоточутливістю",
            "або схильністю до епілептичних нападів.",
            "",
            "Гра створена в стилі breakcore / glitch.",
            "",
            "Натисни будь-яку клавішу або клікни мишею",
            "щоб продовжити."
        ]

        y = 240
        for line in lines:
            glitch_text(line, font_main, WIDTH//2 - 260, y)
            y += 32

        glitch_effect()
        display.update()

        for e in event.get():
            if e.type == QUIT:
                quit()
            if e.type in (KEYDOWN, MOUSEBUTTONDOWN):
                return

# ================== СЕРВЕР ==================
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080))
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# ================== ЗАПУСК ==================
mode = menu()
warning_screen()
mixer.music.play(-1)

game_over = False
you_winner = None
current_move = "STOP"

my_id, game_state, buffer, client = connect_to_server()
if my_id == 0:
    client.send(mode.encode())

Thread(target=receive, daemon=True).start()

# ================== ІГРА ==================
while True:
    for e in event.get():
        if e.type == QUIT:
            mixer.music.stop()
            quit()

    keys = key.get_pressed()
    new_move = "STOP"
    if keys[K_w]:
        new_move = "UP"
    elif keys[K_s]:
        new_move = "DOWN"

    if new_move != current_move:
        client.send(new_move.encode())
        current_move = new_move

    if game_state:
        offset_x = random.randint(-shake, shake) if shake > 0 else 0
        offset_y = random.randint(-shake, shake) if shake > 0 else 0
        shake = max(0, shake - 1)

        screen.blit(background, (offset_x, offset_y))

        ball_x = game_state['ball']['x']
        ball_y = game_state['ball']['y']

        draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))
        draw.rect(screen, (255, 0, 77), (WIDTH - 40, game_state['paddles']['1'], 20, 100))
        draw.circle(screen, (255, 0, 77), (ball_x, ball_y), 10)

        glitch_text(f"{game_state['scores'][0]} : {game_state['scores'][1]}",
                    font_big, WIDTH//2 - 20, 20)

        if game_state.get('sound_event'):
            shake = 6
            spawn_particles(ball_x, ball_y, (255, 255, 255))

        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), 3)
            if p["life"] <= 0:
                particles.remove(p)

        glitch_effect()

    display.update()
    clock.tick(60)
