import os, threading, subprocess, shutil
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
    cap=cv2.VideoCapture(path)
    if not cap.isOpened(): raise RuntimeError("Kunne ikke åpne videoen.")
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); dur=n/fps if n else 0
    step=max(1,round(fps)); active=False; start=None; last=None; raw=[]
    i=0
    while i<n:
        ok,frame=cap.read()
        if not ok: break
        if i%step==0:
            t=i/fps; h,w=frame.shape[:2]
            roi=frame[int(h*.125):int(h*.215),int(w*.35):int(w*.65)]
            hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
            g=cv2.inRange(hsv,(35,70,50),(95,255,255))
            r=cv2.inRange(hsv,(0,70,50),(12,255,255))+cv2.inRange(hsv,(165,70,50),(180,255,255))
            color=(cv2.countNonZero(g)+cv2.countNonZero(r))/float(roi.shape[0]*roi.shape[1])
            edge=cv2.countNonZero(cv2.Canny(cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY),80,160))/float(roi.shape[0]*roi.shape[1])
            on=color>.015 and edge>.045
            if on:
                if not active: start=max(0,t-1); active=True
                last=t
            elif active and last is not None and t-last>=4:
                end=min(dur,last+10)
                if end-start>=20: raw.append((start,end))
                active=False; start=last=None
            progress(min(80,80*t/dur if dur else 0))
        i+=1
    if active and last is not None:
        end=min(dur,last+10)
        if end-start>=20: raw.append((start,end))
    cap.release()
    merged=[]
    for a,b in raw:
        if merged and a-merged[-1][1]<=4: merged[-1]=(merged[-1][0],max(merged[-1][1],b))
        else: merged.append((a,b))
    return merged

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
        try:
            ff=find_ffmpeg()
            if not ff: raise RuntimeError("FFmpeg mangler i programmet.")
            self.set_status("Analyserer video…"); self.msg("Starter analyse.")
            segs=detect_battles(self.video,self.set_progress)
            if not segs: raise RuntimeError("Fant ingen sikre kampsekvenser.")
            out=Path(self.out.get()).expanduser(); out.mkdir(parents=True,exist_ok=True)
            base=Path(self.name.get()).name
            if Path(base).suffix.lower()!=".mp4":base+=".mp4"
            outs=[out/base] if len(segs)==1 else [out/f"{Path(base).stem}_kamp_{i:02d}.mp4" for i in range(1,len(segs)+1)]
            for i,((a,b),dst) in enumerate(zip(segs,outs),1):
                self.set_status(f"Klipper kamp {i}/{len(segs)}…"); self.msg(f"Kamp {i}: {a:.1f}s → {b:.1f}s")
                cmd=[ff,"-y","-ss",f"{a:.3f}","-i",self.video,"-t",f"{b-a:.3f}","-map","0","-c","copy","-avoid_negative_ts","make_zero",str(dst)]
                r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                if r.returncode: raise RuntimeError("FFmpeg feilet:\n"+r.stderr[-1200:])
                self.set_progress(80+20*i/len(segs))
            self.set_status(f"Ferdig. {len(outs)} klipp lagret."); self.msg("FERDIG: "+str(out))
            self.root.after(0,lambda:messagebox.showinfo(APP,f"Ferdig!\n{len(outs)} klipp lagret i:\n{out}"))
        except Exception as e:
            self.set_status("Feil – se loggen."); self.msg("FEIL: "+str(e)); self.root.after(0,lambda:messagebox.showerror(APP,str(e)))
        finally:
            self.running=False; self.root.after(0,lambda:self.start.configure(state="normal"))

if __name__=="__main__":
    root=TkinterDnD.Tk(); App(root); root.mainloop()
