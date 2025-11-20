"""
math_adventure_full_gui_final.py
Complete Math Adventure GUI with:
- AI-like question generator
- Monster images & animations (fallback shapes)
- Attack animations (projectile + shake)
- Dark/Light theme toggle
- Learning mode (no HP loss)
- Combo / streak system
- Monster skills per level
- Difficulty modes (affect timer)
- Highscore persistence (highscore.txt)
Requires only Python standard library. Pillow optional for image resizing
"""

import tkinter as tk
from tkinter import messagebox
import random
import os
import math
import time

# Try importing PIL for robust image resizing; optional
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

HIGHSCORE_FILE = "highscore.txt"
MAX_LEVEL = 5

# Candidate image filenames (include ones you uploaded)
IMAGE_CANDIDATES = {
    1: ["slime.png", "ea604cdf-61ea-4474-bc15-c0cc8d00ecaf.png", "/mnt/data/ea604cdf-61ea-4474-bc15-c0cc8d00ecaf.png"],
    2: ["goblin.png", "87d49896-b060-4201-8235-b724f5b59c62.png", "/mnt/data/87d49896-b060-4201-8235-b724f5b59c62.png"],
    3: ["fluffy.png", "044147b5-4f8c-43de-9358-bf0bafc90d91.png", "/mnt/data/044147b5-4f8c-43de-9358-bf0bafc90d91.png"],
    4: ["monster4.png"],
    5: ["finalboss.png", "e48733d8-6661-44ba-9618-413ba743f6a4.png", "/mnt/data/e48733d8-6661-44ba-9618-413ba743f6a4.png"]
}

# Difficulty timers (seconds per question)
DIFFICULTY_TIMER = {
    "Easy": 15,
    "Normal": 10,
    "Hard": 7,
    "Nightmare": 4
}

# Monster skill descriptions (used for flavor & simple effects)
MONSTER_SKILLS = {
    1: {"name": "Slime", "skill": "No special skill"},
    2: {"name": "Goblin", "skill": "Counterattack chance (20%) on hit"},
    3: {"name": "Fluffy", "skill": "Shield (30% chance to block 1 damage)"},
    4: {"name": "Golem", "skill": "Slow (reduces your next question time by 2s)"},
    5: {"name": "Dark Demon", "skill": "Boss: double HP, faster timer"}
}
# Debug cek apakah folder benar
print(os.getcwd())
print(os.path.exists("assets/slime.png"))

