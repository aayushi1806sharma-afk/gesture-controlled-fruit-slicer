import cv2
import time
import random
import math
import numpy as np
from collections import deque

from hand_tracking import HandTracker
from game_objects  import Vegetable, Bomb
from effects       import Particle
from sound_manager import SoundManager
from leaderboard   import load_scores, save_score, is_high_score, draw_leaderboard


# ──────────────────────────────────────────
#  SETUP
# ──────────────────────────────────────────
cap     = cv2.VideoCapture(0)
tracker = HandTracker()
sfx     = SoundManager()

TRAIL_LEN    = 28
trail_points = deque(maxlen=TRAIL_LEN)

vegetables = []
bombs      = []
particles  = []

score      = 0
combo      = 0
prev_combo = 0

game_state  = "menu"    # menu | playing | name_entry | leaderboard | gameover
player_name = ""        # typed during name_entry state
pulse_t     = 0.0       # global timer for animations

last_spawn      = time.time()
last_bomb_spawn = time.time()

prev_pos = None


# ──────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────
def reset_game():
    global vegetables, bombs, particles, score, combo, prev_combo
    global trail_points, prev_pos, last_spawn, last_bomb_spawn
    vegetables      = [Vegetable() for _ in range(5)]
    bombs           = [Bomb()      for _ in range(2)]
    particles       = []
    score           = 0
    combo           = 0
    prev_combo      = 0
    trail_points.clear()
    prev_pos        = None
    last_spawn      = time.time()
    last_bomb_spawn = time.time()


