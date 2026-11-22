"""The edit: every card, stamp, date card and sound effect, anchored to phrases in the voiceover."""
from cards import (Board, Black, Checklist, Clip, Copies, Counter, Dictionary, Doc, EndScreen, Folder,
                   Letter, Media, Photo, Quote, Receipt, Split, Starfish, TextSlam)
from gfx import RED, WHITE

YEL = (255, 214, 64)
W2, H2 = 960, 540


def build(tl):
    at = tl.at
    cards, dates, chapters, sfx, monitor = [], [], [], [], []

    def add(card):
        cards.append(card)
        return card

    def clip(cid, punch=None):
        s = tl.clip(cid)
        add(Clip(s["g0"], seg=s, punch=punch))
        if not s.get("real"):
            sfx.append((s["g0"] + 0.05, "typing", 0.5))
            if s["dur"] > 3.0:
                sfx.append((s["g0"] + 1.6, "typing", 0.4))
        return s

    def date(t, d, title, season):
        dates.append((t, d, title, season))
        sfx.append((t + 0.05, "typing", 0.45))
        sfx.append((t + 1.45, "typewriter_bell", 0.25))

    def chapter(t, n, title):
        chapters.append((t, n, title))

    def mon(t, level=1.0, label="BRAIN ACTIVITY", flat=False):
        monitor.append((t, level, label, flat))

    # ------------------------------------------------------------ COLD OPEN
    add(Black(0.0, text="MAY 1, 1999", type_time=0.9))
    sfx.append((0.05, "typing", 0.6))
    add(Media(at("VO_01", "the very first episode"), label="B01  HELP WANTED", path="clips/B01.mp4",
              tag="EXHIBIT 00  //  HELP WANTED  //  S1"))
    date(at("VO_01", "the very first episode"), "05.01.1999", "HELP WANTED", "S1")
    add(Media(at("VO_01", "panics"), label="B01  HELP WANTED", path="clips/B01.mp4", src_in=3.0,
              tag="EXHIBIT 00  //  HELP WANTED  //  S1", enter="cut")).caption(at("VO_01", "panics"), "HE PANICS")
    add(TextSlam(at("VO_01", "is patrick"), lines=[("...IS PATRICK.", WHITE)], size=210))
    sfx.append((at("VO_01", "is patrick"), "impact", 0.7))
    clip("C01")

    add(TextSlam(at("VO_02", "pep talk"), lines=[("A PEP TALK.", WHITE)]))
    sfx.append((at("VO_02", "pep talk"), "thud", 0.7))
    add(TextSlam(at("VO_02", "and it works"), lines=[("A PEP TALK.", WHITE), ("THAT WORKED.", YEL)],
                 times=[at("VO_02", "and it works") - 5, at("VO_02", "and it works")]))
    ty = at("VO_02", "twelve years later")
    add(Counter(ty, range=(1999, 2011), t_start=ty + 0.1, t_end=ty + 1.3, label="TWELVE YEARS LATER"))
    sfx.append((ty + 0.1, "riser", 0.35))
    sfx.append((ty + 1.3, "thud", 0.6))
    ps = at("VO_02", "pet")
    add(Media(ps, label="B10  PET SITTER PAT", path="clips/B10.mp4", tag="EXHIBIT 00b  //  PET SITTER PAT  //  S8",
              flip_at=at("VO_02", "upside down")))
    date(ps, "09.16.2011", "PET SITTER PAT", "S8")
    sfx.append((at("VO_02", "upside down"), "whoosh_rev", 0.5))
    clip("C02")
    sfx.append((tl.clip("C02")["g0"] + 2.5, "paper_slide", 0.5))

    # ------------------------------------------------------------ INTRO / FILE OPEN
    t = at("VO_03", "something happened")
    board1 = dict(c99=(560, 460, ["05.01.1999", "HELP WANTED", "the pep talk"], t),
                  c11=(1380, 460, ["09.16.2011", "PET SITTER PAT", "list upside down"], t + 0.4),
                  q=(970, 760, ["WHEN?"], at("VO_03", "i wanted a date")))
    add(Board(t, items=board1, strings=[("c99", "q", at("VO_03", "i wanted a date") + 0.2),
                                        ("c11", "q", at("VO_03", "i wanted a date") + 0.5)]))
    sfx += [(t, "pin", 0.5), (t + 0.4, "pin", 0.5), (at("VO_03", "i wanted a date"), "pin", 0.6)]
    eps = ["JELLYFISHING", "THE SECRET BOX", "I'M WITH STUPID", "VALENTINE'S DAY", "PATRICK SMARTPANTS",
           "PAT NO PAY", "BIG PINK LOSER", "THAT'S NO LADY"]
    t = at("VO_03", "went back through")
    add(Copies(t, lines=["EPISODE LOG", "re-watched: 47", "regretted: 12"], t_copy=t + 0.3, rate=7))
    add(Doc(at("VO_03", "i dug up"), file="doc_dumbest.png", focus=(0.5, 0.2), zoom=0.1)).source(
        "Wikipedia, \"Patrick Star\"")
    add(Doc(at("VO_03", "2023"), file="doc_nature.png", focus=(0.4, 0.35), zoom=0.12, w=1100)).source(
        "Nature 623, 555-561 (2023)").note(at("VO_03", "did not plan on"), "??", 1500, 820, 140)
    ft = at("VO_03", "this is the file")
    add(Folder(ft, label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "RE: THE BRAIN"])).stamp(
        at("VO_03", "brain") + 0.15, "CASE OPEN", 1180, 760, -10, 120)
    sfx += [(ft, "whoosh", 0.6), (ft + 0.3, "folder_slam", 0.9), (at("VO_03", "brain") + 0.15, "stamp", 0.9)]
    mon(at("VO_03", "brain") + 0.6)

    # ------------------------------------------------------------ 01 DUMBEST GUY IN TOWN
    t = at("VO_04", "okay")
    chapter(t, 1, "The dumbest guy in town")
    add(TextSlam(t, lines=[("SECRETLY BRILLIANT?", WHITE)], size=150)).stamp(
        at("VO_04", "bad news") + 0.3, "DENIED", 1450, 760)
    sfx.append((at("VO_04", "bad news") + 0.3, "stamp", 0.8))
    add(Photo(at("VO_04", "steven hillenburg"), file="hillenburg.jpg", caption="Stephen Hillenburg, creator",
              credit="Photo: Carlos Cazurro Burgos, CC BY-SA 3.0", w=640, h=680))
    sfx.append((at("VO_04", "steven hillenburg"), "shutter", 0.5))
    add(Doc(at("VO_04", "described patrick"), file="doc_dumbest.png", focus=(0.55, 0.12), zoom=0.28,
            zoom_time=3.5)).source("Hillenburg, SpongeBob Movie DVD featurette (via Wikipedia)").stamp(
        at("VO_04", "drew him"), "FROM THE CREATOR", 1350, 820, -7, 80)
    sfx.append((at("VO_04", "drew him"), "stamp", 0.8))

    add(Photo(at("VO_05", "bill"), file="fagerbakke.jpg", caption="Bill Fagerbakke, voice of Patrick",
              credit="Photo: Michelle Nakashima, CC BY 2.0", w=760, h=640, rot=3))
    sfx.append((at("VO_05", "bill"), "shutter", 0.5))
    add(Media(at("VO_05", "tape of tom kenny"), label="AUDITION, 1997", tag="AUDITION TAPE  //  1997"))
    q0 = at("VO_05", "i do the big")
    add(Quote(q0 - 0.3, text="I do the big dumb stuff. That's my deal.", who="BILL FAGERBAKKE, ON HIS AUDITION",
              words=tl.words_between(q0, at("VO_05", "my deal", end=True)), size=80))
    ad = at("VO_05", "aqua dauber")
    add(TextSlam(ad - 0.1, lines=[("AQUA", (120, 200, 255)), ("DAUBER", WHITE)], size=200,
                 times=[ad - 0.1, ad + 0.35]))
    sfx += [(ad - 0.1, "thud", 0.6), (ad + 0.35, "thud", 0.7)]
    add(Doc(at("VO_05", "dauber was"), file="doc_aquadauber.png", focus=(0.3, 0.1), zoom=0.3,
            zoom_time=3)).source("Wikipedia, \"Patrick Star\"")
    bd = at("VO_05", "built dumb")
    add(Folder(bd - 0.4, label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "STATUS: BUILT DUMB"], enter="cut")
        ).stamp(at("VO_05", "paperwork"), "ON PAPER", 1180, 760, -10, 120)
    sfx.append((at("VO_05", "paperwork"), "stamp", 0.9))

    t = at("VO_06", "which means")
    add(Black(t, text="WHEN DID PATRICK BECOME STUPID??", size=74, type_time=0.9)).strike(
        at("VO_06", "problem"), 640, 560, 1010, 545)
    sfx += [(t, "typing", 0.5), (at("VO_06", "problem"), "record_scratch", 0.6)]
    s1 = at("VO_06", "season one")
    add(Split(s1, panels=[("SEASON 1", "1999", s1), ("SEASON 7", "2010", at("VO_06", "season seven"))],
              mid=("?", at("VO_06", "two different"))))
    sfx += [(at("VO_06", "season seven"), "whoosh_short", 0.4), (at("VO_06", "two different"), "thud", 0.6)]

    # ------------------------------------------------------------ 02 FIRMLY GRASP IT
    t = at("VO_07", "july")
    chapter(t, 2, "Firmly grasp it")
    add(Media(t, label="EXHIBIT A", path="clips/C03.mp4", tag="EXHIBIT A  //  JELLYFISHING  //  S1"))
    date(t, "07.31.1999", "JELLYFISHING", "S1")
    add(TextSlam(at("VO_07", "expert in the room"), lines=[("THE EXPERT", YEL)], size=200))
    sfx.append((at("VO_07", "expert in the room"), "thud", 0.6))
    add(Media(at("VO_07", "one problem"), label="EXHIBIT A", path="clips/C03.mp4", src_in=2.0,
              tag="EXHIBIT A  //  JELLYFISHING  //  S1", enter="cut")).circle(at("VO_07", "bandages"), 1180, 560, 380, 300)
    clip("C03")
    mon(tl.clip("C03")["g1"], 0.8)

    t = at("VO_08", "thats stupid")
    rows = [(at("VO_08", "how jellyfishing works"), "HOW JELLYFISHING WORKS", "y"),
            (at("VO_08", "how hands work"), "HOW HANDS WORK", "n"),
            (at("VO_08", "he has hobbies"), "HOBBIES", "y"),
            (at("VO_08", "strong opinions"), "STRONG OPINIONS", "y"),
            (at("VO_08", "doing nothing"), "DOING NOTHING (EXPERT)", "y")]
    add(Media(t, label="B02  UNDER THE ROCK", path="clips/B02.mp4", tag="EXHIBIT A2  //  S1"))
    add(Checklist(rows[0][0] - 0.4, title="WHAT EARLY PATRICK KNOWS", rows=rows))
    for r in rows:
        sfx.append((r[0], "type_key", 0.6))
        sfx.append((r[0] + 0.35, "pop", 0.4))

    # ------------------------------------------------------------ 03 AN ENIGMA
    t = at("VO_09", "september")
    chapter(t, 3, "An enigma")
    add(Media(t, label="B03  THE SECRET BOX", path="clips/B03.mp4", tag="EXHIBIT B  //  THE SECRET BOX  //  S2"))
    date(t, "09.07.2001", "THE SECRET BOX", "S2")
    add(TextSlam(at("VO_09", "most famous line"), lines=[("HIS MOST FAMOUS LINE", WHITE)], size=140))
    clip("C04")

    add(TextSlam(at("VO_10", "great joke"), lines=[("GREAT JOKE.", WHITE)]))
    add(Media(at("VO_10", "the ending is better"), label="B03  THE SECRET BOX", path="clips/B03.mp4", src_in=2,
              tag="EXHIBIT B  //  NIGHT, PATRICK'S ROCK")).caption(at("VO_10", "stocking"), "STOCKING MASK")
    add(TextSlam(at("VO_10", "a piece of string"), lines=[("IT'S A STRING.", WHITE)], size=190))
    sfx.append((at("VO_10", "a piece of string"), "record_scratch", 0.5))
    add(TextSlam(at("VO_10", "the idiot right"), lines=[("IT'S A STRING.", WHITE), ("PATRICK = IDIOT?", RED)],
                 times=[0, at("VO_10", "the idiot right")], size=170))
    add(TextSlam(at("VO_10", "then patrick alone"), lines=[("...THEN HE PULLS IT.", YEL)], size=160))
    clip("C05")

    t = at("VO_11", "a hidden compartment")
    add(Media(t, label="C05  THE PHOTO", path="clips/C05.mp4", src_in=4.0, tag="EXHIBIT B2  //  THE PHOTO")
        ).circle(at("VO_11", "embarrassing"), 1150, 560, 420, 320)
    hp = at("VO_11", "he played him")
    add(TextSlam(hp, lines=[("HE PLAYED HIM.", WHITE)], size=210))
    sfx.append((hp, "impact", 0.6))
    add(TextSlam(at("VO_11", "kept a secret"), lines=[("PATRICK  1", YEL), ("SPONGEBOB  0", WHITE)],
                 times=[at("VO_11", "kept a secret"), at("VO_11", "and won")], size=170))
    sfx.append((at("VO_11", "and won"), "monitor_beep", 0.5))
    tb = at("VO_11", "paul tibbitt")
    board2 = dict(sb=(620, 430, ["09.07.2001", "THE SECRET BOX", "Patrick wins"], at("VO_11", "one of the three")),
                  pt=(1300, 560, ["PAUL TIBBITT", "co-writer, The Secret Box"], tb))
    add(Board(at("VO_11", "one of the three"), items=board2, strings=[("sb", "pt", tb + 0.3)])).note(
        at("VO_11", "hold on"), "remember this name", 1300, 820, 70)
    sfx += [(at("VO_11", "one of the three"), "pin", 0.5), (tb, "pin", 0.7)]

    # ------------------------------------------------------------ 04 PUSH IT SOMEWHERE ELSE
    t = at("VO_12", "one month later")
    chapter(t, 4, "Push it somewhere else")
    add(TextSlam(at("VO_12", "alaskan"), lines=[("ALASKAN BULL WORM", RED)], size=170))
    sfx.append((at("VO_12", "alaskan"), "impact", 0.7))
    add(Media(at("VO_12", "the whole town"), label="B04  THE WORM", path="clips/B04.mp4",
              tag="EXHIBIT C  //  SANDY, SPONGEBOB & THE WORM  //  S2"))
    date(at("VO_12", "the whole town"), "10.12.2001", "SANDY, SPONGEBOB, AND THE WORM", "S2")
    add(TextSlam(at("VO_12", "with a plan"), lines=[("PATRICK HAS A PLAN.", YEL)], size=170))
    clip("C06")

    t = at("VO_13", "and then")
    add(Media(at("VO_13", "they do it"), label="B04  THEY PUSH THE CITY", path="clips/B04.mp4", src_in=3,
              tag="EXHIBIT C2  //  THEY ACTUALLY DID IT")).caption(at("VO_13", "push the city"), "THEY PUSHED THE CITY")
    add(TextSlam(at("VO_13", "grew up with"), lines=[("THE PATRICK", WHITE), ("I GREW UP WITH", YEL)], size=150))
    add(TextSlam(at("VO_13", "one bad day"), lines=[("THE WHOLE TOWN:", WHITE), ("ONE BAD DAY AWAY", RED)], size=150))
    add(TextSlam(at("VO_13", "sometimes his idea"), lines=[("PATRICK'S PLAN", WHITE)], size=170)).stamp(
        at("VO_13", "they go with"), "APPROVED", 1300, 760, -8, 110)
    sfx.append((at("VO_13", "they go with"), "stamp", 0.9))

    # ------------------------------------------------------------ 05 SACK OF DIAPERS
    t = at("VO_14", "this is where")
    chapter(t, 5, "Dumber than a sack of diapers")
    add(Board(t, items=dict(th=(960, 520, ["THEORY:", "Patrick used to be smart"], t))).stamp(
        at("VO_14", "falling apart"), "COLLAPSING", 1300, 760, -10, 100))
    sfx += [(at("VO_14", "falling apart"), "glitch", 0.5), (at("VO_14", "falling apart"), "stamp", 0.8)]
    s2 = at("VO_14", "im with stupid")
    add(Media(s2, label="B05  I'M WITH STUPID", path="clips/B05.mp4", tag="EXHIBIT D  //  I'M WITH STUPID  //  S2"))
    date(s2, "10.19.2001", "I'M WITH STUPID", "S2")
    lt = at("VO_14", "please try")
    add(Letter(at("VO_14", "a letter"), text="Please try to remember, but don't try too hard, or you'll hurt "
                                             "yourself like last time.",
               words=tl.words_between(lt, at("VO_14", "last time", end=True))))
    sfx.append((at("VO_14", "a letter"), "paper_slide", 0.6))
    clip("C07")

    t = at("VO_15", "so in")
    add(TextSlam(at("VO_15", "old news"), lines=[("ALREADY", WHITE), ("OLD NEWS", YEL)], size=170))
    add(TextSlam(at("VO_15", "his own family"), lines=[("HIS OWN FAMILY KNOWS.", WHITE)], size=150))
    add(Media(at("VO_15", "the plan"), label="B05  DINNER", path="clips/B05.mp4", src_in=2,
              tag="EXHIBIT D2  //  THE PLAN")).stamp(at("VO_15", "at dinner"), "FORGOT IT WAS AN ACT", 1250, 800, -7, 70)
    sfx.append((at("VO_15", "at dinner"), "stamp", 0.8))
    jm = at("VO_15", "janet")
    add(Board(at("VO_15", "and at the end"), items=dict(
        p=(960, 300, ["\"PATRICK'S PARENTS\""], at("VO_15", "and at the end")),
        j=(640, 640, ["JANET", "stranger"], jm), m=(1280, 640, ["MARTY", "stranger"], jm + 0.3)),
        strings=[("p", "j", jm + 0.1), ("p", "m", jm + 0.4)])).stamp(jm + 0.9, "NOT HIS PARENTS", 960, 900, -6, 90)
    sfx += [(jm, "pin", 0.6), (jm + 0.3, "pin", 0.6), (jm + 0.9, "stamp", 0.8)]
    ga = at("VO_15", "golden age")
    add(TextSlam(at("VO_15", "so no"), lines=[("A GOLDEN AGE?", WHITE)], size=180)).stamp(
        at("VO_15", "i checked"), "CHECKED: NONE", 1300, 780, -8, 100)
    sfx.append((at("VO_15", "i checked"), "stamp", 0.9))
    mon(ga, 0.8, "RESULT: NO CHANGE")

    # ------------------------------------------------------------ 06 A ONE-TIME THING
    t = at("VO_16", "but there is")
    chapter(t, 6, "A one-time thing")
    mon(t, 1.0)
    vd = at("VO_16", "february")
    add(Media(vd, label="B06  VALENTINE'S DAY", path="clips/B06.mp4", tag="EXHIBIT E  //  VALENTINE'S DAY  //  S1"))
    date(vd, "02.14.2000", "VALENTINE'S DAY", "S1")
    add(Media(at("VO_16", "hot air balloon"), label="B06  CHOCOLATE BALLOON", path="clips/B06.mp4", src_in=2,
              tag="EXHIBIT E2  //  THE GIFT", enter="cut")).caption(at("VO_16", "chocolate"), "MADE OF CHOCOLATE")
    hs = at("VO_16", "handshake")
    add(TextSlam(hs - 0.2, lines=[("1 X HANDSHAKE", WHITE)], size=190))
    sfx.append((hs - 0.2, "thud", 0.6))
    clip("C08")

    add(TextSlam(at("VO_17", "he snaps"), lines=[("HE SNAPS.", RED)], size=230))
    sfx.append((at("VO_17", "he snaps"), "impact", 0.8))
    add(Media(at("VO_17", "tears through"), label="C08  THE RAMPAGE", path="clips/C08.mp4", src_in=3,
              tag="EXHIBIT E3  //  THE DOCK"))
    jl = at("VO_17", "jay lender")
    add(Doc(jl, file="doc_lender.png", focus=(0.6, 0.35), zoom=0.35, zoom_time=3.5)).source(
        "Jay Lender, The Oral History of SpongeBob, Hogan's Alley #17 (2010)")
    add(TextSlam(at("VO_17", "and then he said"), lines=[("AND THEN:", YEL)], size=160))
    sfx.append((at("VO_17", "and then he said"), "riser", 0.3))

    q0, q1 = tl.beat_g("VO_18")
    lender = ("When that show came back, it felt so right that his dark side started popping up everywhere. "
              "You can plan ahead all you want, but the characters eventually tell you who they are.")
    add(Quote(q0 - 0.2, text=lender, who="JAY LENDER, WRITER, VALENTINE'S DAY", words=tl.words_between(q0, q1),
              size=58)).source("Hogan's Alley #17 (2010)")
    sw = at("VO_19", "swap")
    add(Quote(sw - 0.1, text=lender, who="JAY LENDER, WRITER, VALENTINE'S DAY", enter="cut", size=58)
        ).strike(at("VO_19", "dark side"), 1090, 437, 1420, 437).note(at("VO_19", "for stupid"), "stupid", 1260, 370, 80)
    sfx.append((at("VO_19", "for stupid"), "pop", 0.5))
    jw = at("VO_19", "a joke works once")
    add(Copies(jw, lines=["JOKE #1", "Patrick is dumb.", "(audience laughs)"], t_copy=at("VO_19", "do it again"),
               rate=6))
    sfx.append((at("VO_19", "do it again"), "receipt_printer", 0.35))
    add(TextSlam(at("VO_19", "its all he is"), lines=[("IT'S ALL HE IS.", WHITE)], size=200))
    sfx.append((at("VO_19", "its all he is"), "impact", 0.6))
    fl = at("VO_19", "flanderization")
    add(Dictionary(fl - 0.3, word="Flan·der·i·za·tion", pron="(noun)  //  TV Tropes",
                   definition="When one trait of a character gets exaggerated, episode after episode, until it "
                              "becomes the whole character.", t_def=fl + 0.3))
    add(TextSlam(at("VO_19", "made entirely of church"), lines=[("NICE NEIGHBOR", WHITE), ("↓", RED),
                                                                 ("100% CHURCH", YEL)], size=140,
                 times=[at("VO_19", "nice guy"), at("VO_19", "slowly"), at("VO_19", "made entirely of church")]))

    # ------------------------------------------------------------ 07 BRAIN CORAL
    t = at("VO_20", "and if you want")
    chapter(t, 7, "Brain coral")
    add(TextSlam(at("VO_20", "heres my pick"), lines=[("MY PICK:", YEL)], size=200))
    add(Doc(at("VO_20", "in 2004"), file="doc_tibbitt.png", focus=(0.4, 0.6), zoom=0.35, zoom_time=4)).source(
        "Wikipedia, \"Paul Tibbitt\"")
    pt = at("VO_20", "paul tibbitt")
    board3 = dict(sb=(620, 430, ["09.07.2001", "THE SECRET BOX", "Patrick wins"], pt - 5),
                  pt=(1300, 560, ["PAUL TIBBITT", "co-writer, The Secret Box", "showrunner, S4-S9"], pt - 5))
    add(Board(pt, items=board3, strings=[("sb", "pt", pt - 5)], focus=(1300, 560, 1.6), pullback=True)).note(
        at("VO_20", "the secret box guy"), "same guy", 1260, 860, 80)
    sfx.append((pt, "pin", 0.7))
    sp = at("VO_20", "october")
    add(Media(sp, label="C09  PATRICK SMARTPANTS", path="clips/C09.mp4", tag="EXHIBIT F  //  PATRICK SMARTPANTS  //  S4"
              ).stamp(at("VO_20", "patrick smartpants") + 0.2, "PRIME SUSPECT", 1350, 830, -8, 100))
    date(sp, "10.21.2005", "PATRICK SMARTPANTS", "S4")
    sfx += [(at("VO_20", "patrick smartpants") + 0.2, "stamp", 1.0), (at("VO_20", "patrick smartpants") + 0.25, "impact", 0.5)]
    clip("C09")

    add(TextSlam(at("VO_21", "danger"), lines=[("DANGER: CLIFF", RED)], size=200))
    sfx.append((at("VO_21", "knocks the top"), "impact", 0.6))
    add(TextSlam(at("VO_21", "knocks the top"), lines=[("HEAD: OFF", WHITE)], size=210))
    add(TextSlam(at("VO_21", "into art"), lines=[("ART", YEL), ("MATH", WHITE), ("CLASSICAL MUSIC", (120, 200, 255))],
                 times=[at("VO_21", "into art"), at("VO_21", "and math"), at("VO_21", "classical music")], size=170))
    sfx += [(at("VO_21", "into art"), "pop", 0.6), (at("VO_21", "and math"), "pop", 0.6),
            (at("VO_21", "classical music"), "pop", 0.6)]
    mon(at("VO_21", "into art"), 2.4, "BRAIN ACTIVITY ?!")
    add(Media(at("VO_21", "he tells squidward"), label="B07  SMART PATRICK", path="clips/B07.mp4",
              tag="EXHIBIT F2  //  SMART PATRICK"))
    add(TextSlam(at("VO_21", "hes unbearable"), lines=[("UNBEARABLE", RED), ("& LONELY", WHITE)],
                 times=[at("VO_21", "hes unbearable"), at("VO_21", "lonely")], size=190))
    add(TextSlam(at("VO_21", "actual physics"), lines=[("ACTUAL PHYSICS", (120, 200, 255))], size=200))
    sfx.append((at("VO_21", "actual physics"), "typing", 0.4))
    clip("C10")

    bc = at("VO_22", "brain coral")
    add(TextSlam(bc - 0.15, lines=[("BRAIN CORAL.", (255, 140, 160))], size=230))
    sfx.append((bc - 0.15, "impact", 0.7))
    mon(bc, 0.8)
    add(TextSlam(at("VO_22", "screwed a rock"), lines=[("A ROCK", WHITE), ("SHAPED LIKE A BRAIN", YEL)], size=150))
    add(Media(at("VO_22", "picks friendship"), label="B08  OLD HEAD BACK ON", path="clips/B08.mp4",
              tag="EXHIBIT F3  //  HAPPY ENDING")).caption(at("VO_22", "happy ending"), "HAPPY ENDING")
    s01 = at("VO_22", "in 2001")
    add(Split(s01, panels=[("2001: A PIECE OF STRING", "OUTSMARTS SPONGEBOB", s01),
                           ("2005: A HEAD INJURY", "SMART FOR 11 MINUTES", at("VO_22", "in 2005"))]))
    sfx.append((at("VO_22", "in 2005"), "whoosh_short", 0.4))
    acc = at("VO_22", "now its an accident")
    add(TextSlam(acc, lines=[("SMART PATRICK", WHITE)], size=190)).stamp(at("VO_22", "accident"), "ACCIDENT",
                                                                         1250, 760, -10, 120).note(
        at("VO_22", "before the credits"), "fixed before the credits", 960, 880, 64)
    sfx.append((at("VO_22", "accident"), "stamp", 0.9))

    qn = at("VO_23", "quick note")
    add(Media(qn, label="C09  PATRICK SMARTPANTS", path="clips/C09.mp4",
              tag="EXHIBIT F  //  PATRICK SMARTPANTS  //  S4", enter="cut").stamp(
        qn, "PRIME SUSPECT", 1350, 830, -8, 100).strike(at("VO_23", "thats my read"), 1130, 820, 1580, 800,
                                                        (20, 20, 20)).note(
        at("VO_23", "thats my read") + 0.3, "my read", 1350, 950, 90))
    sfx.append((at("VO_23", "thats my read"), "paper_slide", 0.5))
    add(TextSlam(at("VO_23", "nobody from the show"), lines=[("OFFICIAL STATEMENT:", WHITE), ("NONE", RED)],
                 times=[at("VO_23", "nobody from the show"), at("VO_23", "his head is empty")], size=170))
    tb2 = at("VO_23", "co-wrote")
    add(Board(at("VO_23", "and tibbitt"), items=board3, strings=[("sb", "pt", 0)])).note(
        tb2 + 0.4, "not one guy's fault", 960, 880, 70)
    add(TextSlam(at("VO_23", "but look at"), lines=[("WHAT THE STUPIDITY", WHITE), ("GETS USED FOR", YEL)], size=150))

    # ------------------------------------------------------------ 08 FIFTY KRABBY PATTIES
    t = at("VO_24", "same season")
    chapter(t, 8, "Fifty Krabby Patties")
    add(Media(t, label="C11  THAT'S NO LADY", path="clips/C11.mp4", tag="EXHIBIT G  //  THAT'S NO LADY  //  S4"))
    date(t, "11.25.2006", "THAT'S NO LADY", "S4")
    clip("C11")

    pn = at("VO_25", "august")
    add(Media(pn, label="B09  PAT NO PAY", path="clips/B09.mp4", tag="EXHIBIT H  //  PAT NO PAY  //  S5"))
    date(pn, "08.02.2007", "PAT NO PAY", "S5")
    f50 = at("VO_25", "fifty")
    add(Receipt(f50, head="THE KRUSTY KRAB", rows=[(f50 + 0.1, "50 x KRABBY PATTY", "$$$"),
                                                   (f50 + 0.6, "   + EXTRA CHEESE", "$$"),
                                                   (at("VO_25", "eats every"), "EATEN:", "50/50"),
                                                   (at("VO_25", "any money"), "PAID:", "$0.00")])
        ).stamp(at("VO_25", "lockdown"), "LOCKDOWN", 1350, 700, -10, 120)
    sfx += [(f50 + 0.1, "receipt_printer", 0.5), (at("VO_25", "any money"), "record_scratch", 0.5),
            (at("VO_25", "lockdown"), "impact", 0.7), (at("VO_25", "lockdown"), "stamp", 0.8)]
    s11 = at("VO_25", "september")
    add(Media(s11, label="B10  PET SITTER PAT", path="clips/B10.mp4", tag="EXHIBIT I  //  PET SITTER PAT  //  S8",
              flip_at=at("VO_25", "upside"), enter="cut"))
    date(s11, "09.16.2011", "PET SITTER PAT", "S8")
    add(Media(at("VO_25", "by the end"), label="B10  BEDTIME STORY", path="clips/B10.mp4", src_in=3,
              tag="EXHIBIT I2  //  WHO'S READING TO WHOM")).caption(at("VO_25", "bedtime story"),
                                                                     "THE SNAIL IS READING TO HIM")
    clip("C12")

    t = at("VO_26", "old patrick")
    add(Checklist(t, title="OLD PATRICK: DUMB ABOUT...", rows=[
        (at("VO_26", "jellyfishing"), "JELLYFISHING", None), (at("VO_26", "phones"), "PHONES", None),
        (at("VO_26", "the idea"), "RESTAURANT NAMES", None)]))
    sfx += [(at("VO_26", "jellyfishing"), "type_key", 0.6), (at("VO_26", "phones"), "type_key", 0.6),
            (at("VO_26", "the idea"), "type_key", 0.6)]
    ev = at("VO_26", "everything")
    add(Copies(ev - 0.2, lines=["LATER PATRICK: DUMB ABOUT", "EVERYTHING"], t_copy=ev, rate=14))
    add(Receipt(at("VO_26", "somebody else pays"), head="WHO PAYS FOR IT",
                rows=[(at("VO_26", "somebody else pays") + 0.1, "SQUIDWARD", "billed"),
                      (at("VO_26", "somebody else pays") + 0.4, "MR. KRABS", "billed"),
                      (at("VO_26", "somebody else pays") + 0.7, "GARY", "billed"),
                      (at("VO_26", "somebody else pays") + 1.0, "PATRICK", "$0.00")]))
    sfx.append((at("VO_26", "somebody else pays") + 0.1, "receipt_printer", 0.5))
    add(TextSlam(at("VO_26", "needs something to break"), lines=[("NEED SOMETHING", WHITE), ("TO BREAK?", WHITE)],
                 size=170))
    sp2 = at("VO_26", "send patrick in")
    add(TextSlam(at("VO_26", "they just"), lines=[("SEND PATRICK IN.", RED)], size=200))
    mon(sp2 + 0.2, 0.0, "FLATLINE", True)
    sfx.append((sp2 + 0.2, "flatline", 0.45))

    # ------------------------------------------------------------ 09 NO, THIS IS PATRICK
    t = at("VO_27", "now about phones")
    chapter(t, 9, "No, this is Patrick")
    mon(t, 0.5)
    bp = at("VO_27", "big pink loser")
    add(Media(bp, label="B12  BIG PINK LOSER", path="clips/B12.mp4", tag="EXHIBIT J  //  BIG PINK LOSER  //  S2"))
    date(bp, "02.03.2001", "BIG PINK LOSER", "S2")
    ap = at("VO_27", "answer the phone")
    add(TextSlam(ap - 0.2, lines=[("TASK #1:", WHITE), ("ANSWER THE PHONE", YEL)], size=160))
    sfx.append((ap + 0.4, "phone_ring", 0.5))
    clip("C13")

    st = at("VO_28", "stupid town")
    add(Media(at("VO_28", "a customer"), label="B12  STUPIDTOWN", path="clips/B12.mp4", src_in=3,
              tag="EXHIBIT J2  //  THE CUSTOMER")).caption(st, "\"DID YOU COME IN FROM STUPIDTOWN?\"")
    ff = at("VO_28", "fast forward")
    add(Counter(ff, range=(2001, 2021), t_start=ff + 0.1, t_end=ff + 1.1, label="FAST FORWARD"))
    sfx += [(ff + 0.1, "riser", 0.3)]
    pr = at("VO_28", "nickelodeon premieres")
    add(Doc(pr, file="doc_pss.png", focus=(0.5, 0.3), zoom=0.3, zoom_time=3)).source("Wikipedia, \"The Patrick Star Show\"")
    date(pr, "07.09.2021", "THE PATRICK STAR SHOW", "S1")
    add(Media(at("VO_28", "talk show"), label="B11  THE PATRICK STAR SHOW", path="clips/B11.mp4",
              tag="EXHIBIT K  //  THE PATRICK STAR SHOW  //  2021"))
    add(TextSlam(at("VO_28", "twenty years after"), lines=[("CAN'T ANSWER A PHONE", WHITE), ("↓", RED),
                                                            ("HAS HIS OWN SHOW", YEL)], size=140,
                 times=[at("VO_28", "twenty years after"), at("VO_28", "he has his own"), at("VO_28", "he has his own") + 0.1]))
    kk = at("VO_28", "is this the")
    add(TextSlam(kk - 0.3, lines=[("\"IS THIS THE", WHITE), ("KRUSTY KRAB?\"", WHITE)], size=170))
    sfx.append((kk - 0.6, "phone_ring", 0.45))
    tp = at("VO_28", "this is patrick")
    add(TextSlam(tp, lines=[("NO.", RED), ("THIS IS PATRICK.", WHITE)], size=190))
    sfx.append((tp + 0.9, "hangup", 0.8))

    # ------------------------------------------------------------ 10 ALL HEAD
    t = at("VO_29", "okay one last thing")
    chapter(t, 10, "All head")
    add(Folder(t, label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "APPENDIX: BIOLOGY"]))
    sfx += [(t, "whoosh", 0.5), (t + 0.3, "folder_slam", 0.8)]
    add(Photo(at("VO_29", "steven hillenburg"), file="hillenburg.jpg", caption="Stephen Hillenburg",
              credit="Photo: Carlos Cazurro Burgos, CC BY-SA 3.0", w=640, h=680)).stamp(
        at("VO_29", "marine biology"), "MARINE BIOLOGIST", 1350, 820, -8, 80)
    sfx.append((at("VO_29", "marine biology"), "stamp", 0.8))
    add(Doc(at("VO_29", "when he explained"), file="doc_dumbest.png", focus=(0.65, 0.33), zoom=0.3,
            zoom_time=4)).source("Hillenburg, SpongeBob Movie DVD featurette (via Wikipedia)")
    add(Media(at("VO_29", "if you remember"), label="C08  THE RAMPAGE", path="clips/C08.mp4", src_in=2,
              tag="EXHIBIT E3  //  \"VERY ACTIVE AND AGGRESSIVE\""))

    rs = at("VO_30", "real starfish")
    add(Photo(rs, file="starfish2.jpg", caption="A real starfish (Pisaster ochraceus)",
              credit="Photo: Charles J. Sharp, CC BY-SA 4.0", w=860, h=600, rot=-2))
    sfx.append((rs, "shutter", 0.5))
    nb = at("VO_30", "none")
    add(TextSlam(nb, lines=[("BRAIN:", WHITE), ("NONE", RED)], size=220))
    sfx.append((nb, "impact", 0.7))
    mon(nb, 0.0, "BRAIN: NOT FOUND", True)
    rn = at("VO_30", "just a ring")
    sf = add(Starfish(rn - 0.2, t_nerves=rn + 0.2, t_head=at("VO_30", "the genes that build a head"),
                      labels=[(rn + 0.3, "NERVE RING", (255, 245, 120), 380),
                              (at("VO_30", "down each arm"), "+ 5 RADIAL NERVES", (255, 245, 120), 440)]))
    nt = at("VO_30", "in november")
    add(Doc(nt, file="doc_nature.png", focus=(0.4, 0.3), zoom=0.2, w=1150)).source(
        "Formery et al., Nature 623 (2023); Stanford University")
    date(nt, "11.01.2023", "NATURE, VOL. 623", "STANFORD")
    sl = at("VO_30", "they sliced")
    add(Starfish(sl, t_nerves=sl, labels=[(sl + 0.2, "SLICED + GENE-MAPPED", WHITE, 380),
                                          (at("VO_30", "nothing that builds a body"), "BODY GENES: ~NONE", (255, 120, 120), 440)]))
    hd = at("VO_30", "the genes that build a head")
    add(Starfish(hd, t_head=hd + 0.1, labels=[(hd + 0.4, "HEAD GENES:", (80, 200, 255), 380),
                                              (hd + 1.2, "CENTER + EVERY ARM", (80, 200, 255), 440)]))
    sfx.append((hd + 0.1, "riser", 0.3))
    sh = at("VO_30", "the headlines")
    add(Photo(sh, file="starfish1.jpg", caption="Basically a head.", credit="Photo: Hans Hillewaert, CC BY-SA 4.0",
              w=860, h=600, rot=2))
    wa = at("VO_30", "a starfish is basically")
    add(TextSlam(wa, lines=[("A STARFISH", WHITE), ("IS A HEAD.", YEL)], size=200,
                 times=[wa, at("VO_30", "a head")]))
    sfx.append((at("VO_30", "a head"), "impact", 0.7))
    add(Photo(at("VO_30", "walking around"), file="starfish3.jpg", caption="walking around",
              credit="Photo: Steven Pavlov, CC BY-SA 4.0", w=860, h=600, rot=-3, enter="cut"))

    gh = at("VO_31", "giant head")
    add(TextSlam(gh - 0.2, lines=[("GIANT HEAD", WHITE), ("NO BRAIN", RED)], size=200,
                 times=[gh - 0.2, at("VO_31", "no brain")]))
    sfx.append((at("VO_31", "no brain"), "thud", 0.7))
    add(Folder(at("VO_31", "he was the most"), label=["FILE NO. 0047", "SUBJECT: PATRICK STAR", "FINDING:"],
               enter="cut")).stamp(at("VO_31", "scientifically accurate"), "SCIENTIFICALLY ACCURATE", 1100, 760, -8, 90)
    sfx.append((at("VO_31", "scientifically accurate"), "stamp", 1.0))
    ct = at("VO_31", "science just took")
    add(Counter(ct, range=(1999, 2023), t_start=ct + 0.2, t_end=at("VO_31", "catch up", end=True),
                label="SCIENCE CATCHING UP"))

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
    strings = [("a", "b", t), ("b", "c", t), ("c", "d", t), ("d", "p", t), ("p", "f", t), ("f", "g", t), ("g", "h", t),
               ("e", "f", t)]
    add(Board(t, items=items, strings=strings, focus=(960, 540, 1.5), pullback=True))
    op = at("VO_32", "on paper")
    add(Board(op, items=items, strings=strings, enter="cut").circle(op + 0.2, 330, 300, 470, 260).note(
        op + 0.5, "on paper", 330, 470, 64))
    sfx.append((op + 0.5, "pop", 0.4))
    pl = at("VO_32", "punchline with legs")
    add(TextSlam(at("VO_32", "but when did"), lines=[("A PUNCHLINE", WHITE), ("WITH LEGS", YEL)], size=180,
                 times=[at("VO_32", "punchline"), at("VO_32", "with legs")]))
    o21 = at("VO_32", "im going with")
    add(Board(o21, items=items, strings=strings, enter="cut", focus=(820, 640, 1.0)).circle(
        at("VO_32", "october") + 0.1, 330, 300, 470, 260).circle(at("VO_32", "october") + 0.2, 820, 640, 520, 280).note(
        at("VO_32", "october") + 0.6, "my pick", 820, 820, 70))
    sfx += [(at("VO_32", "october") + 0.2, "impact", 0.5)]
    add(TextSlam(at("VO_32", "by accident"), lines=[("SMART = ACCIDENT", WHITE)], size=180))
    yp = at("VO_32", "you might pick")
    add(TextSlam(yp, lines=[("YOUR PICK?", YEL), ("↓ COMMENTS ↓", WHITE)], size=170,
                 times=[yp, at("VO_32", "tell me")]))
    fi = at("VO_32", "and if theres")
    add(Folder(fi, label=["FILE NO. 0048", "SUBJECT: ???", "SUBMITTED BY: YOU"]))
    sfx += [(fi, "whoosh", 0.5), (fi + 0.3, "folder_slam", 0.7)]
    rt = at("VO_32", "i read them")
    add(Black(rt + 0.7, text="I READ THEM.", size=90, type_time=0.6))
    sfx.append((rt + 0.7, "typing", 0.5))

    end = next(s for s in tl.segments if s["kind"] == "end")
    add(EndScreen(end["g0"]))
    sfx.append((end["g0"], "stamp", 0.8))
    mon(end["g0"] - 3, 0, None)
    cards.sort(key=lambda c: c.t0)
    return cards, dates, chapters, sfx, monitor
