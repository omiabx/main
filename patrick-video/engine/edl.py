"""The edit (v6, footage-first). Rule: on-screen text never repeats what the narrator is saying.
Text only appears where it adds something: dates/episode tags, sources, document highlights, diagram labels.
Show footage comes from the user's clips in clips/ (muted under narration; dialogue clips keep their audio)."""
from cards import (Black, Board, Clip, Dictionary, Doc, EndScreen, Folder, Footage, Grid, Montage, Photo, Quote,
                   SplitFootage, Starfish)

C = lambda n: f"clips/{n}.mp4"
# focus points (fx, fy) and good source times picked from contact sheets
PAT_C03 = (C("C03"), 2.5, 0.66, 0.33)
PAT_C04_STARE = (C("C04"), 8.3, 0.64, 0.28)
PAT_C04_GRIN = (C("C04"), 5.0, 0.62, 0.30)
PAT_C06 = (C("C06"), 1.9, 0.42, 0.30)
PAT_C07 = (C("C07"), 1.0, 0.45, 0.40)
PAT_C08_ANGRY = (C("C08"), 9.8, 0.50, 0.40)
PAT_C08_RAMPAGE = (C("C08"), 0.3, 0.32, 0.62)
PAT_C09_HEAD = (C("C09"), 4.4, 0.50, 0.35)
PAT_B07_SMART = (C("B07"), 0.3, 0.55, 0.25)
PAT_C11 = (C("C11"), 8.6, 0.50, 0.35)
PAT_C12_BED = (C("C12"), 11.0, 0.50, 0.40)
PAT_C13 = (C("C13"), 2.7, 0.60, 0.35)
DUMB = [PAT_C04_STARE, PAT_C13, PAT_C11, PAT_C12_BED, PAT_C08_ANGRY, PAT_C03, PAT_C06, PAT_C07, PAT_C09_HEAD,
        (C("C03"), 4.8, 0.55, 0.62), (C("C13"), 15.0, 0.6, 0.35), (C("C11"), 11.9, 0.5, 0.35),
        PAT_C08_RAMPAGE, PAT_C04_GRIN, (C("C12"), 4.1, 0.5, 0.45), (C("B07"), 4.9, 0.55, 0.55)]


