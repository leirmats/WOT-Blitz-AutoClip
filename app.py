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
    "countdown": "iVBORw0KGgoAAAANSUhEUgAAAKwAAABFCAAAAADyEVJOAAABcUlEQVRo3u2Z4ZKDIAyECXPv/8rfzbTXTrW0RkmCnMmvTg3ZZQ2yaCldQRkUfMemczL98+LnXkPeqSKtnztD9g3nb0TzmkjJyMjIyMjI8I6t/ZaNJGw2bF0Z0bkm+WRxvlWgee39XxSiKcjSyuPh0jYqNDm07pSabN1lTJ8MWdlJPozgdrE1bF1hkdep7KuW6wosSrF7waDloyarhe4dIgZtoO0UTKr4k/U/PdYyUViTFbfkLbIxbwUYoyw758fQNgDXJXnpBea4HE+hrBhlvlorbIjRsBMrE9Jnvm9Za2vLUeuCtKwiCoWNjL7bPjDv00Bihe0DDFcWjq/VXmU5+JyQQLIcOBYMI9vpy2TQAiMQ81JGhpnIliTrRFZSWS+yksom2djGMWg5whCzDf7LSWH0gVHmmGnwSdxKFkLg6jwde8WXHNo+6AWrJ5t0TBvITGQj2NYyEVtbBHyRrOXAE6ee+k65F8cPxkGJ5ZcXDGF+AbiCZkSkUCT8AAAAAElFTkSuQmCC",
    "lobby": "iVBORw0KGgoAAAANSUhEUgAAAJ8AAAAZCAAAAAAKmaP5AAAA9ElEQVRIx+2W0Q6EIAwEGeP///LeSal6Gg0ooA/XB4wa22XaUgnJFCoaZ+4o8TSEd9tf31/fkzZ2iMGNA2J8tboe+pIyqvPDvZPWXch8LlwVOOQmKOqS4lo+DtS2f42U5rU89HdT9DtfKORCaMJPk2dupg2So/r1Z5693rQJ6lzIKj2peqY4BlRAw70s/UvDSrpEQNutxn5LeRfP6lvO0V1U5+ojhkf0nR2oizTDaWI144be8pATRXajuTbjxR5jrxvp47yx1qNyAudCCSuGBpIm+A71eWNk/1yMobPlz7nUPRGnqjeA6gy7cfcBRQloMHJ/7AOEe2Auy2Q6eQAAAABJRU5ErkJggg==",
    "battle_button": "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",
}
_REF_CACHE = {}

def _ref_image(name):
    """Decode a bundled reference image as BGR."""
    if name not in _REF_CACHE:
        raw = base64.b64decode(REF_B64[name])
        arr = np.frombuffer(raw, dtype=np.uint8)
        _REF_CACHE[name] = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return _REF_CACHE[name]


def _ref_mask(name):
    """Return a grayscale reference image."""
    return cv2.cvtColor(_ref_image(name), cv2.COLOR_BGR2GRAY)


def _green_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (35,70,70), (95,255,255))


def _orange_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (5,100,100), (30,255,255))


def _anchor_match(frame, name, source_width, source_height, x_range, y_range):
    """Match a UI reference at normalized screen positions and several scales.

    The search is still independent of monitor resolution: the frame is
    normalized first, and the expected UI position is expressed as a
    percentage of the screen rather than fixed pixels.
    """
    small = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    x0 = int(960 * x_range[0]); x1 = int(960 * x_range[1])
    y0 = int(540 * y_range[0]); y1 = int(540 * y_range[1])
    roi = small[y0:y1, x0:x1]

    ref = _ref_image(name)
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
    # "Battle starts in 3" is a top/center UI element. Searching the full
    # normalized frame caused ordinary green HUD elements during gameplay to
    # become false positives. We still search a large screen-independent area,
    # but validate the known relative position of this UI element.
    score, _ = _anchor_match(
        frame, "countdown", 1444, 810,
        (0.20, 0.80), (0.05, 0.45)
    )
    return score


def _lobby_score(frame):
    # The orange BATTLE button is also a top/center UI element. Find orange
    # components across the whole frame, then require the component to be in
    # the normalized top-center region. This remains independent of resolution.
    orange = _orange_mask(frame)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(orange)
    ref_gray = _ref_mask("battle_button")
    ref_orange = _orange_mask(_ref_image("battle_button"))
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

        crop_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        templ_gray = cv2.resize(ref_gray, (w, h), interpolation=cv2.INTER_AREA)
        gray_score = float(
            cv2.matchTemplate(crop_gray, templ_gray, cv2.TM_CCOEFF_NORMED)[0, 0]
        )

        crop_orange = orange[y:y+h, x:x+w]
        templ_orange = cv2.resize(ref_orange, (w, h), interpolation=cv2.INTER_NEAREST)
        a = crop_orange > 0
        b = templ_orange > 0
        union = np.count_nonzero(a | b)
        iou = (np.count_nonzero(a & b) / union) if union else 0.0

        score = 0.75 * gray_score + 0.25 * iou
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
        if _countdown_score(frame) >= 0.68:
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
        if _lobby_score(frame) >= 0.72:
            found = idx / fps
            break

    cap.release()
    return found


def detect_battles(path, progress):
    """Detect complete battles using two strict visual anchors.

    Start: the real "Battle starts in 3" countdown.
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
    last_lobby = -999

    i = 0
    while i < n:
        ok, frame = cap.read()
        if not ok:
            break

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

            if lb >= 0.68 and t - last_lobby > 5:
                lobby_candidates.append(t)
                last_lobby = t

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

    kept = []
    for idx, start in enumerate(starts):
        next_start = starts[idx + 1] if idx + 1 < len(starts) else dur

        # The first real BATTLE-button frame after the battle is the end.
        # Because _refine_lobby searches backward, the Victory/Defeat result
        # remains in the output while the following lobby is removed.
        after = [lp for lp in lobby_points if start + 20 < lp < next_start]
        if after:
            end = after[0]
        elif idx + 1 < len(starts):
            end = max(start, next_start - 0.1)
        else:
            end = dur

        if end - start >= 20:
            kept.append((start, end))

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
            if not segs: raise RuntimeError("Fant ingen sikre kamper med «Battle starts in 3».")

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
