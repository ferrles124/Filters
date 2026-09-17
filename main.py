import math
import random
import time

import cv2
import mediapipe as mp
import numpy as np

WINDOW_W = 1280
WINDOW_H = 720


class Duck:
    def __init__(self, width, height):
        self.direction = 1 if random.random() > 0.5 else -1
        self.x = width + 80 if self.direction == -1 else -80
        self.base_y = random.randint(120, height - 220)
        self.speed = random.uniform(170, 260)
        self.size = random.randint(38, 62)
        self.phase = random.uniform(0, 2 * math.pi)
        self.wobble = random.uniform(1.5, 3.2)
        self.hit = False

    def update(self, dt):
        self.x += self.direction * self.speed * dt
        self.y = self.base_y + math.sin(time.monotonic() * self.wobble + self.phase) * 18

    def draw(self, frame, now):
        x = int(self.x)
        y = int(self.y)
        s = self.size

        body_color = (80, 170, 255) if self.direction > 0 else (255, 180, 90)
        wing_color = (255, 255, 255)
        beak_color = (255, 140, 60)

        cv2.ellipse(frame, (x, y), (s, s // 2), 0, 0, 360, body_color, -1)
        cv2.circle(frame, (x + s // 2, y - 8), s // 3, wing_color, -1)
        cv2.circle(frame, (x + s // 2, y - 10), s // 5, (40, 40, 40), -1)
        cv2.circle(frame, (x + s // 2, y - 12), max(2, s // 10), (0, 0, 0), -1)
        cv2.line(frame, (x + s, y), (x + s + 18, y - 4), beak_color, 7)
        cv2.line(frame, (x + s // 2, y + 8), (x + s // 2 - 10, y + 32), (80, 80, 80), 4)
        cv2.line(frame, (x + s // 2, y + 8), (x + s // 2 + 10, y + 32), (80, 80, 80), 4)
        cv2.ellipse(frame, (x - 10, y - 8), (s // 4, s // 5), 0, 0, 360, (255, 255, 255), -1)

    def collides_with(self, point):
        dx = point[0] - self.x
        dy = point[1] - self.y
        return math.hypot(dx, dy) < self.size * 0.9


class Cloud:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(50, height // 2)
        self.speed = random.uniform(5, 18)
        self.scale = random.uniform(0.7, 1.9)

    def update(self, dt, width):
        self.x -= self.speed * dt
        if self.x < -200:
            self.x = width + 200
            self.y = random.randint(40, height // 2)

    def draw(self, frame):
        x = int(self.x)
        y = int(self.y)
        s = self.scale
        cv2.ellipse(frame, (x, y), (int(70 * s), int(26 * s)), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (x + 46 * s, y + 6), (int(48 * s), int(20 * s)), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (x - 46 * s, y + 8), (int(44 * s), int(18 * s)), 0, 0, 360, (255, 255, 255), -1)


def gradient_sky(frame, scroll):
    h, w = frame.shape[:2]
    for y in range(h):
        t = y / max(1, h)
        b = int(70 + (200 - 70) * t)
        g = int(120 + (230 - 120) * t)
        r = int(140 + (255 - 140) * t)
        frame[y, :, :] = (b, g, r)

    for i in range(0, w + 200, 150):
        x = (i - scroll) % (w + 180)
        cv2.ellipse(frame, (x, 130), (120, 35), 0, 0, 360, (255, 255, 255, 180), -1)

    horizon = int(h * 0.75)
    cv2.rectangle(frame, (0, horizon), (w, h), (120, 180, 120), -1)
    cv2.line(frame, (0, horizon), (w, horizon), (190, 220, 200), 2)

    for i in range(-40, w + 100, 60):
        x = (i - scroll * 1.2) % (w + 100)
        y = horizon + 25 + (i % 50)
        cv2.line(frame, (x, y), (x + 30, y + 15), (90, 140, 100), 3)
        cv2.line(frame, (x + 30, y + 15), (x + 60, y), (90, 140, 100), 3)


def draw_reticle(frame, x, y, active):
    color = (255, 80, 80) if active else (245, 245, 245)
    cv2.circle(frame, (int(x), int(y)), 22, color, 2)
    cv2.line(frame, (int(x) - 15, int(y)), (int(x) + 15, int(y)), color, 2)
    cv2.line(frame, (int(x), int(y) - 15), (int(x), int(y) + 15), color, 2)


def draw_hud(frame, score, lives):
    cv2.rectangle(frame, (20, 20), (260, 90), (0, 0, 0), -1)
    cv2.putText(frame, f"Score: {score}", (35, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(frame, f"Lives: {lives}", (35, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 220, 100), 2)


def play_game():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Kamera açılamadı. Lütfen kameraya erişim izni verin.")

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    score = 0
    lives = 3
    ducks = []
    clouds = [Cloud(WINDOW_W, WINDOW_H) for _ in range(7)]
    spawn_timer = 0.8
    reticle = (WINDOW_W // 2, WINDOW_H // 2)
    last_shot_time = 0.0
    last_hit_flash = 0.0
    flash_position = None
    scroll = 0.0

    previous_time = time.monotonic()

    while True:
        now_mono = time.monotonic()
        dt = now_mono - previous_time
        previous_time = now_mono

        ok, camera_frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(camera_frame, 1)
        hand_point = None
        pinch = False

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            index_tip = landmarks[8]
            thumb_tip = landmarks[4]
            px = int(index_tip.x * WINDOW_W)
            py = int(index_tip.y * WINDOW_H)
            hand_point = (px, py)
            reticle = hand_point

            thumb_index_dist = math.hypot(
                (thumb_tip.x - index_tip.x) * WINDOW_W,
                (thumb_tip.y - index_tip.y) * WINDOW_H,
            )
            pinch = thumb_index_dist < 48

        scene = np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)
        scroll += 80 * dt
        gradient_sky(scene, scroll)

        for cloud in clouds:
            cloud.update(dt, WINDOW_W)
            cloud.draw(scene)

        spawn_timer -= dt
        if spawn_timer <= 0:
            ducks.append(Duck(WINDOW_W, WINDOW_H))
            spawn_timer = random.uniform(0.8, 1.6)

        for duck in ducks:
            duck.update(dt)
            duck.draw(scene, now_mono)

        for duck in list(ducks):
            if duck.x < -120 or duck.x > WINDOW_W + 120:
                ducks.remove(duck)
                if not duck.hit:
                    lives -= 1

        if pinch and now_mono - last_shot_time > 0.45:
            shot_target = None
            best_distance = float("inf")
            for duck in ducks:
                dist = math.hypot(duck.x - reticle[0], duck.y - reticle[1])
                if dist < best_distance:
                    best_distance = dist
                    shot_target = duck

            last_shot_time = now_mono
            flash_position = reticle
            last_hit_flash = now_mono

            if shot_target is not None and best_distance < 120:
                shot_target.hit = True
                ducks.remove(shot_target)
                score += 1
            else:
                score = max(0, score - 1)

        if flash_position is not None and now_mono - last_hit_flash < 0.18:
            cv2.circle(scene, flash_position, 18, (255, 200, 80), -1)
            cv2.circle(scene, flash_position, 30, (255, 140, 80), 3)
        else:
            flash_position = None

        if hand_point is not None:
            draw_reticle(scene, *hand_point, pinch)

        draw_hud(scene, score, lives)

        cv2.putText(
            scene,
            "shoot with your pinch",
            (WINDOW_W - 260, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Sky Hunt", scene)

        if lives <= 0:
            cv2.putText(scene, "Game Over", (WINDOW_W // 2 - 150, WINDOW_H // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 70, 70), 4)
            cv2.imshow("Sky Hunt", scene)
            cv2.waitKey(1200)
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    play_game()


"""
Not: Orijinal filtre tabanlı AR yapısı korunmak istenirse; bu oyun sürümü ana giriş noktası olarak
`main.py` içinde çalışır. Görüntülenen şey gerçek kameraya ait ekrana değil, gökyüzü ve ördekler oyun sahnesidir.
"""


