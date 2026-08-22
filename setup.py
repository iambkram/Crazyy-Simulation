"""
Crazyy Simulation - Windows Setup Wizard
Self-contained: bundles game assets inside EXE, installs like a real application.
"""
import ctypes
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("iambkram.crazyysimulation.setup.1")
except Exception:
    pass

import pygame, os, sys, json, shutil, subprocess, threading, math, random

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.abspath(os.path.dirname(__file__))

DEFAULT_INSTALL_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Programs", "Crazyy-Simulation"
)

try:
    DESKTOP_DIR = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath(\"Desktop\")"],
        creationflags=0x08000000).decode().strip()
    SM_RAW = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath(\"StartMenu\")"],
        creationflags=0x08000000).decode().strip()
    START_MENU_DIR = os.path.join(SM_RAW, "Programs", "Crazyy Simulation")
except Exception:
    DESKTOP_DIR    = os.path.join(os.environ.get("USERPROFILE", "~"), "Desktop")
    START_MENU_DIR = os.path.join(os.environ.get("APPDATA",""), "Microsoft","Windows","Start Menu","Programs","Crazyy Simulation")

BLACK=(0,0,0); WHITE=(255,255,255); NEON_CYAN=(0,255,255); NEON_PINK=(255,0,200)
NEON_BLUE=(30,120,255); NEON_GREEN=(0,255,80); DARK_BG=(8,5,20); CARD_BG=(15,10,35)
DIM_GREY=(60,60,80); RED=(220,50,50)

PAGE_WELCOME=0; PAGE_OPTIONS=1; PAGE_INSTALL=2; PAGE_DONE=3

pygame.init()
pygame.mixer.init()
W,H=800,600
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Crazyy Simulation - Setup")
try:
    pygame.display.set_icon(pygame.image.load(os.path.join(BUNDLE_DIR,"icon.ico")))
except:
    pass

try:
    FONT_TITLE=pygame.font.Font(os.path.join(BUNDLE_DIR,"game_assets","PressStart2P.ttf"),20)
    FONT_MED  =pygame.font.Font(os.path.join(BUNDLE_DIR,"game_assets","PressStart2P.ttf"),11)
    FONT_SMALL=pygame.font.Font(os.path.join(BUNDLE_DIR,"game_assets","PressStart2P.ttf"),8)
except:
    FONT_TITLE=pygame.font.SysFont("Consolas",22,bold=True)
    FONT_MED  =pygame.font.SysFont("Consolas",13)
    FONT_SMALL=pygame.font.SysFont("Consolas",11)

page=PAGE_WELCOME; install_path=DEFAULT_INSTALL_DIR
opt_desktop=True; opt_start_menu=True
install_logs=[]; install_progress=0.0; install_done=False; install_error=None
stars=[[random.randint(0,W),random.randint(0,H),random.uniform(0.3,1.2),random.randint(60,200)] for _ in range(120)]
pulse_t=0.0

def dtxt(surf,text,font,color,cx,cy):
    s=font.render(text,True,color); surf.blit(s,s.get_rect(center=(cx,cy)))

def neon_rect(surf,color,rect,w=2,r=10):
    pygame.draw.rect(surf,color,rect,w,border_radius=r)

