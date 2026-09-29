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


REF_B64 = {"countdown_text":"iVBORw0KGgoAAAANSUhEUgAAAKUAAABNCAAAAADiV/vpAAACWElEQVRoBdXBCXLbSAAEMPT/H907pCgfiWQOUzWuJZAa4v8tFf97cQdxB3EHcQdxB3EHcQdxB3EHcQdxB3EHcQdxpvFKY7nGQ9xB3EHcQdxB3EHcQdxB3EHcQdxB3EHcQVxXm/g9cVk9xBeNp4r3Gi80fhKX1SE+VGoXFe8U8Yca4psSH+KyEjWEItRTVFBDHIpQQ1DEUIdQxEMJihD/oFFD1C7qEBXUEIci6iE1RH0ItYldQ+1CXFa7GOpPUVKbONR7qSHULjaNekpcVg8x1CYVtYmSIk1jU1+lqdR3UZvYNfUpLitShNqlQg1RX8RQu6gh1F+iNrGrr+KyOgS1SYUaor6ITQ1BEepT1JBKiYdKfYjLStQQ1JAKiqhPsashKGKop6hUlHhqNHWIq4qoTWqXCjVE7eJTfYr6KioVahObBnWIq2pIHaI2aWpIkRIfKvUh9VXUEJoiNkXqEFfVS6ld6pDGrn4SNUTtYlOkDnFV/S0qmtpFHYL6SShRD7FpKjWkxGX1kDrEU4NGHWKoN6KCCg0lvqpo4rraxK6Ip8ahNrGrh9Q3qdg0fhK/oR6inmJe/IL6W1wQ69ULcUEsVm/EvFir3oppsVS9F9NipToTM2KhOhUzYp2aEBNinZoQE2KdOhczYp06FzNimZoRE2KZmhOnYpmaE6dimZoTp2KdmhHnYp2aEBNinToXM2KdOhczYqE6FxNioToVM2KhOhNTYp06FVNipfpJzIql6r2YFmvVa3FFrFWvxRWxWL0UV8Rq9UJcEuvVn+KaWK++S+Oa+AX1EP/oP8d100bFkK90AAAAAElFTkSuQmCC","digit_3":"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","digit_4":"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","digit_5":"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","digit_6":"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"}
REF_SOURCE_WIDTH = {"countdown_text": 1444, "digit_3": 1280, "digit_4": 1280, "digit_5": 1280, "digit_6": 1280}
_REF_CACHE = {}

def _ref(name):
    if name not in _REF_CACHE:
        raw = base64.b64decode(REF_B64[name])
        arr = np.frombuffer(raw, dtype=np.uint8)
        _REF_CACHE[name] = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    return _REF_CACHE[name]

def _scaled_template(name, frame_width=640):
    t = _ref(name)
    src_w = REF_SOURCE_WIDTH[name]
    tw = max(5, int(t.shape[1] * frame_width / src_w))
    th = max(5, int(t.shape[0] * frame_width / src_w))
    return cv2.resize(t, (tw, th), interpolation=cv2.INTER_AREA)

def _countdown_scores(frame):
    small = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
    b, g, r = cv2.split(small)

    green = ((g > 100) & (g > r * 1.20) & (g > b * 1.10)).astype(np.uint8) * 255
    roi_green = green[int(.18 * 360):int(.72 * 360), int(.25 * 640):int(.75 * 640)]
    text_t = _scaled_template("countdown_text")
    generic = float(cv2.matchTemplate(roi_green, text_t, cv2.TM_CCOEFF_NORMED).max())

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    roi_digit = gray[int(.22 * 360):int(.78 * 360), int(.30 * 640):int(.70 * 640)]

    scores = {}
    for name in ("digit_3", "digit_4", "digit_5", "digit_6"):
        t = _scaled_template(name)
        scores[name] = float(cv2.matchTemplate(roi_digit, t, cv2.TM_CCOEFF_NORMED).max())

    three = scores["digit_3"]
    other = max(scores["digit_4"], scores["digit_5"], scores["digit_6"])
    return generic, three, three - other

def _lobby_score(frame):
    small = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    roi = hsv[int(.04 * 360):int(.23 * 360), int(.38 * 640):int(.68 * 640)]
    orange = cv2.inRange(roi, (5, 120, 100), (25, 255, 255))
    ratio = float(orange.mean() / 255.0)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(orange, 8)
    largest = max((int(s[4]) for s in stats[1:]), default=0)
    return ratio, largest

def _refine_start(path, candidate, countdown_started, fps):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first = max(0, int((candidate - 1.5) * fps))
    last = min(n - 1, int((candidate + 0.5) * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    found = None
    for idx in range(first, last + 1):
        ok, frame = cap.read()
        if not ok:
            break
        t = idx / fps
        generic, three, margin = _countdown_scores(frame)
        if (t - countdown_started >= 1.8 and generic >= 0.55 and
                three >= 0.86 and margin >= 0.05):
            found = t
            break
    cap.release()
    return found

def _refine_lobby(path, candidate, fps):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first = max(0, int((candidate - 1.5) * fps))
    last = min(n - 1, int((candidate + 0.5) * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    found = None
    for idx in range(first, last + 1):
        ok, frame = cap.read()
        if not ok:
            break
        ratio, area = _lobby_score(frame)
        if ratio >= 0.02 and area >= 200:
            found = idx / fps
            break
    cap.release()
    return found

def detect_battles(path, progress):
    """Find exact Battle starts in 3 anchors and lobby anchors; keep only the
    continuous battle/result section and remove everything between battles."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Kunne ikke åpne videoen.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur = n / fps if n else 0
    step = max(1, round(fps * 0.5))

    start_candidates = []
    lobby_candidates = []
    countdown_started = None
    i = 0

    while i < n:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            t = i / fps
            generic, three, margin = _countdown_scores(frame)
            lobby_ratio, lobby_area = _lobby_score(frame)

            if generic >= 0.60:
                if countdown_started is None:
                    countdown_started = t
            elif countdown_started is not None and t - countdown_started > 1.5:
                countdown_started = None

            if (countdown_started is not None and
                    t - countdown_started >= 1.8 and
                    three >= 0.86 and margin >= 0.05):
                start_candidates.append((t, countdown_started))
                countdown_started = None

            if lobby_ratio >= 0.02 and lobby_area >= 200:
                lobby_candidates.append(t)

            progress(min(70, 70 * t / dur if dur else 0))
        i += 1
    cap.release()

    starts = []
    for candidate, countdown_started in start_candidates:
        exact = _refine_start(path, candidate, countdown_started, fps)
        if exact is None:
            continue
        if not starts or exact - starts[-1] > 5.0:
            starts.append(exact)

    if not starts:
        return []

    lobbies = []
    for candidate in lobby_candidates:
        if not lobbies or candidate - lobbies[-1] > 1.0:
            exact = _refine_lobby(path, candidate, fps)
            if exact is not None:
                lobbies.append(exact)

    kept = []
    for idx, start in enumerate(starts):
        next_start = starts[idx + 1] if idx + 1 < len(starts) else dur
        possible = [t for t in lobbies if start + 1.0 < t < next_start]
        if possible:
            end = possible[0]
        else:
            # Conservative fallback if the recording ends without showing the lobby.
            end = next_start if idx + 1 < len(starts) else dur
        if end > start:
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
