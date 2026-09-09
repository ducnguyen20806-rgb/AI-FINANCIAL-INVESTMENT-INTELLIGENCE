"""
Login Form Animation - phien ban Python (Tkinter)
Keo day den de bat/tat -> nen phong doi mau muot va form login hien ra.

Chay:  python login_lamp.py
Khong can cai them thu vien nao (tkinter co san trong Python).
"""

import tkinter as tk

# ---------- Cau hinh mau ----------
ROOM_OFF = "#121417"
ROOM_ON = "#1c1f24"
SHADE_OFF = "#26272a"
SHADE_ON = "#f3e6cd"
METAL_OFF = "#4a4b4e"
METAL_ON = "#9a9ca1"
CARD_OFF = "#16191d"
CARD_ON = "#2a2b28"
GOLD = "#d8b45f"
INK = "#f4f1ec"
MUTED = "#8d9099"

DURATION_MS = 600      # giong duration: 0.6 cua GSAP
FPS = 60

MAX_PULL = 85          # keo day xuong toi da bao nhieu px
PULL_THRESHOLD = 34    # keo qua muc nay thi den moi doi trang thai


# ---------- Tien ich mau ----------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def lerp_color(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex([a[i] + (b[i] - a[i]) * t for i in range(3)])


def ease_out(t):
    """Duong cong giam toc, cho chuyen dong mem hon tuyen tinh."""
    return 1 - (1 - t) ** 3


class Tween:
    """Mo phong gsap.to(): doi mau cua nhieu doi tuong trong duration ms."""

    def __init__(self, root):
        self.root = root
        self.job = None

    def to(self, targets, duration=DURATION_MS):
        """targets: list cac tuple (setter, mau_dau, mau_cuoi)"""
        if self.job:
            self.root.after_cancel(self.job)
            self.job = None

        steps = max(1, int(duration / (1000 / FPS)))
        delay = int(duration / steps)

        def step(i):
            t = ease_out(i / steps)
            for setter, start, end in targets:
                setter(lerp_color(start, end, t))
            if i < steps:
                self.job = self.root.after(delay, step, i + 1)
            else:
                self.job = None

        step(0)