def build(tl):
    at = tl.at
    cards, dates, chapters, sfx, monitor = [], [], [], [], []

    def add(card):
        cards.append(card)
        return card

    def foot(t, src, z0=1.05, z1=1.2, punch=None, hold=True, **kw):
        """Footage card from a (path, src_t, fx, fy) tuple. punch=(t, zoom) zooms onto the focus point."""
        path, st, fx, fy = src
        p = (punch[0], punch[1], fx, fy) if punch else None
        return add(Footage(t, path=path, src_in=st, fx=fx, fy=fy, z0=z0, z1=z1, punch=p, hold=hold, **kw))

    def clip(cid):
        s = tl.clip(cid)
        add(Clip(s["g0"], seg=s))
        if not s.get("real"):
            sfx.append((s["g0"] + 0.05, "typing", 0.5))
        return s

    def date(t, d, title, season):
        dates.append((t, d, title, season))
        sfx.append((t + 0.05, "typing", 0.35))

    def hit(t, name="impact", g=0.6):
        sfx.append((t, name, g))

    chapter = lambda t, n, title: chapters.append((t, n, title))
    mon = lambda t, level=1.0, label="BRAIN ACTIVITY", flat=False: monitor.append((t, level, label, flat))

    # ------------------------------------------------------------ COLD OPEN
    add(Footage(0.0, path=C("B01"), src_in=4.3, fx=0.6, fy=0.5, z0=1.0, z1=1.25, ztime=9,
                punch=(at("VO_01", "panics"), 1.9, 0.6, 0.5)))
    date(0.4, "05.01.1999", "HELP WANTED", "S1")
    hit(at("VO_01", "panics"), "whoosh_short", 0.5)
    ip = at("VO_01", "is patrick")
    foot(ip - 0.05, (C("C01"), 0.3, 0.30, 0.24), z0=1.0, z1=1.05, punch=(ip + 0.1, 1.8))
    hit(ip + 0.1, "impact", 0.7)
    clip("C01")

    foot(at("VO_02", "first real scene"), (C("C01"), 5.3, 0.36, 0.28), z0=1.1, z1=1.35, ztime=8)
    ty = at("VO_02", "twelve years later")
    add(Footage(ty, path=C("C12"), src_in=8.5, fx=0.5, fy=0.45, z0=1.05, z1=1.25, hold=False,
                flip_at=at("VO_02", "upside down")))
    date(ty + 0.1, "09.16.2011", "PET SITTER PAT", "S8")
    hit(ty, "glitch", 0.5)
    hit(at("VO_02", "upside down"), "whoosh_rev", 0.5)
    clip("C02")

    # ------------------------------------------------------------ INTRO
    t = at("VO_03", "something happened")
    board1 = dict(c99=(560, 460, ["05.01.1999", "HELP WANTED"], t),
                  c11=(1380, 460, ["09.16.2011", "PET SITTER PAT"], t + 0.4),
                  q=(970, 760, ["?"], at("VO_03", "i wanted a date")))
    add(Board(t, items=board1, strings=[("c99", "q", at("VO_03", "i wanted a date") + 0.2),
                                        ("c11", "q", at("VO_03", "i wanted a date") + 0.5)]))
    sfx += [(t, "pin", 0.5), (t + 0.4, "pin", 0.5), (at("VO_03", "i wanted a date"), "pin", 0.6)]
    wb = at("VO_03", "went back through")
    add(Montage(wb, items=DUMB, step=0.32))
    for i in range(8):
        sfx.append((wb + i * 0.32, "shutter", 0.25))
    add(Doc(at("VO_03", "i dug up"), file="doc_dumbest.png", focus=(0.5, 0.2), zoom=0.1)).source(
        "Wikipedia, \"Patrick Star\"")
    add(Doc(at("VO_03", "2023"), file="doc_nature.png", focus=(0.4, 0.35), zoom=0.12, w=1100)).source(
        "Nature 623, 555-561 (2023)")
    ft = at("VO_03", "this is the file")
    add(Folder(ft, label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "OPENED: 2026"])).stamp(
        at("VO_03", "brain") + 0.15, "CASE OPEN", 1180, 760, -10, 120)
    sfx += [(ft, "whoosh", 0.6), (ft + 0.3, "folder_slam", 0.9), (at("VO_03", "brain") + 0.15, "stamp", 0.9)]
    mon(at("VO_03", "brain") + 0.6)

    # ------------------------------------------------------------ 01 DUMBEST GUY IN TOWN
    t = at("VO_04", "okay")
    chapter(t, 1, "The dumbest guy in town")
    foot(t, PAT_B07_SMART, z0=1.05, z1=1.25).stamp(at("VO_04", "bad news") + 0.3, "DENIED", 1450, 760)
    hit(at("VO_04", "bad news") + 0.3, "stamp", 0.8)
    add(Photo(at("VO_04", "steven hillenburg"), file="hillenburg.jpg", caption="Stephen Hillenburg, 2011",
              credit="Photo: Carlos Cazurro Burgos, CC BY-SA 3.0", w=640, h=680))
    hit(at("VO_04", "steven hillenburg"), "shutter", 0.5)
    add(Doc(at("VO_04", "described patrick"), file="doc_dumbest.png", focus=(0.55, 0.12), zoom=0.28,
            zoom_time=3.5)).source("Hillenburg, SpongeBob Movie DVD featurette (via Wikipedia)")

    add(Photo(at("VO_05", "bill"), file="fagerbakke.jpg", caption="Bill Fagerbakke, Comic-Con 2009",
              credit="Photo: Michelle Nakashima, CC BY 2.0", w=760, h=640, rot=3))
    hit(at("VO_05", "bill"), "shutter", 0.5)
    foot(at("VO_05", "i do the big"), PAT_C06, z0=1.15, z1=1.35)
    add(Doc(at("VO_05", "aqua dauber") - 0.2, file="doc_aquadauber.png", focus=(0.3, 0.1), zoom=0.3,
            zoom_time=3)).source("Wikipedia, \"Patrick Star\"")
    bd = at("VO_05", "built dumb")
    foot(bd - 0.3, PAT_C04_STARE, z0=1.1, z1=1.2, punch=(at("VO_05", "paperwork"), 1.7))
    hit(at("VO_05", "paperwork"), "thud", 0.7)

    t = at("VO_06", "which means")
    add(Black(t, text="WHEN DID PATRICK BECOME STUPID??", size=74, type_time=0.9)).strike(
        at("VO_06", "problem"), 640, 560, 1010, 545)
    sfx += [(t, "typing", 0.5), (at("VO_06", "problem"), "record_scratch", 0.6)]
    s1 = at("VO_06", "season one")
    add(SplitFootage(s1, panels=[(C("C03"), 2.5, "JELLYFISHING  //  1999", s1, 0.6, 0.4),
                                 (C("C12"), 11.0, "PET SITTER PAT  //  2011", at("VO_06", "season seven"), 0.5, 0.42)]))
    hit(at("VO_06", "season seven"), "whoosh_short", 0.4)

    # ------------------------------------------------------------ 02 FIRMLY GRASP IT
    t = at("VO_07", "july")
    chapter(t, 2, "Firmly grasp it")
    add(Footage(t, path=C("C03"), src_in=0.3, fx=0.55, fy=0.45, z0=1.0, z1=1.1, hold=False, speed=0.5))
    date(t + 0.1, "07.31.1999", "JELLYFISHING", "S1")
    foot(at("VO_07", "expert in the room"), PAT_C03, z0=1.35, z1=1.5)
    hit(at("VO_07", "expert in the room"), "whoosh_short", 0.4)
    foot(at("VO_07", "one problem"), (C("C03"), 9.2, 0.33, 0.62), z0=1.2, z1=1.45).circle(
        at("VO_07", "bandages"), 960, 560, 460, 340)
    clip("C03")
    mon(tl.clip("C03")["g1"], 0.8)

    foot(at("VO_08", "thats stupid"), (C("C03"), 4.8, 0.52, 0.6), z0=1.1, z1=1.25)
    foot(at("VO_08", "how jellyfishing works"), (C("C03"), 11.4, 0.66, 0.35), z0=1.15, z1=1.3)
    foot(at("VO_08", "how hands work"), (C("C03"), 4.8, 0.40, 0.66), z0=1.2, z1=1.25,
         punch=(at("VO_08", "how hands work") + 0.3, 1.8))
    hit(at("VO_08", "how hands work") + 0.3, "thud", 0.6)
    foot(at("VO_08", "early patrick"), (C("C09"), 9.0, 0.6, 0.45), z0=1.05, z1=1.2)
    foot(at("VO_08", "doing nothing"), PAT_C12_BED, z0=1.1, z1=1.3)

    # ------------------------------------------------------------ 03 AN ENIGMA
    t = at("VO_09", "september")
    chapter(t, 3, "An enigma")
    foot(t, (C("C04"), 0.3, 0.55, 0.45), z0=1.0, z1=1.12)
    date(t + 0.1, "09.07.2001", "THE SECRET BOX", "S2")
    foot(at("VO_09", "most famous line"), (C("C04"), 3.0, 0.62, 0.30), z0=1.2, z1=1.3,
         punch=(at("VO_09", "most famous line") + 0.2, 1.6))
    clip("C04")

    foot(at("VO_10", "great joke"), (C("C04"), 4.3, 0.6, 0.45), z0=1.05, z1=1.15)
    foot(at("VO_10", "the ending is better"), (C("C04"), 0.3, 0.60, 0.62), z0=1.3, z1=1.9, ztime=11)
    ps = at("VO_10", "a piece of string")
    foot(ps, (C("C04"), 0.3, 0.60, 0.62), z0=2.0, z1=2.2)
    hit(ps, "record_scratch", 0.5)
    foot(at("VO_10", "the idiot right"), PAT_C04_STARE, z0=1.2, z1=1.3, punch=(at("VO_10", "the idiot right") + 0.2, 1.7))
    foot(at("VO_10", "then patrick alone"), PAT_C04_GRIN, z0=1.15, z1=1.3)
    clip("C05")

    foot(at("VO_11", "a hidden compartment"), PAT_C04_GRIN, z0=1.25, z1=1.45)
    hp = at("VO_11", "he played him")
    foot(hp, PAT_C04_GRIN, z0=1.45, z1=1.5, punch=(hp + 0.1, 2.0))
    hit(hp + 0.1, "impact", 0.6)
    foot(at("VO_11", "kept a secret"), (C("C04"), 1.6, 0.30, 0.45), z0=1.3, z1=1.5)
    tb = at("VO_11", "paul tibbitt")
    board2 = dict(sb=(620, 430, ["09.07.2001", "THE SECRET BOX", "written by: Walt Dohrn,", "Paul Tibbitt,",
                                 "Merriwether Williams"], at("VO_11", "one of the three")),
                  pt=(1300, 640, ["PAUL TIBBITT", "storyboard director, 1999-2004"], tb))
    add(Board(at("VO_11", "one of the three"), items=board2, strings=[("sb", "pt", tb + 0.3)])).circle(
        at("VO_11", "hold on"), 1300, 650, 640, 220)
    sfx += [(at("VO_11", "one of the three"), "pin", 0.5), (tb, "pin", 0.7)]

    # ------------------------------------------------------------ 04 PUSH IT SOMEWHERE ELSE
    t = at("VO_12", "one month later")
    chapter(t, 4, "Push it somewhere else")
    add(Footage(t, path=C("B04"), src_in=0.5, fx=0.5, fy=0.45, z0=1.0, z1=1.15, hold=False))
    date(at("VO_12", "alaskan"), "10.12.2001", "SANDY, SPONGEBOB, AND THE WORM", "S2")
    foot(at("VO_12", "with a plan") - 0.3, PAT_C06, z0=1.2, z1=1.3, punch=(at("VO_12", "with a plan"), 1.7))
    clip("C06")

    add(Footage(at("VO_13", "they do it"), path=C("B04"), src_in=6.0, fx=0.5, fy=0.5, z0=1.05, z1=1.2, hold=False))
    foot(at("VO_13", "grew up with"), (C("C03"), 7.0, 0.68, 0.35), z0=1.2, z1=1.35)
    foot(at("VO_13", "one bad day"), (C("C06"), 6.9, 0.5, 0.5), z0=1.05, z1=1.2)
    foot(at("VO_13", "sometimes his idea"), (C("C06"), 3.6, 0.45, 0.40), z0=1.15, z1=1.3).stamp(
        at("VO_13", "they go with"), "APPROVED", 1450, 780, -8, 110)
    hit(at("VO_13", "they go with"), "stamp", 0.9)

    # ------------------------------------------------------------ 05 SACK OF DIAPERS
    t = at("VO_14", "this is where")
    chapter(t, 5, "Dumber than a sack of diapers")
    add(Board(t, items=dict(th=(960, 520, ["THEORY:", "Patrick used to be smart"], t))))
    hit(at("VO_14", "falling apart"), "glitch", 0.6)
    hit(at("VO_14", "falling apart"), "thud", 0.6)
    s2 = at("VO_14", "im with stupid")
    add(Footage(s2, path=C("B05"), src_in=0.5, fx=0.5, fy=0.45, z0=1.0, z1=1.12, hold=False))
    date(s2 + 0.1, "10.19.2001", "I'M WITH STUPID", "S2")
    add(Footage(at("VO_14", "a letter"), path=C("B05"), src_in=12.5, fx=0.5, fy=0.45, z0=1.1, z1=1.25, hold=False))
    clip("C07")

    foot(at("VO_15", "so in"), PAT_C07, z0=1.1, z1=1.3)
    add(Footage(at("VO_15", "the plan"), path=C("B05"), src_in=2.0, fx=0.5, fy=0.45, z0=1.05, z1=1.2, hold=False))
    jm = at("VO_15", "janet")
    add(Board(at("VO_15", "and at the end"), items=dict(
        p=(960, 300, ["THE STARFISH AT DINNER"], at("VO_15", "and at the end")),
        j=(640, 640, ["JANET"], jm), m=(1280, 640, ["MARTY"], jm + 0.3)),
        strings=[("p", "j", jm + 0.1), ("p", "m", jm + 0.4)]))
    sfx += [(jm, "pin", 0.6), (jm + 0.3, "pin", 0.6)]
    foot(at("VO_15", "so no"), PAT_C04_STARE, z0=1.15, z1=1.35, punch=(at("VO_15", "i checked"), 1.9))
    hit(at("VO_15", "i checked"), "thud", 0.7)
    mon(at("VO_15", "golden age"), 0.8, "RESULT: NO CHANGE")

    # ------------------------------------------------------------ 06 A ONE-TIME THING
    t = at("VO_16", "but there is")
    chapter(t, 6, "A one-time thing")
    mon(t, 1.0)
    add(Doc(t, file="doc_lender.png", focus=(0.5, 0.2), zoom=0.12)).source("Wikipedia, \"Patrick Star\"")
    vd = at("VO_16", "february")
    add(Footage(vd, path=C("B06"), src_in=3.0, fx=0.5, fy=0.45, z0=1.0, z1=1.15, hold=False, speed=0.6))
    date(vd + 0.1, "02.14.2000", "VALENTINE'S DAY", "S1")
    clip("C08")

    sn = at("VO_17", "he snaps")
    foot(sn, PAT_C08_ANGRY, z0=1.05, z1=1.1, punch=(sn + 0.05, 1.6))
    hit(sn + 0.05, "impact", 0.8)
    add(Footage(at("VO_17", "tears through"), path=C("B06"), src_in=3.0, fx=0.5, fy=0.5, z0=1.05, z1=1.2,
                hold=False))
    add(Doc(at("VO_17", "jay lender"), file="doc_lender.png", focus=(0.6, 0.35), zoom=0.35, zoom_time=3.5)).source(
        "Jay Lender, The Oral History of SpongeBob, Hogan's Alley #17 (2010)")

    q0, q1 = tl.beat_g("VO_18")
    add(Doc(q0 - 0.2, file="doc_lender.png", focus=(0.55, 0.75), zoom=0.45, zoom_time=9, enter="cut")).source(
        "Hogan's Alley #17 (2010), via Wikipedia")
    lender = ("When that show came back, it felt so right that his dark side started popping up everywhere. "
              "You can plan ahead all you want, but the characters eventually tell you who they are.")
    sw = at("VO_19", "swap")
    add(Quote(sw - 0.1, text=lender, who="JAY LENDER", enter="cut", size=58)).strike(
        at("VO_19", "dark side"), 1090, 437, 1420, 437).note(at("VO_19", "for stupid"), "stupid", 1260, 370, 80)
    hit(at("VO_19", "for stupid"), "pop", 0.5)
    jw = at("VO_19", "a joke works once")
    ag = at("VO_19", "do it again")
    add(Grid(jw, items=DUMB, steps=[(0, 1), (0, 2), (0, 3), (0, 4), (0, 6)],
             times=[jw, ag, ag + 0.7, at("VO_19", "after a few years"), at("VO_19", "its all he is")]))
    for tt in (ag, ag + 0.7, at("VO_19", "after a few years"), at("VO_19", "its all he is")):
        hit(tt, "shutter", 0.4)
    fl = at("VO_19", "flanderization")
    add(Dictionary(fl - 0.3, word="Flan·der·i·za·tion", pron="(noun)  //  TV Tropes",
                   definition="When one trait of a character gets exaggerated, episode after episode, until it "
                              "becomes the whole character.", t_def=fl + 0.3))
    add(Grid(at("VO_19", "patrick went through"), items=DUMB[::-1], steps=[(0, 6)],
             times=[at("VO_19", "patrick went through")]))

    # ------------------------------------------------------------ 07 BRAIN CORAL
    t = at("VO_20", "and if you want")
    chapter(t, 7, "Brain coral")
    foot(at("VO_20", "heres my pick"), PAT_C09_HEAD, z0=1.0, z1=1.1)
    add(Doc(at("VO_20", "in 2004"), file="doc_tibbitt.png", focus=(0.4, 0.6), zoom=0.35, zoom_time=4)).source(
        "Wikipedia, \"Paul Tibbitt\"")
    pt = at("VO_20", "paul tibbitt")
    board3 = dict(sb=(620, 430, ["09.07.2001", "THE SECRET BOX"], pt - 5),
                  pt=(1300, 600, ["PAUL TIBBITT", "showrunner, seasons 4-9", "(2005-2015)"], pt - 5))
    add(Board(pt, items=board3, strings=[("sb", "pt", at("VO_20", "the secret box guy"))],
              focus=(1300, 600, 1.6), pullback=True))
    hit(pt, "pin", 0.7)
    sp = at("VO_20", "october")
    add(Footage(sp, path=C("C09"), src_in=0.0, fx=0.45, fy=0.5, z0=1.0, z1=1.12, hold=False, speed=0.5)).stamp(
        at("VO_20", "patrick smartpants") + 0.2, "PRIME SUSPECT", 1450, 830, -8, 100)
    date(sp + 0.1, "10.21.2005", "PATRICK SMARTPANTS", "S4")
    hit(at("VO_20", "patrick smartpants") + 0.2, "stamp", 1.0)
    clip("C09")

    foot(at("VO_21", "danger"), (C("C09"), 1.7, 0.40, 0.45), z0=1.15, z1=1.3)
    kt = at("VO_21", "knocks the top")
    foot(kt, PAT_C09_HEAD, z0=1.2, z1=1.3, punch=(kt + 0.3, 1.7))
    hit(kt + 0.3, "impact", 0.6)
    add(Footage(at("VO_21", "into art"), path=C("B07"), src_in=0.3, fx=0.55, fy=0.25, z0=1.1, z1=1.25, hold=False,
                speed=0.6))
    mon(at("VO_21", "into art"), 2.4, "BRAIN ACTIVITY ?!")
    foot(at("VO_21", "he tells squidward"), (C("B07"), 2.1, 0.55, 0.25), z0=1.2, z1=1.35)
    foot(at("VO_21", "hes unbearable"), (C("B07"), 4.9, 0.55, 0.55), z0=1.1, z1=1.3)
    foot(at("VO_21", "actual physics"), (C("B07"), 3.1, 0.55, 0.25), z0=1.25, z1=1.3,
         punch=(at("VO_21", "actual physics") + 0.2, 1.6))
    clip("C10")

    bc = at("VO_22", "brain coral")
    foot(bc - 0.15, (C("C09"), 4.4, 0.5, 0.22), z0=1.3, z1=1.4, punch=(bc + 0.1, 2.1))
    hit(bc + 0.1, "impact", 0.7)
    mon(bc, 0.8)
    foot(at("VO_22", "screwed a rock"), (C("C09"), 4.4, 0.5, 0.25), z0=1.6, z1=1.75)
    add(Footage(at("VO_22", "picks friendship"), path=C("C09"), src_in=5.8, fx=0.5, fy=0.45, z0=1.05, z1=1.2,
                hold=False, speed=0.7))
    s01 = at("VO_22", "in 2001")
    add(SplitFootage(s01, panels=[(C("C04"), 5.0, "THE SECRET BOX  //  2001", s01, 0.62, 0.32),
                                  (C("C09"), 4.4, "PATRICK SMARTPANTS  //  2005", at("VO_22", "in 2005"), 0.5, 0.35)]))
    hit(at("VO_22", "in 2005"), "whoosh_short", 0.4)
    foot(at("VO_22", "now its an accident"), (C("B07"), 1.2, 0.55, 0.25), z0=1.2, z1=1.4)

    qn = at("VO_23", "quick note")
    foot(qn, PAT_C09_HEAD, z0=1.05, z1=1.15).stamp(qn, "PRIME SUSPECT", 1450, 830, -8, 100).strike(
        at("VO_23", "thats my read"), 1230, 820, 1680, 800, (20, 20, 20))
    hit(at("VO_23", "thats my read"), "paper_slide", 0.5)
    add(Board(at("VO_23", "and tibbitt"), items=board3, strings=[("sb", "pt", 0)]))
    foot(at("VO_23", "but look at"), PAT_C12_BED, z0=1.05, z1=1.25)

    # ------------------------------------------------------------ 08 FIFTY KRABBY PATTIES
    t = at("VO_24", "same season")
    chapter(t, 8, "Fifty Krabby Patties")
    foot(t, PAT_C11, z0=1.05, z1=1.2)
    date(t + 0.1, "11.25.2006", "THAT'S NO LADY", "S4")
    clip("C11")

    pn = at("VO_25", "august")
    foot(pn, (C("C11"), 2.0, 0.62, 0.5), z0=1.1, z1=1.3, punch=(at("VO_25", "lockdown"), 1.7))
    date(pn + 0.1, "08.02.2007", "PAT NO PAY", "S5")
    hit(at("VO_25", "lockdown"), "impact", 0.7)
    s11 = at("VO_25", "september")
    add(Footage(s11, path=C("C12"), src_in=8.5, fx=0.5, fy=0.45, z0=1.05, z1=1.2, hold=False,
                flip_at=at("VO_25", "upside")))
    date(s11 + 0.1, "09.16.2011", "PET SITTER PAT", "S8")
    foot(at("VO_25", "by the end"), (C("C12"), 4.1, 0.5, 0.45), z0=1.1, z1=1.35)
    clip("C12")

    foot(at("VO_26", "old patrick"), PAT_C03, z0=1.1, z1=1.2)
    foot(at("VO_26", "phones"), PAT_C13, z0=1.2, z1=1.3)
    foot(at("VO_26", "the idea"), (C("C13"), 15.0, 0.6, 0.35), z0=1.2, z1=1.35)
    ev = at("VO_26", "everything")
    add(Grid(ev - 0.1, items=DUMB, steps=[(0, 2), (0, 3), (0, 4), (0, 6)],
             times=[ev - 0.1, ev + 0.35, ev + 0.7, ev + 1.05]))
    for k in range(4):
        hit(ev - 0.1 + 0.35 * k, "shutter", 0.35)
    sp2 = at("VO_26", "somebody else pays")
    add(Montage(sp2, items=[(C("C03"), 9.2, 0.33, 0.45), (C("C11"), 2.0, 0.62, 0.5), (C("C12"), 4.1, 0.5, 0.45)],
                step=0.75))
    foot(at("VO_26", "needs something to break"), PAT_C08_RAMPAGE, z0=1.15, z1=1.35)
    sp3 = at("VO_26", "send patrick in")
    foot(at("VO_26", "they just"), PAT_C04_STARE, z0=1.2, z1=1.3, punch=(sp3, 2.0))
    mon(sp3 + 0.2, 0.0, "FLATLINE", True)
    hit(sp3 + 0.2, "flatline", 0.45)

    # ------------------------------------------------------------ 09 NO, THIS IS PATRICK
    t = at("VO_27", "now about phones")
    chapter(t, 9, "No, this is Patrick")
    mon(t, 0.5)
    add(Footage(t, path=C("B12"), src_in=0.3, fx=0.6, fy=0.4, z0=1.0, z1=1.12, hold=False, speed=0.5))
    date(at("VO_27", "big pink loser"), "02.03.2001", "BIG PINK LOSER", "S2")
    hit(at("VO_27", "answer the phone") + 0.4, "phone_ring", 0.5)
    clip("C13")

    foot(at("VO_28", "a customer"), (C("B12"), 25.0, 0.55, 0.4), z0=1.05, z1=1.2)
    ff = at("VO_28", "fast forward")
    add(Doc(ff, file="doc_pss.png", focus=(0.5, 0.3), zoom=0.3, zoom_time=4)).source(
        "Wikipedia, \"The Patrick Star Show\"")
    hit(ff, "whoosh", 0.5)
    date(at("VO_28", "nickelodeon premieres"), "07.09.2021", "THE PATRICK STAR SHOW", "S1")
    foot(at("VO_28", "twenty years after"), (C("B12"), 12.5, 0.6, 0.35), z0=1.1, z1=1.3)
    kk = at("VO_28", "is this the")
    add(Footage(kk - 0.3, path=C("B12"), src_in=2.5, fx=0.6, fy=0.35, z0=1.15, z1=1.25, hold=False))
    hit(kk - 0.6, "phone_ring", 0.45)
    tp = at("VO_28", "this is patrick")
    foot(tp, PAT_C13, z0=1.25, z1=1.3, punch=(tp + 0.1, 1.9))
    hit(tp + 0.9, "hangup", 0.8)

    # ------------------------------------------------------------ 10 ALL HEAD
    t = at("VO_29", "okay one last thing")
    chapter(t, 10, "All head")
    add(Folder(t, label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "APPENDIX: BIOLOGY"]))
    sfx += [(t, "whoosh", 0.5), (t + 0.3, "folder_slam", 0.8)]
    add(Photo(at("VO_29", "steven hillenburg"), file="hillenburg.jpg", caption="Stephen Hillenburg",
              credit="Photo: Carlos Cazurro Burgos, CC BY-SA 3.0", w=640, h=680))
    add(Doc(at("VO_29", "when he explained"), file="doc_dumbest.png", focus=(0.65, 0.33), zoom=0.3,
            zoom_time=4)).source("Hillenburg, SpongeBob Movie DVD featurette (via Wikipedia)")
    foot(at("VO_29", "if you remember"), PAT_C08_ANGRY, z0=1.2, z1=1.45)

    rs = at("VO_30", "real starfish")
    add(Photo(rs, file="starfish2.jpg", caption="Pisaster ochraceus",
              credit="Photo: Charles J. Sharp, CC BY-SA 4.0", w=860, h=600, rot=-2))
    hit(rs, "shutter", 0.5)
    nb = at("VO_30", "none")
    hit(nb, "thud", 0.7)
    mon(nb, 0.0, "BRAIN: NOT FOUND", True)
    rn = at("VO_30", "just a ring")
    add(Starfish(rn - 0.2, t_nerves=rn + 0.2, t_head=1e9,
                 labels=[(rn + 0.3, "NERVE RING", (255, 245, 120), 380),
                         (at("VO_30", "down each arm"), "RADIAL NERVES x5", (255, 245, 120), 440)]))
    nt = at("VO_30", "in november")
    add(Doc(nt, file="doc_nature.png", focus=(0.4, 0.3), zoom=0.2, w=1150)).source(
        "Formery et al., Nature 623 (2023); Stanford University")
    date(nt, "11.01.2023", "NATURE, VOL. 623", "STANFORD")
    sl = at("VO_30", "they sliced")
    add(Starfish(sl, t_nerves=sl, labels=[(sl + 0.2, "RNA TOMOGRAPHY", (230, 230, 230), 380),
                                          (at("VO_30", "nothing that builds a body"), "TRUNK GENES: ~0",
                                           (255, 120, 120), 440)]))
    hd = at("VO_30", "the genes that build a head")
    add(Starfish(hd, t_head=hd + 0.1, labels=[(hd + 0.4, "HEAD-PATTERNING GENES", (80, 200, 255), 380)]))
    hit(hd + 0.1, "riser", 0.3)
    add(Photo(at("VO_30", "the headlines"), file="starfish1.jpg", caption="Asterias rubens",
              credit="Photo: Hans Hillewaert, CC BY-SA 4.0", w=860, h=600, rot=2))
    add(Photo(at("VO_30", "walking around"), file="starfish3.jpg", caption="",
              credit="Photo: Steven Pavlov, CC BY-SA 4.0", w=860, h=600, rot=-3, enter="cut"))

    gh = at("VO_31", "giant head")
    foot(gh - 0.2, (C("C09"), 4.4, 0.5, 0.3), z0=1.0, z1=1.6, ztime=4.5)
    foot(at("VO_31", "he was the most"), (C("C09"), 4.4, 0.5, 0.35), z0=1.6, z1=1.7,
         punch=(at("VO_31", "scientifically accurate"), 2.0))
    hit(at("VO_31", "scientifically accurate"), "thud", 0.6)
    add(Photo(at("VO_31", "science just took"), file="starfish2.jpg", caption="",
              credit="Photo: Charles J. Sharp, CC BY-SA 4.0", w=860, h=600, rot=-2, enter="cut"))

    # ------------------------------------------------------------ VERDICT
    t = at("VO_32", "so when did")
    chapter(t, 11, "So when did it happen?")
    mon(t, 0.5, "BRAIN ACTIVITY")
    items = dict(
        a=(330, 300, ["05.01.1999", "HELP WANTED"], t), b=(780, 220, ["07.31.1999", "JELLYFISHING"], t),
        c=(1230, 300, ["02.14.2000", "VALENTINE'S DAY"], t), d=(1650, 230, ["09.07.2001", "THE SECRET BOX"], t),
        e=(360, 700, ["10.12.2001", "THE WORM"], t), f=(820, 640, ["10.21.2005", "PATRICK SMARTPANTS"], t),
        g=(1260, 720, ["08.02.2007", "PAT NO PAY"], t), h=(1660, 660, ["09.16.2011", "PET SITTER PAT"], t),
        p=(1000, 930, ["PAUL TIBBITT"], t))
    strings = [("a", "b", t), ("b", "c", t), ("c", "d", t), ("d", "p", t), ("p", "f", t), ("f", "g", t),
               ("g", "h", t), ("e", "f", t)]
    add(Board(t, items=items, strings=strings, focus=(960, 540, 1.5), pullback=True))
    op = at("VO_32", "on paper")
    add(Board(op, items=items, strings=strings, enter="cut").circle(op + 0.2, 330, 300, 470, 260))
    hit(op + 0.2, "pop", 0.4)
    foot(at("VO_32", "but when did"), PAT_C11, z0=1.1, z1=1.3)
    o21 = at("VO_32", "im going with")
    add(Board(o21, items=items, strings=strings, enter="cut").circle(at("VO_32", "october") + 0.2, 820, 640, 520, 280))
    hit(at("VO_32", "october") + 0.2, "impact", 0.5)
    foot(at("VO_32", "by accident"), PAT_C09_HEAD, z0=1.1, z1=1.35)
    add(Montage(at("VO_32", "you might pick"), items=DUMB, step=0.55, loop=True))
    fi = at("VO_32", "and if theres")
    add(Folder(fi, label=["FILE NO. 0048", "SUBJECT: ???", "SUBMITTED BY: YOU"]))
    sfx += [(fi, "whoosh", 0.5), (fi + 0.3, "folder_slam", 0.7)]

    end = next(s for s in tl.segments if s["kind"] == "end")
    add(EndScreen(end["g0"]))
    hit(end["g0"], "stamp", 0.8)
    mon(end["g0"] - 3, 0, None)
    cards.sort(key=lambda c: c.t0)
    return cards, dates, chapters, sfx, monitor