# Utility: load first existing image from candidate list, optionally resize
def load_image_try(candidates, size=None):
    for p in candidates:
        if os.path.exists(p):
            try:
                if PIL_AVAILABLE and size is not None:
                    img = Image.open(p).convert("RGBA")
                    img = img.resize(size, Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                else:
                    # tkinter PhotoImage will fail for formats not supported; still try
                    return tk.PhotoImage(file=p)
            except Exception:
                continue
    return None

# AI-like question generator
def ai_generate_question(level):
    """
    Local 'AI' generator: creates varied questions depending on level.
    Returns (question_text, answer_value)
    """
    # Increase complexity with level
    # Level 1-2: simple +/-
    if level <= 2:
        a = random.randint(1, 20 * level)
        b = random.randint(1, 20 * level)
        op = random.choice(["+", "-"])
        q = f"{a} {op} {b}"
        ans = eval(q)

    # Level 3: mixed with multiplication and small parentheses
    elif level == 3:
        a = random.randint(2, 40)
        b = random.randint(2, 30)
        c = random.randint(1, 12)
        op1 = random.choice(["+", "-", "*"])
        op2 = random.choice(["+", "-", "*"])
        q = f"({a} {op1} {b}) {op2} {c}"
        ans = eval(q)

    # Level 4: include division (clean) and modulo sometimes
    elif level == 4:
        op = random.choice(["+", "-", "*", "/"])
        if op == "/":
            # ensure integer division result
            b = random.randint(2, 12)
            result = random.randint(2, 12)
            a = result * b
            q = f"{a} / {b}"
            ans = eval(q)
        else:
            a = random.randint(10, 120)
            b = random.randint(2, 30)
            q = f"{a} {op} {b}"
            ans = eval(q)

    # Level 5: boss complexity - nested operations, power, modulo, etc.
    else:
        pattern = random.choice([
            lambda: f"({random.randint(20,150)} + {random.randint(5,80)}) * {random.randint(2,6)}",
            lambda: f"{random.randint(4,18)}**2 - {random.randint(1,50)}",
            lambda: f"({random.randint(30,200)} / {random.randint(2,20)}) + {random.randint(1,50)}",
            lambda: f"({random.randint(20,120)} - {random.randint(1,60)}) * {random.randint(2,8)}",
            lambda: f"({random.randint(50,200)} % {random.randint(2,20)}) + {random.randint(1,40)}"
        ])
        q = pattern()
        try:
            ans = eval(q)
        except Exception:
            # fallback to simpler expression
            a = random.randint(20, 200); b = random.randint(2, 50)
            q = f"{a} + {b}"
            ans = eval(q)

    # Normalize floats that are integers
    if isinstance(ans, float) and ans.is_integer():
        ans = int(ans)

    return q, ans

# Main App
class MathAdventureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Math Adventure - Final")
        self.root.geometry("900x660")
        self.root.configure(bg="#111218")  # dark theme default

        # Game variables
        self.player_name = ""
        self.level = 1
        self.max_player_hp = 5
        self.player_hp = self.max_player_hp
        self.enemy_hp = 3
        self.score = 0
        self.combo = 0
        self.learning_mode = False
        self.theme = "dark"  # or "light"
        self.difficulty = "Normal"
        self.time_left = 0
        self.timer_job = None
        self.anim_job = None
        self.projectile_job = None

        # Load monster images (with fallback)
        self.monster_imgs = {}
        for lvl in range(1, MAX_LEVEL + 1):
            cand = IMAGE_CANDIDATES.get(lvl, [])
            img = load_image_try(cand, size=(300,280) if PIL_AVAILABLE else None)
            self.monster_imgs[lvl] = img

        # Build UI frames
        self.frame_menu = tk.Frame(self.root, bg=self._bg())
        self.frame_game = tk.Frame(self.root, bg=self._bg())
        self.frame_over = tk.Frame(self.root, bg=self._bg())

        self._build_menu()
        self._build_game()
        self._build_over()

        self.show_menu()

    # ---------------- theme helper ----------------
    def _bg(self):
        return "#111218" if self.theme == "dark" else "#f3f3f3"

    def _fg(self):
        return "white" if self.theme == "dark" else "#111"

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        # update backgrounds of frames
        for f in (self.frame_menu, self.frame_game, self.frame_over):
            f.configure(bg=self._bg())
        # rebuild or update existing widgets color
        self.show_menu()

    # ---------------- menu UI ----------------
    def _build_menu(self):
        f = self.frame_menu
        f.pack_propagate(False)
        # top title
        title = tk.Label(f, text="⚔️ Math Adventure", font=("Helvetica", 34, "bold"), fg=self._fg(), bg=self._bg())
        title.pack(pady=(30,8))

        subtitle = tk.Label(f, text="Belajar sambil bermain — jawab cepat, kalahkan monster!", font=("Arial", 12), fg="#a9aab0", bg=self._bg())
        subtitle.pack(pady=(0,12))

        # name entry
        name_frame = tk.Frame(f, bg=self._bg())
        name_frame.pack(pady=10)
        tk.Label(name_frame, text="Nama:", fg=self._fg(), bg=self._bg()).pack(side=tk.LEFT, padx=(0,6))
        self.entry_name = tk.Entry(name_frame, font=("Arial", 14), width=28)
        self.entry_name.pack(side=tk.LEFT)

        # difficulty selector
        diff_frame = tk.Frame(f, bg=self._bg())
        diff_frame.pack(pady=(12,6))
        tk.Label(diff_frame, text="Difficulty:", fg=self._fg(), bg=self._bg()).pack(side=tk.LEFT, padx=(0,8))
        self.diff_var = tk.StringVar(value=self.difficulty)
        diff_menu = tk.OptionMenu(diff_frame, self.diff_var, *DIFFICULTY_TIMER.keys())
        diff_menu.config(width=10)
        diff_menu.pack(side=tk.LEFT)

        # buttons
        btn_frame = tk.Frame(f, bg=self._bg())
        btn_frame.pack(pady=18)
        tk.Button(btn_frame, text="▶ Start", font=("Arial", 14), width=18, bg="#4e8cff", fg="white", command=self.start_game).pack(pady=6)
        tk.Button(btn_frame, text="📘 Learning Mode", font=("Arial", 12), width=18, bg="#6aa84f", fg="white", command=self.start_learning_mode).pack(pady=6)
        tk.Button(btn_frame, text="🎨 Toggle Theme", font=("Arial", 12), width=18, bg="#6b6b6b", fg="white", command=self.toggle_theme).pack(pady=6)

        # highscore
        hs_name, hs_score = self._load_highscore()
        tk.Label(f, text=f"Highscore: {hs_name} — {hs_score}", fg="#ffd26b", bg=self._bg(), font=("Arial", 12)).pack(pady=(18,4))

        # info
        tk.Label(f, text="(Letakkan gambar monster di folder yang sama, jika ingin menampilkan gambar)", fg="#9aa0a8", bg=self._bg(), font=("Arial", 10)).pack(pady=(6,12))

    def show_menu(self):
        self._hide_all_frames()
        self.frame_menu.pack(fill="both", expand=True)

    # ---------------- game UI ----------------
    def _build_game(self):
        f = self.frame_game
        f.pack_propagate(False)

        top = tk.Frame(f, bg=self._bg())
        top.pack(fill="x", pady=6)
        self.lbl_player = tk.Label(top, text="Player: -", fg=self._fg(), bg=self._bg(), font=("Arial", 12))
        self.lbl_player.pack(side="left", padx=10)
        self.lbl_level = tk.Label(top, text="Level: 1", fg=self._fg(), bg=self._bg(), font=("Arial", 12))
        self.lbl_level.pack(side="left", padx=10)
        self.lbl_score = tk.Label(top, text="Score: 0", fg="#ffd26b", bg=self._bg(), font=("Arial", 12))
        self.lbl_score.pack(side="right", padx=12)

        mid = tk.Frame(f, bg=self._bg())
        mid.pack(expand=True, fill="both", pady=10, padx=10)

        left = tk.Frame(mid, bg=self._bg())
        left.pack(side="left", padx=8, pady=6)

        # canvas for monster + animations
        self.canvas = tk.Canvas(left, width=420, height=360, bg="#1b1b25", highlightthickness=0)
        self.canvas.pack()
        # hp bars under canvas
        hp_frame = tk.Frame(left, bg=self._bg())
        hp_frame.pack(pady=6)
        tk.Label(hp_frame, text="HP Kamu:", fg="#9af78b", bg=self._bg()).pack(anchor="w")
        self.player_hp_canvas = tk.Canvas(hp_frame, width=340, height=18, bg="#333", highlightthickness=0)
        self.player_hp_canvas.pack(pady=4)
        tk.Label(hp_frame, text="HP Musuh:", fg="#ff8b8b", bg=self._bg()).pack(anchor="w")
        self.enemy_hp_canvas = tk.Canvas(hp_frame, width=340, height=18, bg="#333", highlightthickness=0)
        self.enemy_hp_canvas.pack(pady=4)

        right = tk.Frame(mid, bg=self._bg())
        right.pack(side="left", padx=12, pady=6, fill="y")

        self.lbl_question = tk.Label(right, text="Soal muncul di sini", font=("Arial", 24, "bold"), fg=self._fg(), bg=self._bg(), wraplength=360, justify="left")
        self.lbl_question.pack(pady=(6,14))

        self.entry_answer = tk.Entry(right, font=("Arial", 18), width=12, justify="center")
        self.entry_answer.pack(pady=6)
        self.entry_answer.bind("<Return>", lambda e: self.submit_answer())

        btn_row = tk.Frame(right, bg=self._bg())
        btn_row.pack(pady=8)
        self.btn_submit = tk.Button(btn_row, text="Jawab", font=("Arial", 14), bg="#4e8cff", fg="white", command=self.submit_answer)
        self.btn_submit.pack(side="left", padx=6)
        tk.Button(btn_row, text="Skip (−1 HP)", font=("Arial", 11), bg="#6b6b6b", fg="white", command=self.skip_question).pack(side="left", padx=6)

        self.lbl_feedback = tk.Label(right, text="", fg="#ffd26b", bg=self._bg(), font=("Arial", 12))
        self.lbl_feedback.pack(pady=6)

        self.lbl_timer = tk.Label(right, text="Waktu: -", fg="#66d9ef", bg=self._bg(), font=("Arial", 16))
        self.lbl_timer.pack(pady=8)

        ctrl = tk.Frame(right, bg=self._bg())
        ctrl.pack(pady=10)
        tk.Button(ctrl, text="↺ Restart", command=self.restart_game, bg="#6b6b6b", fg="white").pack(side="left", padx=6)
        tk.Button(ctrl, text="← Menu", command=self.back_to_menu, bg="#6b6b6b", fg="white").pack(side="left", padx=6)

    def show_game(self):
        self._hide_all_frames()
        self.frame_game.pack(fill="both", expand=True)

    # ---------------- over UI ----------------
    def _build_over(self):
        f = self.frame_over
        tk.Label(f, text="GAME OVER", font=("Arial", 34, "bold"), fg="#ff6b6b", bg=self._bg()).pack(pady=30)
        self.lbl_final = tk.Label(f, text="Skor: 0", font=("Arial", 16), fg=self._fg(), bg=self._bg())
        self.lbl_final.pack(pady=6)
        tk.Button(f, text="Main Lagi", font=("Arial", 14), bg="#4e8cff", fg="white", command=self.restart_game).pack(pady=6)
        tk.Button(f, text="Kembali ke Menu", font=("Arial", 14), bg="#6b6b6b", fg="white", command=self.show_menu).pack(pady=6)

    # ---------------- flow control ----------------
    def _hide_all_frames(self):
        for fr in (self.frame_menu, self.frame_game, self.frame_over):
            fr.pack_forget()
        self._cancel_timer()
        self._cancel_animation()
        self._cancel_projectile()

    def start_game(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Nama kosong", "Masukkan nama pemain dulu.")
            return
        self.player_name = name
        self.learning_mode = False
        self.difficulty = self.diff_var.get() if hasattr(self, "diff_var") else "Normal"
        self._reset_game_state()
        self.show_game()

    def start_learning_mode(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Nama kosong", "Masukkan nama pemain dulu.")
            return
        self.player_name = name
        self.learning_mode = True
        self.difficulty = self.diff_var.get() if hasattr(self, "diff_var") else "Normal"
        self._reset_game_state()
        self.show_game()

    def _reset_game_state(self):
        self.level = 1
        self.player_hp = self.max_player_hp
        self.enemy_hp = 3 + (self.level - 1) * 2
        self.score = 0
        self.combo = 0
        self._spawn_monster()
        self._next_question()
        self._update_ui_all()

    def restart_game(self):
        if messagebox.askyesno("Restart", "Mulai ulang permainan?"):
            self._reset_game_state()
            self.show_game()

    def back_to_menu(self):
        if messagebox.askyesno("Kembali", "Kembali ke menu? Progress akan hilang."):
            self._hide_all_frames()
            self.show_menu()

    # ---------------- monster / spawn / animations ----------------
    def _spawn_monster(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 300, 420, 360, fill="#0f0f13", outline="#0f0f13")
        img = self.monster_imgs.get(self.level)
        if img:
            # center image
            self.monster_id = self.canvas.create_image(210, 150, image=img)
            self.monster_x = 210
        else:
            # draw placeholder circle
            self.monster_id = self.canvas.create_oval(110, 30, 310, 230, fill="#3344aa", outline="")
            self.monster_x = 210
        # show skill text
        skill = MONSTER_SKILLS.get(self.level, {}).get("skill", "")
        self.canvas_skill_text = self.canvas.create_text(210, 270, text=skill, fill="#d9d9d9", font=("Arial", 10))
        # start bobbing animation
        self._cancel_animation()
        self._animate_monster_bob()

    def _animate_monster_bob(self):
        # simple left-right bobbing using after
        dx = 6
        try:
            self.canvas.move(self.monster_id, dx, 0)
            self.monster_x += dx
            if abs(self.monster_x - 210) > 50:
                # reverse direction beyond threshold
                self.canvas.move(self.monster_id, -2*dx, 0)
                self.monster_x -= 2*dx
                dx = -dx
        except Exception:
            pass
        # schedule next bob (store id)
        self.anim_job = self.canvas.after(160, self._animate_monster_bob)

    def _cancel_animation(self):
        if hasattr(self, "anim_job") and self.anim_job:
            try:
                self.canvas.after_cancel(self.anim_job)
            except Exception:
                pass
            self.anim_job = None

    def _blink_monster(self, times=4):
        # change opacity/flash by drawing overlay rectangle quickly
        def do_blink(i=0):
            if i >= times:
                return
            # flash overlay
            overlay = self.canvas.create_rectangle(110, 30, 310, 230, fill="#ffffff", stipple="gray50", outline="")
            self.canvas.after(80, lambda: self.canvas.delete(overlay))
            self.canvas.after(120, lambda: do_blink(i+1))
        do_blink()

    def _shake_screen(self):
        # small window shake (no time.sleep)
        orig = self.root.geometry()
        offsets = ["+10+0", "-10+0", "+6+0", "-6+0", "+0+0"]
        base = orig.split("+")[0]  # window size part
        def do_shake(i=0):
            if i >= len(offsets):
                self.root.geometry(orig)
                return
            # apply offset by moving window slightly relative (works on some platforms)
            try:
                self.root.update()
                self.root.geometry(orig.split("+")[0] + offsets[i])
            except Exception:
                pass
            self.root.after(40, lambda: do_shake(i+1))
        do_shake()

    # ---------------- projectile attack animation ----------------
    def _launch_projectile(self, from_player=True):
        # draw a small circle moving toward monster (from left) or from monster to left when counterattack
        start_x = 40 if from_player else 210
        start_y = 200 if from_player else 150
        target_x = 210 if from_player else 40
        target_y = 150 if from_player else 200
        proj = self.canvas.create_oval(start_x-8, start_y-8, start_x+8, start_y+8, fill="#ffdd55", outline="")
        steps = 20
        dx = (target_x - start_x) / steps
        dy = (target_y - start_y) / steps

        def step(i=0):
            if i >= steps:
                try:
                    self.canvas.delete(proj)
                except Exception:
                    pass
                return
            try:
                self.canvas.move(proj, dx, dy)
            except Exception:
                pass
            self.projectile_job = self.canvas.after(25, lambda: step(i+1))
        step()

    def _cancel_projectile(self):
        if hasattr(self, "projectile_job") and self.projectile_job:
            try:
                self.canvas.after_cancel(self.projectile_job)
            except Exception:
                pass
            self.projectile_job = None

    # ---------------- question & timer ----------------
    def _next_question(self):
        self.current_question, self.current_answer = ai_generate_question(self.level)
        # display question
        self.lbl_question.config(text=f"{self.current_question} = ?")
        self.entry_answer.delete(0, tk.END)
        self.lbl_feedback.config(text="")
        # set timer from difficulty, adjusted by monster skill maybe
        base_time = DIFFICULTY_TIMER.get(self.difficulty, 10)
        # If monster skill is Slow (level 4), reduce player time on first hit? implement as small effect: level 4 reduces time by 2 for this question
        if self.level == 4 and random.random() < 0.25:
            # 25% chance to apply slow on next question (flavor)
            base_time = max(3, base_time - 2)
        self.time_left = base_time
        self._start_timer()

    def _start_timer(self):
        self._cancel_timer()
        self.lbl_timer.config(text=f"Waktu: {self.time_left}s")
        self._timer_tick()

    def _timer_tick(self):
        self.lbl_timer.config(text=f"Waktu: {self.time_left}s")
        if self.time_left <= 0:
            self._on_timeout()
            return
        self.time_left -= 1
        self.timer_job = self.root.after(1000, self._timer_tick)

    def _cancel_timer(self):
        if hasattr(self, "timer_job") and self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except Exception:
                pass
            self.timer_job = None

    def _on_timeout(self):
        # time out: penalize player (unless learning mode)
        self.lbl_feedback.config(text="⏳ Waktu habis! Kamu terkena serangan.", fg="#ffb86b")
        if not self.learning_mode:
            self.player_hp -= 1
        # small shake
        self._shake_screen()
        self._draw_hp_bars()
        if self.player_hp <= 0 and not self.learning_mode:
            self._end_game(False)
            return
        # next question
        self.root.after(600, self._next_question)

    # ---------------- submit / skip ----------------
    def submit_answer(self):
        txt = self.entry_answer.get().strip()
        if txt == "":
            return
        # cancel timer while checking
        self._cancel_timer()
        try:
            # accept integer or float answers
            user_val = float(txt) if "." in txt else int(txt)
        except Exception:
            user_val = None

        correct = False
        if user_val is not None:
            if isinstance(self.current_answer, float):
                correct = abs(user_val - self.current_answer) < 0.01
            else:
                try:
                    correct = int(user_val) == int(self.current_answer)
                except Exception:
                    correct = False

        if correct:
            # correct answer: compute damage based on combo
            self.combo += 1
            dmg = 1 + (self.combo // 3)  # every 3 combo +1 damage
            self.lbl_feedback.config(text=f"💥 Benar! Damage {dmg} (Combo {self.combo})", fg="#7efc6a")
            # show projectile
            self._launch_projectile(from_player=True)
            # apply damage (consider enemy skill: Fluffy shield at level 3)
            blocked = False
            if self.level == 3 and random.random() < 0.30:
                # fluffy shield blocks 1 damage
                blocked = True
            if not blocked:
                self.enemy_hp -= dmg
            else:
                self.lbl_feedback.config(text="🛡️ Musuh memblokir serangan!", fg="#ffd26b")
                # still award small score but no HP damage
                self.score += 2

            # Goblin counterattack skill
            if self.level == 2 and random.random() < 0.20:
                # goblin counterattacks immediately
                self.lbl_feedback.config(text="💥 Kamu kena serangan balik oleh Goblin!", fg="#ff9a7a")
                self._launch_projectile(from_player=False)
                if not self.learning_mode:
                    self.player_hp -= 1

            # Golem (level 4) may reduce your next time - simulated earlier by random effect
            # increase score
            self.score += 10 * self.level
            self._blink_monster()
            self._draw_hp_bars()
            # check enemy death
            if self.enemy_hp <= 0:
                self.root.after(350, self._on_enemy_defeated)
            else:
                self.root.after(450, self._next_question)

        else:
            # wrong
            self.combo = 0
            self.lbl_feedback.config(text=f"❌ Salah! Jawaban benar: {self.current_answer}", fg="#ff6b6b")
            # penalty
            if not self.learning_mode:
                self.player_hp -= 1
            # shake & counter projectile
            self._shake_screen()
            self._draw_hp_bars()
            if self.player_hp <= 0 and not self.learning_mode:
                self._end_game(False)
                return
            self.root.after(500, self._next_question)

    def skip_question(self):
        if not messagebox.askyesno("Lewati", "Lewati soal ini? Kamu kehilangan 1 HP."):
            return
        if not self.learning_mode:
            self.player_hp -= 1
        self.lbl_feedback.config(text="Kamu melewatkan soal (−1 HP).", fg="#ffc36b")
        self._draw_hp_bars()
        if self.player_hp <= 0 and not self.learning_mode:
            self._end_game(False)
            return
        self.root.after(400, self._next_question)

    # ---------------- enemy defeated / level up ----------------
    def _on_enemy_defeated(self):
        # award bonus
        bonus = 20 * self.level
        self.score += bonus
        messagebox.showinfo("Level Cleared", f"Kamu mengalahkan monster level {self.level}!\nBonus skor: {bonus}")
        # next level or win
        self.level += 1
        self.combo = 0
        if self.level > MAX_LEVEL:
            self._end_game(True)
            return
        # reset player HP optionally (here we reset to max for new level)
        self.player_hp = self.max_player_hp
        self.enemy_hp = 3 + (self.level - 1) * 2
        self._spawn_monster()
        self._draw_hp_bars()
        self._next_question()

    # ---------------- drawing HP bars & UI ----------------
    def _draw_hp_bars(self):
        # player HP
        self.player_hp_canvas.delete("all")
        w = 340
        ratio = max(0, self.player_hp) / self.max_player_hp
        self.player_hp_canvas.create_rectangle(0, 0, w, 18, fill="#222", outline="#222")
        self.player_hp_canvas.create_rectangle(0, 0, int(w * ratio), 18, fill="#6ef07a", outline="")
        self.player_hp_canvas.create_text(w//2, 9, text=f"{self.player_hp}/{self.max_player_hp}", fill="#000", font=("Arial", 10))

        # enemy HP
        self.enemy_hp_canvas.delete("all")
        enemy_max = 3 + (self.level - 1) * 2
        ratio_e = max(0, self.enemy_hp) / enemy_max
        self.enemy_hp_canvas.create_rectangle(0, 0, w, 18, fill="#222", outline="#222")
        self.enemy_hp_canvas.create_rectangle(0, 0, int(w * ratio_e), 18, fill="#ff8b8b", outline="")
        self.enemy_hp_canvas.create_text(w//2, 9, text=f"{self.enemy_hp}/{enemy_max}", fill="#000", font=("Arial", 10))

        # update labels
        self.lbl_player.config(text=f"Player: {self.player_name}")
        self.lbl_level.config(text=f"Level: {self.level}")
        self.lbl_score.config(text=f"Score: {self.score}")

    # ---------------- end game ----------------
    def _end_game(self, won):
        self._cancel_timer()
        self._cancel_animation()
        self._cancel_projectile()
        # show final and save highscore if beaten
        hs_name, hs_score = self._load_highscore()
        if self.score > hs_score:
            # write name|score
            try:
                with open(HIGHSCORE_FILE, "w") as f:
                    f.write(f"{self.player_name}|{self.score}")
            except Exception:
                pass
            new_hs = True
        else:
            new_hs = False

        if won:
            msg = f"🏆 Kamu menaklukkan FINAL BOSS!\nSkor: {self.score}"
        else:
            msg = f"💀 Kamu kalah.\nSkor: {self.score}"

        if new_hs:
            msg += "\n\n🎉 NEW HIGHSCORE!"

        messagebox.showinfo("Game Over", msg)
        # show over screen with final score
        self.lbl_final.config(text=f"Skor: {self.score}")
        self._hide_all_frames()
        self.frame_over.pack(fill="both", expand=True)

    # ---------------- highscore ----------------
    def _load_highscore(self):
        if not os.path.exists(HIGHSCORE_FILE):
            return ("-", 0)
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                t = f.read().strip()
                if "|" in t:
                    name, sc = t.split("|", 1)
                    return (name, int(sc))
                else:
                    return ("-", int(t))
        except Exception:
            return ("-", 0)

    # ---------------- utility: update UI / next steps ----------------
    def _update_ui_all(self):
        self._draw_hp_bars()
        self.show_game()

    # ---------------- start next level and question orchestration ----------------
    def _next_question(self):
        self._next_question_internal()

    def _next_question_internal(self):
        self._cancel_timer()
        # ensure enemy hp set
        self.enemy_hp = max(1, self.enemy_hp)
        self._draw_hp_bars()
        self._next_question_observe()

    def _next_question_observe(self):
        # generate new question and start timer
        self.current_question, self.current_answer = ai_generate_question(self.level)
        self.lbl_question.config(text=f"{self.current_question} = ?")
        self.entry_answer.delete(0, tk.END)
        self.lbl_feedback.config(text="")
        # set timer by difficulty (monster 5 boss reduces time)
        base_time = DIFFICULTY_TIMER.get(self.difficulty, 10)
        if self.level == 5:
            base_time = max(3, base_time - 3)
        self.time_left = base_time
        self._start_timer()

    # ---------------- helper to show game frame ----------------
    def show_game(self):
        self._hide_all_frames()
        self.frame_game.pack(fill="both", expand=True)

    # ---------------- run spawn/next on reset / prepare ----------------
    def _start_level(self):
        self.player_hp = self.max_player_hp
        self.enemy_hp = 3 + (self.level - 1) * 2
        self._spawn_monster()
        self._next_question()
        self._update_ui_all()

    # ---------------- helper to spawn & next question used externally ----------------
    def prepare_level(self):
        self._start_level()

    # ---------------- cancel helpers ----------------
    def _cancel_all(self):
        self._cancel_timer()
        self._cancel_animation()
        self._cancel_projectile()

# --------------------- RUN APP ---------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MathAdventureApp(root)
    # pack main UI frames into root (frames themselves are shown/hidden)
    app.frame_menu.pack(fill="both", expand=True)
    root.mainloop()