def draw_glow_trail(frame, points):
    if len(points) < 3:
        return
    pts     = list(points)
    n       = len(pts)
    overlay = frame.copy()
    for i in range(1, n):
        p1, p2 = pts[i - 1], pts[i]
        if p1 is None or p2 is None:
            continue
        t  = i / n
        r  = int(80  + 175 * t)
        g  = int(120 + 135 * t)
        b  = 255
        glow3 = max(2, int(18 * t))
        glow2 = max(2, int(10 * t))
        core  = max(1, int(4  * t))
        cv2.line(overlay, p1, p2,
                 (int(b * 0.3), int(g * 0.3), int(r * 0.3)), glow3, cv2.LINE_AA)
        cv2.line(overlay, p1, p2,
                 (int(b * 0.6), int(g * 0.6), int(r * 0.6)), glow2, cv2.LINE_AA)
        cv2.line(frame,   p1, p2, (b, g, r), core, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
    tip = pts[-1]
    if tip:
        cv2.circle(frame, tip, 16, (180, 230, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, tip, 12, (255, 255, 255), -1, cv2.LINE_AA)


def shadow_text(frame, text, pos, scale, color, thickness):
    cv2.putText(frame, text, (pos[0]+2, pos[1]+2),
                cv2.FONT_HERSHEY_SIMPLEX, scale, (0,0,0), thickness+2)
    cv2.putText(frame, text, pos,
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def dim_frame(frame, alpha=0.55):
    ov = frame.copy()
    cv2.rectangle(ov, (0,0), (frame.shape[1], frame.shape[0]), (0,0,0), -1)
    cv2.addWeighted(ov, alpha, frame, 1-alpha, 0, frame)


# ──────────────────────────────────────────
#  GAME LOOP
# ──────────────────────────────────────────
while True:
    success, frame = cap.read()
    if not success:
        break

    frame   = cv2.resize(frame, (1280, 720))
    frame   = cv2.flip(frame, 1)
    pulse_t = time.time()

    frame, finger_position = tracker.detect_hand(frame)


    # ════════════════════════════════
    #  MENU
    # ════════════════════════════════
    if game_state == "menu":
        t   = pulse_t
        W, H = 1280, 720

        # ── dark gradient overlay ──
        overlay = np.zeros_like(frame)
        for row in range(H):
            alpha = 0.55 + 0.15 * (row / H)
            cv2.line(overlay, (0, row), (W, row),
                     (int(5 + 10*(row/H)), int(5 + 8*(row/H)), int(20 + 15*(row/H))), 1)
        cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

        # ── animated scanline shimmer ──
        scan_y = int((t * 180) % H)
        cv2.line(frame, (0, scan_y), (W, scan_y), (255, 255, 255), 1)
        cv2.line(frame, (0, (scan_y+2)%H), (W, (scan_y+2)%H), (180,180,180), 1)

        # ── decorative side bars ──
        bar_alpha = 0.5 + 0.5 * abs(math.sin(t * 1.2))
        bar_color = (int(0), int(200 * bar_alpha), int(255 * bar_alpha))
        cv2.rectangle(frame, (0, 0),   (8, H), bar_color, -1)
        cv2.rectangle(frame, (W-8, 0), (W, H), bar_color, -1)

        # ── top decorative line ──
        cv2.line(frame, (40, 80), (W-40, 80), (0, 180, 255), 1)
        cv2.line(frame, (40, 83), (W-40, 83), (0, 80, 120), 1)

        # ── animated fruit icons across top ──
        from game_objects import draw_fruit, FRUIT_CONFIGS
        icon_fruits = [
            ((0,215,255),  (120,240,255), "circle"),
            ((0,200,220),  (120,240,255), "oval"),
            ((50,180,60),  (120,220,100),"circle"),
            ((0,140,255),  (100,200,255),"circle"),
            ((180,40,130), (220,120,200),"circle"),
        ]
        for i, (bc, sc, sh) in enumerate(icon_fruits):
            ix = 160 + i * 240
            iy = int(135 + 12 * math.sin(t * 2 + i * 1.2))
            draw_fruit(frame, ix, iy, 28, bc, sc, sh)

        # ── TITLE — big glowing letters ──
        title   = "GESTURE FRUIT NINJA"
        glow_c  = int(160 + 95 * abs(math.sin(t * 1.5)))
        # glow halo
        for offset in [(3,3),(-3,3),(3,-3),(-3,-3),(0,4),(0,-4),(4,0),(-4,0)]:
            cv2.putText(frame, title,
                        (178 + offset[0], 248 + offset[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.1,
                        (0, glow_c//3, glow_c//2), 8)
        # main title
        cv2.putText(frame, title, (178, 248),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.1, (0, glow_c, 255), 4, cv2.LINE_AA)

        # ── subtitle underline ──
        cv2.line(frame, (178, 262), (1102, 262), (0, glow_c//2, 180), 2)

        # ── HOW TO PLAY panel ──
        px, py, pw, ph = 300, 290, 680, 210
        panel = frame.copy()
        cv2.rectangle(panel, (px, py), (px+pw, py+ph), (10, 10, 35), -1)
        cv2.addWeighted(panel, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (px, py), (px+pw, py+ph), (0, 100, 180), 2)

        shadow_text(frame, "HOW  TO  PLAY",
                    (px+220, py+38), 1.1, (0, 220, 255), 2)
        cv2.line(frame, (px+20, py+50), (px+pw-20, py+50), (0,80,140), 1)

        tips = [
            ("index finger", "Move your index finger to SLICE fruits"),
            ("bomb",         "Avoid the BOMBS or it's game over!"),
            ("combo",        "Slice fast in a row for COMBO bonus points"),
            ("score",        "Top 10 scores are saved to leaderboard"),
        ]
        icons_color = [
            (0, 220, 100),
            (0, 60, 255),
            (0, 200, 255),
            (255, 200, 60),
        ]
        for i, ((icon, tip), col) in enumerate(zip(tips, icons_color)):
            ty = py + 85 + i * 38
            cv2.circle(frame, (px+30, ty-6), 8, col, -1, cv2.LINE_AA)
            shadow_text(frame, tip, (px+52, ty), 0.72, (220,220,220), 1)

        # ── pulsing START button ──
        btn_pulse = 0.7 + 0.3 * abs(math.sin(t * 2.5))
        btn_col   = (int(0), int(200*btn_pulse), int(255*btn_pulse))
        bx, by    = 440, 535
        cv2.rectangle(frame, (bx-10, by-38), (bx+400, by+14), (20,20,50), -1)
        cv2.rectangle(frame, (bx-10, by-38), (bx+400, by+14), btn_col, 2)
        shadow_text(frame, "Press  S  to  Start",
                    (bx, by), 1.4, btn_col, 3)

        # ── bottom credit line ──
        shadow_text(frame, "Hand Gesture Controlled  |  Built with OpenCV + MediaPipe",
                    (230, 695), 0.6, (80, 80, 100), 1)

        cv2.imshow("Gesture Slicer", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            sfx.play_tick()
            reset_game()
            game_state = "playing"
        if key == 27:
            break
        continue


    # ════════════════════════════════
    #  NAME ENTRY  (after game over)
    # ════════════════════════════════
    if game_state == "name_entry":
        dim_frame(frame, 0.6)

        is_hs = is_high_score(score)
        if is_hs:
            shadow_text(frame, "NEW HIGH SCORE!", (390, 200), 1.8, (0, 215, 255), 4)

        shadow_text(frame, f"Your Score: {score}", (450, 270), 1.4, (255,255,255), 3)
        shadow_text(frame, "Enter your name:", (430, 340), 1.0, (180,180,180), 2)

        # Name box
        box_x, box_y = 390, 360
        cv2.rectangle(frame, (box_x, box_y), (box_x+500, box_y+55), (40,40,80), -1)
        cv2.rectangle(frame, (box_x, box_y), (box_x+500, box_y+55), (80,160,255), 2)

        # Blinking cursor
        cursor = "_" if int(pulse_t * 2) % 2 == 0 else " "
        shadow_text(frame, player_name + cursor, (box_x+14, box_y+40),
                    1.2, (0, 255, 220), 2)

        shadow_text(frame, "Press ENTER to save  |  ESC to skip",
                    (320, 470), 0.8, (140,140,140), 1)

        cv2.imshow("Gesture Slicer", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 13:   # ENTER — save and show leaderboard
            if player_name.strip():
                new_top = save_score(player_name, score)
                if new_top:
                    sfx.play_highscore()
                else:
                    sfx.play_tick()
            game_state = "leaderboard"

        elif key == 27:   # ESC — skip name entry
            game_state = "leaderboard"

        elif key == 8:    # BACKSPACE
            player_name = player_name[:-1]

        elif 32 <= key <= 126 and len(player_name) < 12:
            player_name += chr(key)

        continue


    # ════════════════════════════════
    #  LEADERBOARD
    # ════════════════════════════════
    if game_state == "leaderboard":
        draw_leaderboard(frame, score, pulse_t)
        cv2.imshow("Gesture Slicer", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            sfx.play_tick()
            player_name = ""
            reset_game()
            game_state = "playing"
        if key == 27:
            break
        continue


    # ════════════════════════════════
    #  PLAYING
    # ════════════════════════════════

    # Trail
    if finger_position:
        if prev_pos is None:
            trail_points.append(finger_position)
        else:
            dist = math.hypot(finger_position[0]-prev_pos[0],
                              finger_position[1]-prev_pos[1])
            if dist > 6:
                trail_points.append(finger_position)
            elif dist < 4:
                trail_points.clear()
        prev_pos = finger_position
    else:
        trail_points.clear()
        prev_pos = None


    # Spawn
    if time.time() - last_spawn > random.uniform(0.8, 1.3):
        vegetables.append(Vegetable())
        last_spawn = time.time()

    if time.time() - last_bomb_spawn > 3.5:
        bombs.append(Bomb())
        last_bomb_spawn = time.time()


    # Bombs
    for bomb in bombs[:]:
        bomb.update()
        bomb.draw(frame)
        if finger_position and bomb.check_hit(finger_position):
            sfx.play_bomb()
            game_state  = "name_entry"
            player_name = ""
            trail_points.clear()


    # Vegetables
    new_vegetables = []
    for veg in vegetables:
        veg.update()
        veg.draw(frame)

        if finger_position and veg.check_slice(finger_position):
            score  += 1 + combo
            combo  += 1

            # Sound: combo ≥ 3 → arpeggio, else slice swoosh
            if combo >= 3 and combo != prev_combo:
                sfx.play_combo()
            else:
                sfx.play_slice()
            prev_combo = combo

            for _ in range(22):
                particles.append(Particle(veg.x, veg.y, veg.body_color))
            new_vegetables.append(Vegetable())
            continue

        if veg.y > 800:
            combo      = 0
            prev_combo = 0
            new_vegetables.append(Vegetable())
        else:
            new_vegetables.append(veg)

    vegetables = new_vegetables


    # Particles
    particles = [p for p in particles if not p.is_dead()]
    for p in particles:
        p.update()
        p.draw(frame)


    # Trail (on top)
    draw_glow_trail(frame, trail_points)


    # HUD
    shadow_text(frame, f"Score: {score}", (30, 60),  1.5, (255,255,255), 3)
    shadow_text(frame, f"Combo: x{combo}", (30, 110), 1.1, (0,255,220), 2)

    if combo >= 3:
        glow = int(180 + 75 * math.sin(pulse_t * 4))
        shadow_text(frame, f"COMBO  x{combo}!",
                    (480, 160), 2.0, (0, glow, 255), 4)


    cv2.imshow("Gesture Slicer", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()