from pygame import *         # Усі модулі pygame
import socket                # Для підключення до сервера
import json                  # Для розбору JSON-даних від сервера
from threading import Thread # Потік для прийому даних паралельно з грою
 
# --- PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600    # Розмір ігрового вікна
 
init()                      # Ініціалізація pygame
screen = display.set_mode((WIDTH, HEIGHT))  # Створення вікна
clock = time.Clock()        # Таймер для обмеження FPS
display.set_caption("Пінг-Понг")  # Заголовок вікна
 
# --- СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            # Створюємо TCP-клієнт
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
            # Підключаємось до сервера
            client.connect(('localhost', 8080))
 
            buffer = ""      # Буфер для часткових повідомлень
            game_state = {}  # Стан гри, який приходить з сервера
 
            # Отримуємо свій ID (0 або 1) від сервера
            my_id = int(client.recv(24).decode())
 
            # Повертаємо всі потрібні дані
            return my_id, game_state, buffer, client
        except:
            # Якщо сервер ще не доступний — пробуємо знову
            pass
 
def receive():
    global buffer, game_state, game_over
    # Окремий потік для отримання даних від сервера
    while not game_over:
        try:
            # Отримуємо дані шматками
            data = client.recv(1024).decode()
 
            # Додаємо їх у буфер
            buffer += data
 
            # Обробляємо всі повні JSON-пакети
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    # Перетворюємо JSON → словник Python
                    game_state = json.loads(packet)
        except:
            # Якщо зʼєднання обірвалось
            game_state["winner"] = -1
            break
 
# --- ШРИФТИ ---
font_win = font.Font(None, 72)   # Великий шрифт для перемоги
font_main = font.Font(None, 36)  # Основний шрифт
# --- ЗОБРАЖЕННЯ ---
background = image.load("photos/52.png").convert()
background = transform.scale(background, (WIDTH, HEIGHT))
 
# --- ЗВУКИ ---
 
# --- ГРА ---
game_over = False        # Чи завершена гра
winner = None            # Переможець
you_winner = None        # Чи переміг саме ти
 
# Підключаємося до сервера
my_id, game_state, buffer, client = connect_to_server()
 
# Запускаємо потік прийому даних
Thread(target=receive, daemon=True).start()
 
# --- ГОЛОВНИЙ ЦИКЛ ГРИ ---
while True:
    # Обробка подій pygame
    for e in event.get():
        if e.type == QUIT:
            exit()
 
    # --- ВІДЛІК ПЕРЕД СТАРТОМ ---
    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.blit(background, (0, 0))
        countdown_text = font.Font(None, 72).render(
            str(game_state["countdown"]), True, (255, 255, 255)
        )
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue  # Не малюємо гру під час відліку
 
    # --- ЕКРАН ПЕРЕМОГИ ---
    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(background, (0, 0))
 
        # Визначаємо результат тільки один раз
        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)
 
        # Текст залежно від результату
        text = "Ти переміг!" if you_winner else "Пощастить наступного разу!"
 
        win_text = font_win.render(text, True, (255, 215, 0))
        screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
 
        restart_text = font_win.render('К - рестарт', True, (255, 215, 0))
        screen.blit(
            restart_text,
            restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        )
 
        display.update()
        continue  # Блокуємо гру після завершення
 
    # --- ОСНОВНЕ МАЛЮВАННЯ ГРИ ---
    if game_state:
        screen.blit(background, (0, 0))
 
        # Ліва ракетка (гравець 0)
        draw.rect(
            screen, (0, 255, 0),
            (20, game_state['paddles']['0'], 20, 100)
        )
 
        # Права ракетка (гравець 1)
        draw.rect(
            screen, (255, 0, 255),
            (WIDTH - 40, game_state['paddles']['1'], 20, 100)
        )
 
        # Мʼяч
        draw.circle(
            screen, ((0, 0, 255)),
            (game_state['ball']['x'], game_state['ball']['y']), 10
        )
 
        # Рахунок
        score_text = font_main.render(
            f"{game_state['scores'][0]} : {game_state['scores'][1]}",
            True, (255, 255, 255)
        )
        screen.blit(score_text, (WIDTH // 2 - 25, 20))
 
        # Обробка звуків
        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                pass  # звук удару об стіну
            elif game_state['sound_event'] == 'platform_hit':
                pass  # звук удару об ракетку
 

    else:
        # Якщо стан гри ще не отриманий
        waiting_text = font_main.render(
            "Очікування гравців...", True, (255, 255, 255)
        )
        screen.blit(waiting_text, (WIDTH // 2 - 25, 20))
 
    # Оновлюємо екран
    display.update()
 
    # Обмежуємо FPS до 60
    clock.tick(60)
 
    # --- ВІДПРАВКА КОМАНД НА СЕРВЕР ---
    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")     # Рух вгору
    elif keys[K_s]:
        client.send(b"DOWN")   # Рух вниз