class LampLogin:
    def __init__(self, root):
        self.root = root
        self.is_on = False
        self.tween = Tween(root)

        root.title("Login Form Animation — AI Financial Platform")
        root.geometry("900x560")
        root.configure(bg=ROOM_OFF)
        root.minsize(760, 520)

        self.canvas = tk.Canvas(root, bg=ROOM_OFF, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._draw_lamp()
        self._draw_form()

    # ---------- Ve cay den ----------
    def _draw_lamp(self):
        c = self.canvas

        # cot sang hat xuong (dung stipple de gia lam trong suot)
        self.beam = c.create_polygon(
            200, 205, 290, 205, 400, 500, 90, 500,
            fill=SHADE_ON, stipple="gray12", outline="", state="hidden",
        )

        # chao den
        self.shade = c.create_oval(150, 130, 340, 215, fill=SHADE_OFF, outline="")
        c.create_rectangle(150, 172, 340, 215, fill=SHADE_OFF, outline="", tags="shade_lower")
        self.shade_lower = "shade_lower"

        # than va de
        self.stem = c.create_rectangle(240, 212, 250, 380, fill=METAL_OFF, outline="")
        self.base = c.create_rectangle(200, 380, 290, 392, fill=METAL_OFF, outline="")

        # day keo + num
        self.cord_line = c.create_line(305, 200, 305, 258, fill="#7c7e83", width=2)
        self.knob = c.create_oval(298, 258, 312, 272, fill="#c98f4e", outline="")

        # vung bam rong hon cho de click
        self.hit = c.create_rectangle(288, 195, 322, 280, fill="", outline="")

        # trang thai keo day
        self.cord_rest_y = 258          # toa do y cua dau day luc nghi
        self.pull = 0                   # da keo xuong bao nhieu px
        self.dragging = False
        self.drag_start_y = 0
        self.snap_job = None

        for item in (self.cord_line, self.knob, self.hit):
            c.tag_bind(item, "<Button-1>", self.on_press)
            c.tag_bind(item, "<B1-Motion>", self.on_drag)
            c.tag_bind(item, "<ButtonRelease-1>", self.on_release)
            c.tag_bind(item, "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind(item, "<Leave>", lambda e: c.config(cursor=""))

        self.root.bind("<space>", self.pull_with_key)   # keo bang phim cach

    # ---------- Keo day ----------
    def set_pull(self, p):
        """Ve lai day va num o do dai da keo p px."""
        p = max(0, min(MAX_PULL, p))
        self.pull = p
        c = self.canvas
        c.coords(self.cord_line, 305, 200, 305, self.cord_rest_y + p)
        c.coords(self.knob, 298, self.cord_rest_y + p, 312, self.cord_rest_y + 14 + p)
        # vung bam di theo num de khong "tuot tay" khi keo
        c.coords(self.hit, 288, 195, 322, self.cord_rest_y + 22 + p)

    def on_press(self, event):
        if self.snap_job:
            self.root.after_cancel(self.snap_job)
            self.snap_job = None
        self.dragging = True
        self.drag_start_y = event.y - self.pull

    def on_drag(self, event):
        if not self.dragging:
            return
        self.set_pull(event.y - self.drag_start_y)

    def on_release(self, event=None):
        if not self.dragging:
            return
        self.dragging = False
        pulled_enough = self.pull > PULL_THRESHOLD
        self.snap_back(then=self.toggle if pulled_enough else None)

    def snap_back(self, then=None):
        """Day bat nguoc len, hoi nay mot chut roi dung lai."""
        start = self.pull
        steps = 14

        def step(i):
            t = i / steps
            # bat len co do nay nhe (overshoot)
            eased = (1 - ease_out(t)) - 0.12 * (1 - t) * (t > 0.55)
            self.set_pull(start * eased)
            if i < steps:
                self.snap_job = self.root.after(16, step, i + 1)
            else:
                self.snap_job = None
                self.set_pull(0)
                if then:
                    then()

        step(0)

    def pull_with_key(self, event=None):
        """Keo day bang phim cach, cho nguoi dung ban phim."""
        if self.dragging or self.snap_job:
            return
        self.set_pull(50)
        self.root.after(120, lambda: self.snap_back(then=self.toggle))

    # ---------- Ve form login ----------
    def _draw_form(self):
        c = self.canvas

        self.card = c.create_rectangle(
            520, 130, 840, 440, fill=CARD_OFF, outline="#232629", width=1
        )
        self.title = c.create_text(
            680, 175, text="Đăng Nhập Hệ Thống", fill=INK, font=("Segoe UI", 16, "bold")
        )
        self.lbl_user = c.create_text(
            552, 218, text="Tên đăng nhập", anchor="w", fill=MUTED, font=("Segoe UI", 9)
        )
        self.lbl_pass = c.create_text(
            552, 300, text="Mật khẩu", anchor="w", fill=MUTED, font=("Segoe UI", 9)
        )

        self.e_user = tk.Entry(
            self.root,
            bg="#1e2126",
            fg=INK,
            insertbackground=INK,
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightbackground="#2b2f35",
            highlightcolor=GOLD,
        )
        self.e_user.insert(0, "Admin")

        self.e_pass = tk.Entry(
            self.root,
            show="•",
            bg="#1e2126",
            fg=INK,
            insertbackground=INK,
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightbackground="#2b2f35",
            highlightcolor=GOLD,
        )
        self.e_pass.insert(0, "admin")

        self.btn = tk.Button(
            self.root, text="Đăng nhập & Mở Dashboard", command=self.sign_in,
            bg=GOLD, fg="#2a2110", activebackground="#e6c877",
            relief="flat", font=("Segoe UI", 11, "bold"), cursor="hand2",
        )

        # Hỗ trợ phím Enter để đăng nhập nhanh
        self.e_user.bind("<Return>", lambda _e: self.sign_in())
        self.e_pass.bind("<Return>", lambda _e: self.sign_in())

        self.w_user = c.create_window(680, 245, window=self.e_user, width=270, height=34)
        self.w_pass = c.create_window(680, 327, window=self.e_pass, width=270, height=34)
        self.w_btn = c.create_window(680, 395, window=self.btn, width=270, height=40)

        self.status = c.create_text(680, 425, text="", fill=MUTED, font=("Segoe UI", 9))

        self._set_form_visible(False)

    def _set_form_visible(self, visible):
        """An/hien toan bo khung login, ke ca khung nen va cac nhan."""
        state = "normal" if visible else "hidden"
        for item in (self.card, self.title, self.lbl_user, self.lbl_pass,
                     self.w_user, self.w_pass, self.w_btn, self.status):
            self.canvas.itemconfigure(item, state=state)

    # ---------- Bat / tat den ----------
    def toggle(self, event=None):
        self.is_on = not self.is_on
        c = self.canvas

        if self.is_on:
            self._set_form_visible(True)
            c.itemconfigure(self.beam, state="normal")
            c.itemconfigure(self.knob, fill="#f7e2a8")
            targets = [
                (lambda col: (self.root.configure(bg=col), c.configure(bg=col)),
                 ROOM_OFF, ROOM_ON),
                (lambda col: (c.itemconfigure(self.shade, fill=col),
                              c.itemconfigure(self.shade_lower, fill=col)),
                 SHADE_OFF, SHADE_ON),
                (lambda col: (c.itemconfigure(self.stem, fill=col),
                              c.itemconfigure(self.base, fill=col)),
                 METAL_OFF, METAL_ON),
                (lambda col: c.itemconfigure(self.card, fill=col), CARD_OFF, CARD_ON),
            ]
        else:
            self._set_form_visible(False)
            c.itemconfigure(self.beam, state="hidden")
            c.itemconfigure(self.knob, fill="#c98f4e")
            targets = [
                (lambda col: (self.root.configure(bg=col), c.configure(bg=col)),
                 ROOM_ON, ROOM_OFF),
                (lambda col: (c.itemconfigure(self.shade, fill=col),
                              c.itemconfigure(self.shade_lower, fill=col)),
                 SHADE_ON, SHADE_OFF),
                (lambda col: (c.itemconfigure(self.stem, fill=col),
                              c.itemconfigure(self.base, fill=col)),
                 METAL_ON, METAL_OFF),
                (lambda col: c.itemconfigure(self.card, fill=col), CARD_ON, CARD_OFF),
            ]

        self.tween.to(targets)

    def sign_in(self):
        user = self.e_user.get().strip()
        if not user:
            self.canvas.itemconfigure(self.status, text="Vui lòng nhập tên tài khoản.")
            return
        self.canvas.itemconfigure(self.status, text=f"Xin chào, {user}! Đang mở Dashboard...")
        import webbrowser
        self.root.after(700, lambda: webbrowser.open(f"http://localhost:8501/?auth=true&user={user}"))


if __name__ == "__main__":
    root = tk.Tk()
    LampLogin(root)
    root.mainloop()
