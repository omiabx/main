"""Shared data: source paths, crowd head coordinates, VO word timings."""
import json, os
SCR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(SCR, "clips_raw")
S5 = os.path.join(RAW, "s5_v2d2.mp4")      # WEHTS (captioned -> use ymax=365)
S2 = os.path.join(RAW, "s2_d1.mp4")        # Patty Hype (clean)
D05 = os.path.join(RAW, "f100_d05.mp4")    # Band Geeks (captioned)
N6 = os.path.join(RAW, "n100_d01.mp4")     # Nautical Novice (captioned)
CAP = 365  # ymax that hides burned-in captions

VO = {k: os.path.join(SCR, "vo", f"chunk{k}.mp3") for k in ["1", "2", "2b", "3", "4", "5", "6", "7", "8", "9"]}
WORDS = json.load(open(os.path.join(SCR, "vo", "words.json")))

def word_t(chunk, idx_or_text, nth=0):
    ws = WORDS[chunk]["words"]
    if isinstance(idx_or_text, int): return ws[idx_or_text]["s"]
    hits = [w for w in ws if w["w"].lower().strip(".,?!\"") == idx_or_text.lower()]
    return hits[nth]["s"]

# Patty Hype crowd frame (s2_d1 @ 6768.0), head positions counted by hand in 718x480 frame coords.
CROWD_T = 6768.0
_heads718 = [
 (58,8),(35,35),(100,22),(80,60),(140,45),(160,8),(195,50),(215,12),(135,105),(210,95),(40,145),(90,145),(205,140),(170,230),(140,170),
 (250,15),(295,5),(335,15),(380,20),(472,20),(295,65),(245,85),(325,80),(385,75),(425,45),(455,90),(345,105),(265,125),(300,125),(410,125),(445,140),
 (535,5),(575,15),(650,20),(530,60),(610,60),(665,90),(485,100),(530,90),(580,95),(515,145),(645,145),(575,175),(590,210),(700,195),(660,230),
 (10,290),(65,300),(95,270),(115,245),(150,250),(180,265),(145,300),(90,380),(165,370),(215,310),(225,360),(145,440),
 (285,345),(345,345),(390,335),(430,355),(450,295),(300,420),(385,410),(470,400),
 (495,275),(560,255),(650,255),(615,245),(595,300),(520,330),(570,380),(700,330),(640,420),(500,390),(520,225)]
HEADS = [(x * 640 / 718, y) for x, y in _heads718]   # display-corrected 640x480 coords
# repeated designs (display coords) for the "same guy" beat
REPEATS = {"smallblue": [(142 * 640 / 718, 45), (262 * 640 / 718, 25)],
           "lavender": [(95 * 640 / 718, 160), (652 * 640 / 718, 157)]}
