import os, threading, subprocess, shutil, tempfile
import base64
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import cv2
import numpy as np

APP="WoT Blitz AutoClip"
TANKS=["Velg tank…","Sheridan","Vickers Light","FV215b","FV215b 183","WZ-121","WZ-113","STB-1","90TP Lewandowskiego","Kranvagn","T95","HWK 12","Object 84","Skoda T 50","50TP Tyszkiewicza","Panther II","JPanther II","53TP Markowskiego","Panther","LTG","AMX 13 M24","Leo","T-34/100","Carro d'Assa","45TP Habicha","Ju-Nu","59-16","BUGI","40TP Habicha","Skoda P-JS","SDP 44 Burza","Bassotto","AC Ocelote","Mitsu 108","DS PZInz","SDP 40 Zadymka","Semovente M41","AC Highlander","T26E4","Lorraine 40t","AMX CDC","Edelweiss","Hafen","WZ Blaze","PZ IV S","AC IV Sentinel","Bretagne Panther","Y5 Firefly","Krupp-38(D)","T-25","Pz V/IV","Y5 T-34","XM66F","VK 168.01 (P)","T-34-3","50TP Prototyp","IS-3 Defender","Centurion Mk 5/1","Type 59","Prowler","Kunze Panzer","VK 45.03","Nameless","Vulcan","Lupus","Rudolph","Agent","U-Panzer","Icebreaker","Triumphant","SU-100Y","Explorer","Ox","Eraser BP44","P.43/06 SNN","Pudel","Pz IV Gargoyle","PZ.Sfl. IVc","KV-220","Nightmare","M3 Lee","Luchs","B2","DW2","A-32","Valentine Mk IX","Ke-Ho","Mark I Male"]
EXT={".mp4",".mkv",".avi",".mov",".webm",".ts",".m4v"}

def find_ffmpeg():
    """Find the bundled FFmpeg executable in both PyInstaller and source runs."""
    import sys
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys._MEIPASS) / "ffmpeg.exe")
        candidates.append(Path(sys.executable).resolve().parent / "ffmpeg.exe")
    else:
        candidates.append(Path(__file__).resolve().parent / "ffmpeg.exe")
        candidates.append(Path(__file__).resolve().parent / "build_tools" / "ffmpeg.exe")
    for p in candidates:
        if p.exists():
            return str(p)
    return shutil.which("ffmpeg")


REF_B64 = {
    "countdown_text": "iVBORw0KGgoAAAANSUhEUgAAAJoAAAAWCAAAAAAd5tpoAAAA9klEQVRIDc3BQW7TAABFwXn3P/THRm2hxJWIlUVm8rbytvK28rbytvK28rZyZciHhWX51+QvywvlymIZMZosRk6jNTJiDY18mkNuypVl+bCwLIflNIdGlmUxTf5YlptyZU1M08iyLMtpmqaROTVNy2/LstyUK2tyGDktaw45jZjMIYuJ5cuy3JQry1qYFpZlTQ5zalpDFpNvluWmXFlM0zSxLMunoWlOTUyYnJZluSlXhtY0jSzLEOYfWUzT5MOy3JT/thwW1nyT5dGy3JQry2nkyzKEeRTLg+WmPG8e5PXytHmU18uz5kJeL0+aH+TF8pz5SV7sF0czihepBoDuAAAAAElFTkSuQmCC",
    "countdown": "iVBORw0KGgoAAAANSUhEUgAAAKwAAABFCAAAAADyEVJOAAABcUlEQVRo3u2Z4ZKDIAyECXPv/8rfzbTXTrW0RkmCnMmvTg3ZZQ2yaCldQRkUfMemczL98+LnXkPeqSKtnztD9g3nb0TzmkjJyMjIyMjI8I6t/ZaNJGw2bF0Z0bkm+WRxvlWgee39XxSiKcjSyuPh0jYqNDm07pSabN1lTJ8MWdlJPozgdrE1bF1hkdep7KuW6wosSrF7waDloyarhe4dIgZtoO0UTKr4k/U/PdYyUViTFbfkLbIxbwUYoyw758fQNgDXJXnpBea4HE+hrBhlvlorbIjRsBMrE9Jnvm9Za2vLUeuCtKwiCoWNjL7bPjDv00Bihe0DDFcWjq/VXmU5+JyQQLIcOBYMI9vpy2TQAiMQ81JGhpnIliTrRFZSWS+yksom2djGMWg5whCzDf7LSWH0gVHmmGnwSdxKFkLg6jwde8WXHNo+6AWrJ5t0TBvITGQj2NYyEVtbBHyRrOXAE6ee+k65F8cPxkGJ5ZcXDGF+AbiCZkSkUCT8AAAAAElFTkSuQmCC",
    "lobby": "iVBORw0KGgoAAAANSUhEUgAAAJ8AAAAZCAAAAAAKmaP5AAAA9ElEQVRIx+2W0Q6EIAwEGeP///LeSal6Gg0ooA/XB4wa22XaUgnJFCoaZ+4o8TSEd9tf31/fkzZ2iMGNA2J8tboe+pIyqvPDvZPWXch8LlwVOOQmKOqS4lo+DtS2f42U5rU89HdT9DtfKORCaMJPk2dupg2So/r1Z5693rQJ6lzIKj2peqY4BlRAw70s/UvDSrpEQNutxn5LeRfP6lvO0V1U5+ojhkf0nR2oizTDaWI144be8pATRXajuTbjxR5jrxvp47yx1qNyAudCCSuGBpIm+A71eWNk/1yMobPlz7nUPRGnqjeA6gy7cfcBRQloMHJ/7AOEe2Auy2Q6eQAAAABJRU5ErkJggg==",
    "battle_button": "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",
}
_REF_CACHE = {}

