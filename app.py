import os, threading, subprocess, shutil, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import cv2

APP="WoT Blitz AutoClip"
TANKS=["Velg tank…","Sheridan","Vickers Light","FV215b","FV215b 183","WZ-121","WZ-113","STB-1","90TP Lewandowskiego","Kranvagn","T95","HWK 12","Object 84","Skoda T 50","50TP Tyszkiewicza","Panther II","JPanther II","53TP Markowskiego","Panther","LTG","AMX 13 M24","Leo","T-34/100","Carro d'Assa","45TP Habicha","Ju-Nu","59-16","BUGI","40TP Habicha","Skoda P-JS","SDP 44 Burza","Bassotto","AC Ocelote","Mitsu 108","DS PZInz","SDP 40 Zadymka","Semovente M41","AC Highlander","T26E4","Lorraine 40t","AMX CDC","Edelweiss","Hafen","WZ Blaze","PZ IV S","AC IV Sentinel","Bretagne Panther","Y5 Firefly","Krupp-38(D)","T-25","Pz V/IV","Y5 T-34","XM66F","VK 168.01 (P)","T-34-3","50TP Prototyp","IS-3 Defender","Centurion Mk 5/1","Type 59","Prowler","Kunze Panzer","VK 45.03","Nameless","Vulcan","Lupus","Rudolph","Agent","U-Panzer","Icebreaker","Triumphant","SU-100Y","Explorer","Ox","Eraser BP44","P.43/06 SNN","Pudel","Pz IV Gargoyle","PZ.Sfl. IVc","KV-220","Nightmare","M3 Lee","Luchs","B2","DW2","A-32","Valentine Mk IX","Ke-Ho","Mark I Male"]
EXT={".mp4",".mkv",".avi",".mov",".webm",".ts",".m4v"}

def find_ffmpeg():
    p=Path(__file__).resolve().parent/"ffmpeg.exe"
    return str(p) if p.exists() else shutil.which("ffmpeg")

def detect_battles(path, progress):
    """Detect battle + result sections and return sections to keep."""
    cap=cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Kunne ikke åpne videoen.")
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur=n/fps if n else 0
    step=max(1,round(fps*0.5))
    samples=[]
    i=0
    while i<n:
        ok,frame=cap.read()
        if not ok: break
        if i%step==0:
            t=i/fps; h,w=frame.shape[:2]
            mini=frame[int(h*.62):int(h*.98),:int(w*.25)]
            gray=cv2.cvtColor(mini,cv2.COLOR_BGR2GRAY)
            battle_edge=cv2.countNonZero(cv2.Canny(gray,80,160))/float(gray.size)
            battle_on=battle_edge>.050
            rr=frame[int(h*.20):int(h*.85),int(w*.15):int(w*.85)]
            hsv=cv2.cvtColor(rr,cv2.COLOR_BGR2HSV)
            blue=cv2.inRange(hsv,(85,80,60),(125,255,255))
            result_on=(cv2.countNonZero(blue)/float(blue.size))>.050
            samples.append((t,battle_on,result_on))
            progress(min(75,75*t/dur if dur else 0))
        i+=1
    cap.release()
    if not samples: return []

    # Require sustained minimap detection so garage/loading flicker cannot
    # split a real battle into multiple clips.
    battle_runs=[]; current=None; last_on=None
    for t,battle_on,_ in samples:
        if battle_on:
            if current is None: current=t
            last_on=t
        elif current is not None and last_on is not None and t-last_on>=3.0:
            if last_on-current>=5.0: battle_runs.append((current,last_on))
            current=None; last_on=None
    if current is not None and last_on is not None and last_on-current>=5.0:
        battle_runs.append((current,last_on))
    if not battle_runs: return []

    kept=[]
    for idx,(battle_start,battle_end) in enumerate(battle_runs):
        start=0.0 if battle_start<=10.0 else max(0.0,battle_start-1.0)
        next_battle=battle_runs[idx+1][0] if idx+1<len(battle_runs) else dur
        search_from=max(0.0,battle_end-2.0)
        search_to=min(next_battle,dur)

        # Search only after a battle has ended. This prevents blue UI inside
        # normal gameplay from being mistaken for the result screen.
        result_runs=[]; rs=None; rl=None
        for t,_,result_on in samples:
            if t<search_from or t>search_to: continue
            if result_on:
                if rs is None: rs=t
                rl=t
            elif rs is not None and rl is not None and t-rl>=2.0:
                if rl-rs>=1.0: result_runs.append((rs,rl))
                rs=None; rl=None
        if rs is not None and rl is not None and rl-rs>=1.0:
            result_runs.append((rs,rl))

        end=min(dur,result_runs[-1][1]+2.0) if result_runs else min(dur,battle_end+10.0)
        if end>start: kept.append((start,end))
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
            if not segs: raise RuntimeError("Fant ingen sikre kampsekvenser.")

            out=Path(self.out.get()).expanduser(); out.mkdir(parents=True,exist_ok=True)
            base=Path(self.name.get()).name
            if Path(base).suffix.lower()!=".mp4": base+=".mp4"
            dst=out/base

            # Extract each battle/result section, then concatenate them into
            # ONE final video. Lobby, queue and loading between battles vanish.
            if len(segs)==1:
                a,b=segs[0]
                self.set_status("Klipper kamp 1/1…"); self.msg(f"Kamp 1: {a:.1f}s → {b:.1f}s")
                cmd=[ff,"-y","-ss",f"{a:.3f}","-i",self.video,"-t",f"{b-a:.3f}",
                     "-map","0","-c","copy","-avoid_negative_ts","make_zero",str(dst)]
                r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                if r.returncode: raise RuntimeError("FFmpeg feilet:\n"+r.stderr[-1200:])
            else:
                temp_dir=Path(tempfile.mkdtemp(prefix="wot_autoclip_"))
                parts=[]
                for i,(a,b) in enumerate(segs,1):
                    self.set_status(f"Henter kamp {i}/{len(segs)}…")
                    self.msg(f"Kamp {i}: {a:.1f}s → {b:.1f}s")
                    part=temp_dir/f"part_{i:02d}.mp4"
                    cmd=[ff,"-y","-ss",f"{a:.3f}","-i",self.video,"-t",f"{b-a:.3f}",
                         "-map","0","-c","copy","-avoid_negative_ts","make_zero",str(part)]
                    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    if r.returncode: raise RuntimeError("FFmpeg feilet:\n"+r.stderr[-1200:])
                    parts.append(part)
                    self.set_progress(75+10*i/len(segs))

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