def btn(surf,text,cx,cy,bw=220,bh=44,hov=False):
    col=NEON_CYAN if hov else NEON_BLUE
    bg=(0,40,80) if hov else (5,15,40)
    r=pygame.Rect(cx-bw//2,cy-bh//2,bw,bh)
    pygame.draw.rect(surf,bg,r,border_radius=10)
    neon_rect(surf,col,r); dtxt(surf,text,FONT_MED,col,cx,cy)
    return r

def draw_stars():
    for s in stars:
        s[1]+=s[2]
        if s[1]>H: s[1]=0; s[0]=random.randint(0,W)
        br=max(30,int(s[3])); pygame.draw.rect(screen,(br,br,br),(int(s[0]),int(s[1]),2,2))

def shortcut(target,lnk,icon,wd):
    try:
        import pythoncom
        pythoncom.CoInitialize()
        import win32com.client
        os.makedirs(os.path.dirname(lnk),exist_ok=True)
        shell = win32com.client.Dispatch('WScript.Shell')
        s = shell.CreateShortCut(lnk)
        s.Targetpath = target
        s.WorkingDirectory = wd
        s.IconLocation = icon
        s.save()
    except Exception as ex:
        install_logs.append(f"  [WARN] Shortcut: {ex}")

def do_install():
    global install_progress,install_done,install_error
    try:
        install_logs.append(">> Creating install directory...")
        os.makedirs(install_path,exist_ok=True); install_progress=0.10

        install_logs.append(">> Copying game executable...")
        src_exe=os.path.join(BUNDLE_DIR,"Crazyy-Simulation.exe")
        dst_exe=os.path.join(install_path,"Crazyy-Simulation.exe")
        if os.path.exists(src_exe): shutil.copy2(src_exe,dst_exe)
        install_progress=0.30

        install_logs.append(">> Copying icon...")
        src_ico=os.path.join(BUNDLE_DIR,"icon.ico")
        dst_ico=os.path.join(install_path,"icon.ico")
        if os.path.exists(src_ico): shutil.copy2(src_ico,dst_ico)
        install_progress=0.40

        install_logs.append(">> Deploying game assets...")
        src_a=os.path.join(BUNDLE_DIR,"game_assets"); dst_a=os.path.join(install_path,"game_assets")
        if os.path.exists(src_a):
            for root,_,files in os.walk(src_a):
                rel=os.path.relpath(root,src_a)
                d=os.path.join(dst_a,rel) if rel!="." else dst_a
                os.makedirs(d,exist_ok=True)
                for f in files:
                    try: shutil.copy2(os.path.join(root,f),os.path.join(d,f))
                    except: pass
        install_progress=0.65

        install_logs.append(">> Writing default save profile...")
        sdst=os.path.join(install_path,"save.json")
        if not os.path.exists(sdst):
            with open(sdst,"w") as sf:
                json.dump({"coins":0,"hp":200,"hp_step":0,"speed":7,"speed_step":0,
                    "bullets":1,"bullet_step":0,"max_galaxy_level":1,"max_nebula_level":1,
                    "max_blackhole_level":1,"env2_unlocked":False,"env3_unlocked":False,
                    "control_type":"PC","music_vol":0.5,"sfx_vol":0.7,
                    "show_fps":False,"visual_quality":"high","screen_shake":True,
                    "display_mode":"windowed"},sf,indent=4)
        install_progress=0.75

        install_logs.append(">> Creating shortcuts...")
        ico_f=dst_ico if os.path.exists(dst_ico) else ""
        if opt_desktop:
            shortcut(dst_exe,os.path.join(DESKTOP_DIR,"Crazyy Simulation.lnk"),ico_f,install_path)
        if opt_start_menu:
            shortcut(dst_exe,os.path.join(START_MENU_DIR,"Crazyy Simulation.lnk"),ico_f,install_path)
        install_progress=0.88

        install_logs.append(">> Registering application...")
        try:
            import winreg
            kp=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CrazzyySimulation"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,kp) as k:
                winreg.SetValueEx(k,"DisplayName",0,winreg.REG_SZ,"Crazyy Simulation")
                winreg.SetValueEx(k,"DisplayVersion",0,winreg.REG_SZ,"1.0.0")
                winreg.SetValueEx(k,"Publisher",0,winreg.REG_SZ,"iambkram")
                winreg.SetValueEx(k,"InstallLocation",0,winreg.REG_SZ,install_path)
                winreg.SetValueEx(k,"DisplayIcon",0,winreg.REG_SZ,ico_f)
        except: pass
        install_progress=1.0
        install_logs.append(">> Done! Crazyy Simulation installed successfully!")
        install_done=True
    except Exception as ex:
        install_error=str(ex); install_logs.append(f">> ERROR: {ex}"); install_done=True

def run():
    global page,opt_desktop,opt_start_menu,pulse_t
    clock=pygame.time.Clock(); running=True; th=None
    while running:
        pulse_t+=0.04; screen.fill(DARK_BG); draw_stars()
        pygame.draw.rect(screen,NEON_BLUE,(2,2,W-4,H-4),2,border_radius=8)
        pygame.draw.rect(screen,NEON_PINK,(6,6,W-12,H-12),1,border_radius=6)
        mx,my=pygame.mouse.get_pos(); clicked=False
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1: clicked=True
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE and page in(PAGE_WELCOME,PAGE_DONE): running=False
        a=int(200+55*math.sin(pulse_t))
        dtxt(screen,"CRAZYY SIMULATION",FONT_TITLE,(*NEON_CYAN[:3],),W//2,45)
        dtxt(screen,"SETUP WIZARD  v1.0.0",FONT_SMALL,NEON_PINK,W//2,72)
        pygame.draw.line(screen,NEON_BLUE,(40,90),(W-40,90),1)

        if page==PAGE_WELCOME:
            dtxt(screen,"WELCOME!",FONT_MED,NEON_CYAN,W//2,145)
            for i,ln in enumerate(["This wizard will install Crazyy Simulation","on your Windows PC.","",
                "Click NEXT to continue or QUIT to exit."]):
                dtxt(screen,ln,FONT_SMALL,WHITE,W//2,210+i*28)
            nr=btn(screen,"NEXT  >",W//2+110,H-80,hov=pygame.Rect(W//2,H-102,220,44).collidepoint(mx,my))
            qr=btn(screen,"QUIT",W//2-110,H-80,bw=160,hov=pygame.Rect(W//2-200,H-102,160,44).collidepoint(mx,my))
            if clicked:
                if nr.collidepoint(mx,my): page=PAGE_OPTIONS
                elif qr.collidepoint(mx,my): running=False

        elif page==PAGE_OPTIONS:
            dtxt(screen,"INSTALL OPTIONS",FONT_MED,NEON_CYAN,W//2,135)
            def cb(label,val,bx,by):
                r=pygame.Rect(bx-10,by-10,20,20); pygame.draw.rect(screen,NEON_BLUE,r,2,border_radius=4)
                if val:
                    pygame.draw.line(screen,NEON_GREEN,(bx-5,by),(bx,by+6),2)
                    pygame.draw.line(screen,NEON_GREEN,(bx,by+6),(bx+8,by-5),2)
                dtxt(screen,label,FONT_SMALL,WHITE,bx+130,by); return r
            c1=cb("Add Desktop shortcut",opt_desktop,140,220)
            c2=cb("Add Start Menu entry",opt_start_menu,140,265)
            if clicked:
                if c1.collidepoint(mx,my): opt_desktop=not opt_desktop
                if c2.collidepoint(mx,my): opt_start_menu=not opt_start_menu
            dtxt(screen,"Install to:",FONT_SMALL,DIM_GREY,W//2,330)
            dtxt(screen,install_path[:60],FONT_SMALL,NEON_CYAN,W//2,358)
            br=btn(screen,"< BACK",W//2-110,H-80,bw=160,hov=pygame.Rect(W//2-190,H-102,160,44).collidepoint(mx,my))
            ir=btn(screen,"INSTALL",W//2+110,H-80,hov=pygame.Rect(W//2,H-102,220,44).collidepoint(mx,my))
            if clicked:
                if br.collidepoint(mx,my): page=PAGE_WELCOME
                elif ir.collidepoint(mx,my):
                    page=PAGE_INSTALL; th=threading.Thread(target=do_install,daemon=True); th.start()

        elif page==PAGE_INSTALL:
            dtxt(screen,"INSTALLING...",FONT_MED,NEON_CYAN,W//2,125)
            bw=W-120; bx,by=60,162
            pygame.draw.rect(screen,CARD_BG,(bx,by,bw,24),border_radius=12)
            fw=int(bw*install_progress)
            if fw>0: pygame.draw.rect(screen,NEON_GREEN,(bx,by,fw,24),border_radius=12)
            neon_rect(screen,NEON_BLUE,(bx,by,bw,24),r=12)
            dtxt(screen,f"{int(install_progress*100)}%",FONT_SMALL,WHITE,W//2,by+12)
            ly=205
            for ln in install_logs[-13:]:
                dtxt(screen,ln[:78],FONT_SMALL,NEON_CYAN if ">>" in ln else DIM_GREY,W//2,ly); ly+=24
            if install_done: page=PAGE_DONE

        elif page==PAGE_DONE:
            if install_error:
                dtxt(screen,"INSTALLATION FAILED",FONT_MED,RED,W//2,155)
                dtxt(screen,install_error[:65],FONT_SMALL,WHITE,W//2,205)
            else:
                dtxt(screen,"INSTALLATION COMPLETE!",FONT_MED,NEON_GREEN,W//2,155)
                dtxt(screen,"Crazyy Simulation is ready to play.",FONT_SMALL,WHITE,W//2,200)
                dtxt(screen,"Desktop shortcut created!" if opt_desktop else "",FONT_SMALL,NEON_CYAN,W//2,230)
            dtxt(screen,"Thank you for playing!",FONT_SMALL,DIM_GREY,W//2,300)
            lr=btn(screen,"LAUNCH GAME",W//2,H-145,bw=240,hov=pygame.Rect(W//2-120,H-167,240,44).collidepoint(mx,my))
            cr=btn(screen,"CLOSE",W//2,H-85,bw=180,hov=pygame.Rect(W//2-90,H-107,180,44).collidepoint(mx,my))
            if clicked:
                gexe=os.path.join(install_path,"Crazyy-Simulation.exe")
                if lr.collidepoint(mx,my) and os.path.exists(gexe):
                    subprocess.Popen([gexe],cwd=install_path); running=False
                elif cr.collidepoint(mx,my): running=False

        pygame.display.flip(); clock.tick(60)
    pygame.quit()

if __name__=="__main__":
    run()