def _ref_image(name):
    """Decode a bundled reference image as BGR and validate it."""
    if name not in _REF_CACHE:
        raw = base64.b64decode(REF_B64[name])
        arr = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise RuntimeError(f"Referansebildet '{name}' kunne ikke dekodes.")
        _REF_CACHE[name] = image
    return _REF_CACHE[name]


def _ref_mask(name):
    """Return a grayscale reference image."""
    return cv2.cvtColor(_ref_image(name), cv2.COLOR_BGR2GRAY)


def _green_mask(frame):
    if frame is None or frame.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (35,70,70), (95,255,255))


def _orange_mask(frame):
    if frame is None or frame.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (5,100,100), (30,255,255))


def _anchor_match(frame, name, source_width, source_height, x_range, y_range):
    """Match a UI reference at normalized screen positions and several scales.

    The search is still independent of monitor resolution: the frame is
    normalized first, and the expected UI position is expressed as a
    percentage of the screen rather than fixed pixels.
    """
    if frame is None or frame.size == 0:
        return 0.0, None

    small = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    x0 = int(960 * x_range[0]); x1 = int(960 * x_range[1])
    y0 = int(540 * y_range[0]); y1 = int(540 * y_range[1])
    roi = small[y0:y1, x0:x1]
    if roi.size == 0:
        return 0.0, None

    ref = _ref_image(name)
    if ref is None or ref.size == 0:
        return 0.0, None
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    best = 0.0
    best_center = None

    base_x = 960.0 / float(source_width)
    base_y = 540.0 / float(source_height)
    base = (base_x + base_y) * 0.5

    for relative_scale in (0.70, 0.85, 1.00, 1.15, 1.30):
        tw = max(10, int(ref.shape[1] * base * relative_scale))
        th = max(8, int(ref.shape[0] * base * relative_scale))
        if tw >= roi.shape[1] or th >= roi.shape[0]:
            continue

        templ = cv2.resize(ref_gray, (tw, th), interpolation=cv2.INTER_AREA)
        score_map = cv2.matchTemplate(
            cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY),
            templ,
            cv2.TM_CCOEFF_NORMED,
        )
        _, score, _, loc = cv2.minMaxLoc(score_map)

        if score > best:
            best = float(score)
            cx = (x0 + loc[0] + tw / 2) / 960.0
            cy = (y0 + loc[1] + th / 2) / 540.0
            best_center = (cx, cy)

    return best, best_center


