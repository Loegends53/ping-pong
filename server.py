import socket
import json
import threading
import time
import random
import math

WIDTH, HEIGHT = 800, 600
BALL_SPEED = 5
MAX_BALL_SPEED = 9
PADDLE_SPEED = 8
BOT_SPEED = 6
PADDLE_HEIGHT = 100
COUNTDOWN_START = 3


class GameServer:
    def __init__(self, host='localhost', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("🎮 Server started")

        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()

        self.mode = None
        self.expected_players = 2

        self.sound_event = None

    # ================= GAME STATE =================
    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}
        self.paddle_dir = {0: 0, 1: 0}
        self.scores = [0, 0]

        angle = random.uniform(-0.5, 0.5)
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * angle
        }

        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None

    # ================= CLIENT =================
    def handle_client(self, pid):
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode().strip()
                if not data:
                    continue

                with self.lock:
                    if data in ("classic", "training"):
                        self.mode = data
                        self.expected_players = 1 if data == "training" else 2
                    elif data == "UP":
                        self.paddle_dir[pid] = -1
                    elif data == "DOWN":
                        self.paddle_dir[pid] = 1
                    elif data == "STOP":
                        self.paddle_dir[pid] = 0
        except:
            with self.lock:
                self.connected[pid] = False
                self.game_over = True
                self.winner = 1 - pid

    # ================= NETWORK =================
    def broadcast_state(self):
        state = json.dumps({
            "mode": self.mode,
            "paddles": self.paddles,
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event
        }) + "\n"

        for conn in self.clients.values():
            if conn:
                try:
                    conn.sendall(state.encode())
                except:
                    pass

    # ================= GAME LOOP =================
    def ball_logic(self):
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        while not self.game_over:
            with self.lock:
                # --- paddles ---
                for pid in [0, 1]:
                    self.paddles[pid] += self.paddle_dir[pid] * PADDLE_SPEED
                    self.paddles[pid] = max(
                        60, min(HEIGHT - PADDLE_HEIGHT, self.paddles[pid])
                    )

                # --- bot ---
                if self.mode == "training":
                    target = self.ball["y"] - PADDLE_HEIGHT // 2
                    if self.paddles[1] < target:
                        self.paddles[1] += BOT_SPEED
                    elif self.paddles[1] > target:
                        self.paddles[1] -= BOT_SPEED

                # --- ball ---
                self.ball["x"] += self.ball["vx"]
                self.ball["y"] += self.ball["vy"]

                if self.ball["y"] <= 60 or self.ball["y"] >= HEIGHT:
                    self.ball["vy"] *= -1
                    self.sound_event = "wall_hit"

                for pid, px in [(0, 40), (1, WIDTH - 40)]:
                    if abs(self.ball["x"] - px) < 10:
                        py = self.paddles[pid]
                        if py <= self.ball["y"] <= py + PADDLE_HEIGHT:
                            offset = (
                                self.ball["y"]
                                - (py + PADDLE_HEIGHT / 2)
                            ) / (PADDLE_HEIGHT / 2)
                            self.ball["vx"] *= -1
                            self.ball["vy"] = offset * MAX_BALL_SPEED
                            self.sound_event = "platform_hit"

                # --- goal ---
                if self.ball["x"] < 0:
                    self.scores[1] += 1
                    self.reset_ball()
                elif self.ball["x"] > WIDTH:
                    self.scores[0] += 1
                    self.reset_ball()

                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

                self.broadcast_state()
                self.sound_event = None

            time.sleep(0.016)

    def reset_ball(self):
        angle = random.uniform(-0.7, 0.7)
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * angle
        }

    # ================= CONNECTION =================
    def accept_players(self):
        while sum(self.connected.values()) < self.expected_players:
            conn, _ = self.server.accept()
            pid = 0 if not self.connected[0] else 1

            self.clients[pid] = conn
            self.connected[pid] = True
            conn.sendall((str(pid) + "\n").encode())

            threading.Thread(
                target=self.handle_client,
                args=(pid,),
                daemon=True
            ).start()

    # ================= MAIN =================
    def run(self):
        while True:
            self.mode = None
            self.expected_players = 2

            self.accept_players()
            self.reset_game_state()

            threading.Thread(
                target=self.ball_logic,
                daemon=True
            ).start()

            while not self.game_over:
                time.sleep(0.1)

            time.sleep(3)

            for pid in [0, 1]:
                try:
                    if self.clients[pid]:
                        self.clients[pid].close()
                except:
                    pass
                self.clients[pid] = None
                self.connected[pid] = False


GameServer().run()
