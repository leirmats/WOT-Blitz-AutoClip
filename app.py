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
}
_REF_CACHE = {}

def _ref_mask(name):
    if name not in _REF_CACHE:
        raw = base64.b64decode(REF_B64[name])
        arr = np.frombuffer(raw, dtype=np.uint8)
        _REF_CACHE[name] = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    return _REF_CACHE[name]

def _match_ref(frame, name, roi_box, source_width=1444):
    x0,y0,x1,y1 = roi_box
    small = cv2.resize(frame, (640,360), interpolation=cv2.INTER_AREA)
    roi = small[int(y0*360):int(y1*360), int(x0*640):int(x1*640)]
    t = _ref_mask(name)
    scale = 640.0 / source_width
    tw = max(5, int(t.shape[1]*scale))
    th = max(5, int(t.shape[0]*scale))
    t = cv2.resize(t, (tw,th), interpolation=cv2.INTER_NEAREST)
    if roi.shape[0] < th or roi.shape[1] < tw:
        return 0.0
    return float(cv2.matchTemplate(roi, t, cv2.TM_CCOEFF_NORMED).max())

def _green_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (35,70,70), (95,255,255))

def _orange_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (5,100,100), (30,255,255))

def _countdown_score(frame):
    # The reference is the actual "Battle starts in 3" text supplied from the user's screenshot.
    mask = _green_mask(cv2.resize(frame,(640,360),interpolation=cv2.INTER_AREA))
    t = _ref_mask("countdown")
    scale = 640.0 / 1444.0
    t = cv2.resize(t,(max(5,int(t.shape[1]*scale)),max(5,int(t.shape[0]*scale))),interpolation=cv2.INTER_NEAREST)
    roi = mask[int(.28*360):int(.68*360),int(.35*640):int(.65*640)]
    if roi.shape[0] < t.shape[0] or roi.shape[1] < t.shape[1]:
        return 0.0
    return float(cv2.matchTemplate(roi,t,cv2.TM_CCOEFF_NORMED).max())

def _lobby_score(frame):
    small = cv2.resize(frame,(640,360),interpolation=cv2.INTER_AREA)
    mask = _orange_mask(small)
    t = _ref_mask("lobby")
    scale = 640.0 / 1427.0
    t = cv2.resize(t,(max(5,int(t.shape[1]*scale)),max(5,int(t.shape[0]*scale))),interpolation=cv2.INTER_NEAREST)
    roi = mask[0:int(.25*360),int(.35*640):int(.75*640)]
    if roi.shape[0] < t.shape[0] or roi.shape[1] < t.shape[1]:
        return 0.0
    return float(cv2.matchTemplate(roi,t,cv2.TM_CCOEFF_NORMED).max())

def _refine_start(path, candidate, fps):
    cap=cv2.VideoCapture(path)
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first=max(0,int((candidate-1.0)*fps))
    last=min(n-1,int((candidate+0.5)*fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES,first)
    found=None
    for idx in range(first,last+1):
        ok,frame=cap.read()
        if not ok: break
        if _countdown_score(frame)>=0.60:
            found=idx/fps
            break
    cap.release()
    return found

def _refine_lobby(path, candidate, fps):
    cap=cv2.VideoCapture(path)
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first=max(0,int((candidate-1.0)*fps))
    last=min(n-1,int((candidate+0.5)*fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES,first)
    found=None
    for idx in range(first,last+1):
        ok,frame=cap.read()
        if not ok: break
        if _lobby_score(frame)>=0.70:
            found=idx/fps
            break
    cap.release()
    return found

def detect_battles(path, progress):
    """Use the exact countdown and lobby UI references as battle boundaries."""
    cap=cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Kunne ikke åpne videoen.")
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur=n/fps if n else 0
    step=max(1,round(fps*0.35))
    starts=[]
    lobbies=[]
    last_start=-999
    last_lobby=-999
    i=0
    while i<n:
        ok,frame=cap.read()
        if not ok: break
        if i%step==0:
            t=i/fps
            cs=_countdown_score(frame)
            if cs>=0.60 and t-last_start>8:
                starts.append(t); last_start=t
            ls=_lobby_score(frame)
            if ls>=0.70 and t-last_lobby>3:
                lobbies.append(t); last_lobby=t
            progress(min(70,70*t/dur if dur else 0))
        i+=1
    cap.release()

    exact_starts=[]
    for cand in starts:
        exact=_refine_start(path,cand,fps)
        if exact is not None and (not exact_starts or exact-exact_starts[-1]>8):
            exact_starts.append(exact)

    exact_lobbies=[]
    for cand in lobbies:
        exact=_refine_lobby(path,cand,fps)
        if exact is not None and (not exact_lobbies or exact-exact_lobbies[-1]>3):
            exact_lobbies.append(exact)

    if not exact_starts:
        return []

    kept=[]
    for idx,start in enumerate(exact_starts):
        next_start=exact_starts[idx+1] if idx+1<len(exact_starts) else dur
        after=[t for t in exact_lobbies if start+15<t<next_start]
        if after:
            end=after[0]
        elif idx+1<len(exact_starts):
            # If no lobby was recorded, don't eat into the next countdown.
            end=max(start,next_start-0.1)
        else:
            end=dur
        if end>start:
            kept.append((start,end))
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