def _countdown_score(frame):
    """Detect the fixed green "Battle starts in" text, independent of the number."""
    if frame is None or frame.size == 0:
        return 0.0

    small = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (40, 110, 145), (90, 255, 255))

    # Tight, screen-independent area containing the fixed phrase.
    x0, x1 = int(960 * 0.35), int(960 * 0.65)
    y0, y1 = int(540 * 0.38), int(540 * 0.49)
    roi = green[y0:y1, x0:x1]
    if roi.size == 0:
        return 0.0

    ref = _ref_mask("countdown_text")
    best = 0.0
    for scale in (0.85, 0.92, 1.00, 1.08, 1.15):
        tw = max(20, int(ref.shape[1] * scale))
        th = max(10, int(ref.shape[0] * scale))
        if tw >= roi.shape[1] or th >= roi.shape[0]:
            continue
        templ = cv2.resize(ref, (tw, th), interpolation=cv2.INTER_NEAREST)
        score_map = cv2.matchTemplate(roi, templ, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(score_map)
        best = max(best, float(score))
    return best

def _lobby_score(frame):
    if frame is None or frame.size == 0:
        return 0.0

    # The orange BATTLE button is also a top/center UI element. Find orange
    # components across the whole frame, then require the component to be in
    # the normalized top-center region. This remains independent of resolution.
    orange = _orange_mask(frame)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(orange)
    # Do not make lobby detection depend on decoding the bundled BATTLE image.
    # Some PyInstaller builds have shown that embedded PNG occasionally fails
    # to decode even though the same image is valid in the source tree.
    # The button itself has a very distinctive orange, wide/short shape, so
    # use resolution-independent geometry as the primary/fallback detector.
    best = 0.0

    for x, y, w, h, area in stats[1:]:
        if area < 80:
            continue
        cx = (x + w / 2) / frame.shape[1]
        cy = (y + h / 2) / frame.shape[0]
        if not (0.20 <= cx <= 0.80 and 0.02 <= cy <= 0.25):
            continue
        ratio = w / max(1, h)
        if not (2.5 <= ratio <= 6.5):
            continue
        if not (25 <= w <= 360 and 6 <= h <= 100):
            continue

        # BATTLE button reference geometry in the normalized 1280x720 layout:
        # roughly 111x25 px. Score candidates by aspect ratio, relative size,
        # and how much of the component is orange. This avoids a fragile
        # dependency on a binary-embedded reference image.
        ratio_score = max(0.0, 1.0 - abs(ratio - 4.44) / 3.0)
        rel_w = w / max(1, frame.shape[1])
        rel_h = h / max(1, frame.shape[0])
        size_score = max(
            0.0,
            1.0
            - 0.5 * abs(rel_w - (111 / 1280)) / (111 / 1280)
            - 0.5 * abs(rel_h - (25 / 720)) / (25 / 720),
        )
        component = orange[y:y+h, x:x+w]
        orange_fill = float(np.count_nonzero(component)) / max(1, w * h)
        fill_score = max(0.0, min(1.0, orange_fill / 0.884))

        score = 0.45 * ratio_score + 0.30 * size_score + 0.25 * fill_score
        best = max(best, score)
    return best


def _refine_start(path, candidate, fps):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first = max(0, int((candidate - 1.2) * fps))
    last = min(n - 1, int((candidate + 1.0) * fps))

    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    found = None
    for idx in range(first, last + 1):
        ok, frame = cap.read()
        if not ok:
            break
        if frame is None or frame.size == 0:
            continue
        if _countdown_score(frame) >= 0.60:
            found = idx / fps
            break

    cap.release()
    return found


def _refine_lobby(path, candidate, fps):
    """Search backward from a lobby anchor to its first visible BATTLE frame."""
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first = max(0, int((candidate - 3.0) * fps))
    last = min(n - 1, int((candidate + 0.6) * fps))

    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    found = None
    for idx in range(first, last + 1):
        ok, frame = cap.read()
        if not ok:
            break
        if frame is None or frame.size == 0:
            continue
        if _lobby_score(frame) >= 0.72:
            found = idx / fps
            break

    cap.release()
    return found


def detect_battles(path, progress):
    """Detect complete battles using two strict visual anchors.

    Start: the first visible "Battle starts in" countdown.
    End: the orange BATTLE button returning in the lobby.

    The detector deliberately rejects isolated matches. A countdown must be
    seen repeatedly in a short time window before it becomes a battle start.
    This prevents green HUD elements inside a battle from creating new clips.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Kunne ikke åpne videoen.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur = n / fps if n else 0

    # One analysis sample about every 0.4 s. The exact start is refined
    # frame-by-frame afterwards.
    step = max(1, round(fps * 0.40))
    countdown_candidates = []
    lobby_candidates = []

    recent_cd = []
    recent_lobby = []
    last_lobby = -999

    i = 0
    while i < n:
        ok, frame = cap.read()
        if not ok:
            break
        if frame is None or frame.size == 0:
            i += 1
            continue

        if i % step == 0:
            t = i / fps
            cd = _countdown_score(frame)
            lb = _lobby_score(frame)

            recent_cd.append((t, cd))
            recent_cd = [(tt, ss) for tt, ss in recent_cd if t - tt <= 1.4]

            # Require two strong countdown observations close together.
            # This is the key protection against false positives during play.
            strong = [tt for tt, ss in recent_cd if ss >= 0.68]
            if len(strong) >= 2:
                candidate = strong[0]
                if not countdown_candidates or candidate - countdown_candidates[-1] > 8:
                    countdown_candidates.append(candidate)
                recent_cd = [(t, cd)]

            # Require two strong lobby observations close together.
            # A single orange UI element can appear briefly during normal
            # gameplay and look like the BATTLE button. The real lobby button
            # remains visible for several frames/seconds, so persistence is a
            # much safer signal than one isolated geometry match.
            recent_lobby.append((t, lb))
            recent_lobby = [(tt, ss) for tt, ss in recent_lobby if t - tt <= 1.6]
            strong_lobbies = [tt for tt, ss in recent_lobby if ss >= 0.68]
            if len(strong_lobbies) >= 2 and t - last_lobby > 5:
                lobby_candidates.append(strong_lobbies[0])
                last_lobby = t
                recent_lobby = [(t, lb)]

            progress(min(70, 70 * t / dur if dur else 0))

        i += 1

    cap.release()

    starts = []
    for cand in countdown_candidates:
        exact = _refine_start(path, cand, fps)
        if exact is not None and (not starts or exact - starts[-1] > 8):
            starts.append(exact)

    lobby_points = []
    for cand in lobby_candidates:
        exact = _refine_lobby(path, cand, fps)
        if exact is not None and (not lobby_points or exact - lobby_points[-1] > 5):
            lobby_points.append(exact)

    if not starts:
        return []

    # Use a strict state machine after the first detected battle.
    #
    # A false "Battle starts in" match can occasionally happen during normal
    # gameplay because the HUD contains green elements. Previously such a
    # false start was accepted as a new battle, and the real battle was then
    # cut at that false start. From Build 23 onward, a later battle start is
    # only accepted AFTER a confirmed lobby has been seen following the
    # previous battle.
    #
    # This gives us the intended sequence:
    #   battle start -> whole battle/results -> lobby -> next battle start
    #
    # If no lobby is found after a started battle, never cut that battle in
    # the middle: keep it to the end of the recording instead.
    kept = []

    first_start = starts[0]
    current_start = first_start

    # Ignore any other countdown candidates until the first confirmed lobby.
    remaining_starts = starts[1:]

    while True:
        after_lobby = [lp for lp in lobby_points if current_start + 20 < lp]
        if not after_lobby:
            # No confirmed lobby means we have no safe end anchor. Keeping to
            # the end is safer than losing the last part of an actual battle.
            if dur - current_start >= 20:
                kept.append((current_start, dur))
            break

        lobby = after_lobby[0]
        kept.append((current_start, lobby))

        # The next battle must start after this lobby. This prevents a false
        # countdown detected during the previous battle from ending it.
        next_candidates = [s for s in remaining_starts if s > lobby + 0.5]
        if not next_candidates:
            break

        current_start = next_candidates[0]
        remaining_starts = [s for s in next_candidates[1:]]

    return kept


class App:
    def __init__(self,root):
        self.root=root; root.title(APP); root.geometry("760x610"); root.minsize(700,560)
        self.video=None; self.user_dir=False; self.running=False
        p=ttk.Frame(root,padding=14); p.pack(fill="both",expand=True)
        ttk.Label(p,text=APP,font=("Segoe UI",16,"bold")).pack(anchor="w",pady=(0,10))
        self.drop=tk.Label(p,text="DRA VIDEO HIT\n\neller bruk «Velg video…»",relief="groove",bd=2,height=5,font=("Segoe UI",11))
        self.drop.pack(fill="x",pady=(0,8)); self.drop.drop_target_register(DND_FILES); self.drop.dnd_bind("<<Drop>>",self.drop_video)
        row=ttk.Frame(p); row.pack(fill="x")
        self.path=tk.StringVar(); ttk.Entry(row,textvariable=self.path,state="readonly").pack(side="left",fill="x",expand=True)
        ttk.Button(row,text="Velg video…",command=self.choose_video).pack(side="left",padx=(8,0))
        ttk.Label(p,text="Tank:").pack(anchor="w",pady=(10,2))
        self.tank=tk.StringVar(value=TANKS[0]); self.tanks=ttk.Combobox(p,textvariable=self.tank,values=TANKS,state="readonly"); self.tanks.pack(fill="x"); self.tanks.bind("<<ComboboxSelected>>",self.tank_changed)
        ttk.Label(p,text="Nytt filnavn:").pack(anchor="w",pady=(10,2))
        self.name=tk.StringVar(); ttk.Entry(p,textvariable=self.name).pack(fill="x")
        ttk.Label(p,text="Lagre i:").pack(anchor="w",pady=(10,2))
        orow=ttk.Frame(p); orow.pack(fill="x"); self.out=tk.StringVar(); ttk.Entry(orow,textvariable=self.out).pack(side="left",fill="x",expand=True); ttk.Button(orow,text="Velg mappe…",command=self.choose_dir).pack(side="left",padx=(8,0))
        self.start=ttk.Button(p,text="▶  START REDIGERING",command=self.start_edit); self.start.pack(fill="x",ipady=8,pady=14)
        self.bar=ttk.Progressbar(p,maximum=100); self.bar.pack(fill="x")
        self.status=tk.StringVar(value="Klar. Ingenting starter før START REDIGERING."); ttk.Label(p,textvariable=self.status,wraplength=700).pack(anchor="w",pady=6)
        self.log=tk.Text(p,height=9,state="disabled"); self.log.pack(fill="both",expand=True)

    def msg(self,s):
        self.root.after(0,lambda:(self.log.configure(state="normal"),self.log.insert("end",s+"\n"),self.log.see("end"),self.log.configure(state="disabled")))
    def set_status(self,s): self.root.after(0,lambda:self.status.set(s))
    def set_progress(self,v): self.root.after(0,lambda:self.bar.configure(value=v))
    def set_video(self,f):
        f=os.path.abspath(f)
        if Path(f).suffix.lower() not in EXT: return messagebox.showerror(APP,"Velg en videofil.")
        self.video=f; self.path.set(f); stem=Path(f).stem; tank=self.tank.get() if self.tank.get()!="Velg tank…" else "WoT"
        self.name.set(f"{tank}_{stem}_klipp.mp4")
        if not self.user_dir: self.out.set(str(Path(f).parent/"WoT Blitz Klipp"/tank))
        self.status.set("Video valgt. Velg tank, navn/mappe og trykk START REDIGERING.")
        self.msg("Video valgt: "+f)
    def drop_video(self,e):
        for f in self.root.tk.splitlist(e.data):
            if Path(f).suffix.lower() in EXT: self.set_video(f); return
        messagebox.showerror(APP,"Slipp inn en gyldig videofil.")
    def choose_video(self):
        f=filedialog.askopenfilename(filetypes=[("Video","*.mp4 *.mkv *.avi *.mov *.webm *.ts *.m4v"),("Alle filer","*.*")])
        if f:self.set_video(f)
    def tank_changed(self,_=None):
        t=self.tank.get()
        if self.video:
            stem=Path(self.video).stem; self.name.set(f"{t}_{stem}_klipp.mp4")
            if not self.user_dir:self.out.set(str(Path(self.video).parent/"WoT Blitz Klipp"/t))
        self.status.set("Tank valgt. Ingenting starter før START REDIGERING.")
    def choose_dir(self):
        d=filedialog.askdirectory()
        if d:self.user_dir=True; self.out.set(os.path.abspath(d))
    def start_edit(self):
        if self.running:return
        if not self.video:return messagebox.showwarning(APP,"Velg eller dra inn en video først.")
        if self.tank.get()=="Velg tank…":return messagebox.showwarning(APP,"Velg tank.")
        if not self.name.get().strip():return messagebox.showwarning(APP,"Skriv inn filnavn.")
        if not self.out.get().strip():return messagebox.showwarning(APP,"Velg lagringsmappe.")
        self.running=True; self.start.configure(state="disabled"); self.bar["value"]=0
        threading.Thread(target=self.process,daemon=True).start()
    def process(self):
        temp_dir=None
        try:
            ff=find_ffmpeg()
            if not ff: raise RuntimeError("FFmpeg mangler i programmet.")
            self.set_status("Analyserer video…"); self.msg("Starter analyse.")
            segs=detect_battles(self.video,self.set_progress)
            if not segs: raise RuntimeError("Fant ingen sikre kamper med «Battle starts in».")

            out=Path(self.out.get()).expanduser(); out.mkdir(parents=True,exist_ok=True)
            base=Path(self.name.get()).name
            if Path(base).suffix.lower()!=".mp4": base+=".mp4"
            dst=out/base

            # Frame-accurate trimming requires re-encoding; stream copy can only
            # cut cleanly on keyframes and could start before "Battle starts in 3".
            def encode_segment(a,b,target):
                cmd=[ff,"-y","-ss",f"{a:.3f}","-i",self.video,"-t",f"{b-a:.3f}",
                     "-map","0:v:0","-map","0:a?","-c:v","libx264","-preset","veryfast",
                     "-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k",
                     "-movflags","+faststart",str(target)]
                r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                if r.returncode:
                    raise RuntimeError("FFmpeg feilet under presis klipping:\n"+r.stderr[-1600:])

            if len(segs)==1:
                a,b=segs[0]
                self.set_status("Klipper kamp 1/1…"); self.msg(f"Kamp 1: {a:.2f}s → {b:.2f}s")
                encode_segment(a,b,dst)
            else:
                temp_dir=Path(tempfile.mkdtemp(prefix="wot_autoclip_"))
                parts=[]
                for i,(a,b) in enumerate(segs,1):
                    self.set_status(f"Klipper kamp {i}/{len(segs)}…")
                    self.msg(f"Kamp {i}: {a:.2f}s → {b:.2f}s")
                    part=temp_dir/f"part_{i:02d}.mp4"
                    encode_segment(a,b,part)
                    parts.append(part)
                    self.set_progress(70+20*i/len(segs))

                concat_list=temp_dir/"concat.txt"
                with concat_list.open("w",encoding="utf-8") as f:
                    for part in parts:
                        safe=str(part).replace("'","'\\''")
                        f.write(f"file '{safe}'\n")

                self.set_status("Setter kampene sammen til én video…")
                self.msg(f"Slår sammen {len(parts)} kampklipp.")
                cmd=[ff,"-y","-f","concat","-safe","0","-i",str(concat_list),
                     "-map","0","-c","copy","-movflags","+faststart",str(dst)]
                r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                if r.returncode: raise RuntimeError("FFmpeg kunne ikke sette sammen klippene:\n"+r.stderr[-1600:])

            self.set_progress(100)
            self.set_status(f"Ferdig. {len(segs)} kamper samlet i én video.")
            self.msg("FERDIG: "+str(dst))
            self.root.after(0,lambda:messagebox.showinfo(APP,
                f"Ferdig!\n{len(segs)} kamper samlet i én video.\n\nLagret i:\n{dst}"))
        except Exception as e:
            self.set_status("Feil – se loggen."); self.msg("FEIL: "+str(e))
            self.root.after(0,lambda:messagebox.showerror(APP,str(e)))
        finally:
            if temp_dir: shutil.rmtree(temp_dir,ignore_errors=True)
            self.running=False; self.root.after(0,lambda:self.start.configure(state="normal"))

if __name__=="__main__":
    root=TkinterDnD.Tk(); App(root); root.mainloop()