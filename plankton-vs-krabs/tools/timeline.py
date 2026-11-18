"""Edit decision list. Each shot starts on an ANCHOR phrase (words from that chunk's voiceover)
and lasts until the next shot. Visuals: C(clip_id, ...) = episode clip you supply, G(name, ...) = original graphic.
SFX: "name" or ("name", offset_seconds, volume)."""

from gfx import KRABS, PLANK, KAREN, YELLOW, WHITE, INK


def C(cid, **o): o["type"] = "clip"; o["id"] = cid; return o
def G(_gname, **o): return {"type": "gfx", "name": _gname, "args": o}
def S(anchor, v, *sfx): return {"at": anchor, "v": v, "sfx": list(sfx)}


# ---------------- CLIP LIST (you supply these; see 03_CLIP_LIST.md) ----------------
CLIPS = {
    "C01": ("Plankton!", 1999, "Plankton's first scene in the Krusty Krab: yelling at Krabs ('I went to college!') and being thrown out the door"),
    "C02": ("any episode", None, "Krusty Krab exterior wide shot, front door visible"),
    "C03": ("any episode", None, "Chum Bucket exterior wide shot (ideally with the Krusty Krab across the road)"),
    "C04": ("The Algae's Always Greener", 2002, "Karen on her monitor talking to Plankton"),
    "C05": ("Plankton's Pet", None, "Plankton with Spot the amoeba"),
    "C06": ("Plankton's Regular", None, "the regular customer happily eating chum at the Chum Bucket"),
    "C07": ("Friend or Foe", 2007, "young Krabs and young Plankton together as kids"),
    "C08": ("Friend or Foe", 2007, "opening: SpongeBob asks Mr. Krabs about Plankton"),
    "C09": ("Friend or Foe", 2007, "Krabs's version: kid Plankton as the evil one"),
    "C10": ("Friend or Foe", 2007, "Krabs's version: Krabs tossed into the garbage pile"),
    "C11": ("Friend or Foe", 2007, "Plankton's version: same scenes, roles swapped"),
    "C12": ("Friend or Foe", 2007, "Karen starts telling the real version"),
    "C13": ("Friend or Foe", 2007, "carnival: little Krabs finds the penny and buys Plankton the balloon"),
    "C14": ("Friend or Foe", 2007, "Stinky's Burgers at the dump, owner refuses to serve them"),
    "C15": ("Friend or Foe", 2007, "Plabs Burgers stand at the dump, no customers"),
    "C16": ("Friend or Foe", 2007, "Old Man Jenkins takes a bite and collapses"),
    "C17": ("Friend or Foe", 2007, "the two blame each other and rip the recipe in half"),
    "C18": ("Friend or Foe", 2007, "shelf falls, ingredients spill into the mix; Krabs left with the new recipe"),
    "C19": ("Friend or Foe", 2007, "Plankton storms off; his Chum Burger fails; he vows revenge"),
    "C20": ("Plankton!", 1999, "Plankton inside SpongeBob's head controlling him"),
    "C21": ("Imitation Krabs", None, "Plankton's robot Mr. Krabs"),
    "C22": ("F.U.N.", None, "SpongeBob and Plankton being friends"),
    "C23": ("montage", None, "4-6 quick moments of Plankton schemes failing / being flung out (any episodes)"),
    "C24": ("The SpongeBob SquarePants Movie", 2004, "Plankton steals Neptune's crown / Krabs gets frozen"),
    "C25": ("The SpongeBob SquarePants Movie", 2004, "bucket helmets on everyone, Planktopolis"),
    "C26": ("The SpongeBob SquarePants Movie", 2004, "SpongeBob's guitar rock moment, buckets blow off"),
    "C27": ("Single Cell Anniversary", None, "Karen steals the formula herself; Plankton messes it up"),
    "C28": ("Plankton's Regular", None, "the reveal that Karen pays the regular"),
    "C29": ("Plankton's Regular", None, "Mr. Krabs adds chum to the Krusty Krab menu"),
    "C30": ("Enemy In-Law", 2005, "Plankton dating Mama Krabs; Mr. Krabs freaking out"),
    "C31": ("One Coarse Meal", None, "Mr. Krabs in the Pearl/whale disguise scaring Plankton"),
    "C32": ("One Coarse Meal", None, "SpongeBob telling Krabs he's gone too far"),
    "C33": ("Born Again Krabs", 2003, "Krabs trades SpongeBob to the Flying Dutchman for 62 cents"),
    "C34": ("Born Again Krabs", 2003, "Squidward calls Krabs out"),
    "C35": ("Plankton Retires", 2017, "Plankton announces his retirement / retirement home"),
    "C36": ("Plankton Retires", 2017, "Krabs and SpongeBob spying from the ceiling fan"),
    "C37": ("Plankton Retires", 2017, "robot reveal: Plankton's robot, then Krabs's robots"),
    "C38": ("Plankton: The Movie (trailer)", 2025, "Karen as the villain / giant Karen"),
    "C39": ("Friend or Foe", 2007, "ending: they make up, Plankton snatches the formula, chase"),
    "C40": ("any episode", None, "Mr. Krabs close-up (scowl / counting money)"),
    "C41": ("any episode", None, "the Krabby Patty secret formula bottle or safe"),
    "C43": ("any episode", None, "Plankton evil laugh"),
    "C44": ("any episode", None, "Pearl on screen"),
    "C45": ("Friend or Foe", 2007, "kids picking on young Krabs and Plankton"),
}

FOF = "FRIEND OR FOE · 2007"

# ---------------- DIALOGUE BITES ----------------
# The narration pauses, the show line plays with its own audio, then narration resumes (the channel does this
# 10-30 times per video). Each bite is OPTIONAL: if clips/Bxx.* is missing it is skipped and the VO runs straight.
# (anchor = the VO words the bite plays *before*; "@end" = after the chunk's last line; seconds = max length)
BITES = {
    "01": [("He has been", "B01", 4.6)],
    "05": [("and what we get", "B02", 1.8)],
    "08": [("And the owner", "B13", 3.8)],
    "09": [("They grab the paper", "B04", 3.5), ("and nobody wants it", "B14", 2.6)],
    "11": [("He's built", "B12", 3.7)],
    "12": [("Which is bleak", "B05", 5.1)],
    "13": [("which, fair", "B06", 4.6)],
    "14": [("So yeah", "B08", 6.0)],
    "15": [("Both of them", "B09", 3.3)],
    "16": [("They had the chance", "B10", 4.1)],
    "17": [("@end", "B11", 2.0)],
}
BITE_CLIPS = {
    "B01": ("Plankton!", 1999, "Plankton's first threat to Krabs about the formula"),
    "B02": ("Friend or Foe", 2007, "Krabs: the story is about to get juicy"),
    "B04": ("Friend or Foe", 2007, "kid Krabs and Plankton arguing over whose recipe it is"),
    "B05": ("Plankton's Regular", None, "Karen sensing the regular coming in with cash"),
    "B06": ("Enemy In-Law", 2005, "Mr. Krabs insisting Plankton is after the formula"),
    "B08": ("Born Again Krabs", 2003, "Squidward calls out the 62-cent deal; Krabs's reply"),
    "B09": ("Imitation Krabs", None, "the real Krabs vs. the robot Krabs"),
    "B10": ("Friend or Foe", 2007, "Plankton admitting he was after the formula"),
    "B11": ("Plankton!", 1999, "Plankton: \"I went to college.\" (the payoff)"),
    "B12": ("Plankton!", 1999, "SpongeBob fighting Plankton out of his brain"),
    "B13": ("Friend or Foe", 2007, "the Stinky's Burgers jingle line"),
    "B14": ("Friend or Foe", 2007, "Plankton pitching his chum burger"),
}

# ---------------- YOUTUBE CHAPTERS (written into the description) ----------------
CHAPTERS = [
    ("01", None, "July 31, 1999"),
    ("02", "I went back", "I was watching this wrong"),
    ("03", "Quick refresher", "The smallest villain on TV"),
    ("04", None, "The plan (every time)"),
    ("05", "The show actually", "Three liars and a computer"),
    ("07", None, "Karen's version"),
    ("08", "They call it", "Plabs"),
    ("09", None, "The fight that made the Krabby Patty"),
    ("10", "So let's say", "He was in the room"),
    ("11", None, "The losing streak"),
    ("11", "The one time", "Plan Z"),
    ("12", "Then there's Plankton's", "One customer"),
    ("13", "And once you see", "Okay, about Krabs"),
    ("14", None, "One Coarse Meal"),
    ("14", "This is also", "62 cents"),
    ("15", None, "Plankton Retires"),
    ("16", None, "Who's the bad guy?"),
    ("17", None, "He went to college"),
]

# chapter labels shown top-right on clip shots
CH = {
    "03": "CH.1 · THE SMALLEST VILLAIN", "05": "CH.2 · THREE LIARS", "11": "CH.3 · THE LOSING STREAK",
    "13": "CH.4 · OKAY, ABOUT KRABS", "15": "CH.5 · NEITHER WANTS IT TO END", "16": "THE VERDICT",
}

TAIL = {"02": .5, "04": .7, "10": .8, "12": .5, "14": .6, "15": .5, "16": 1.6, "17": 3.8}

T = {}

T["01"] = [
    S("On July", G("polaroid", still="C01", caption="Plankton! (1999)")),
    S("a guy about", C("C01", zoom="in"), ("whoosh_short", -.15, .4)),
    S("sesame seed", C("C01", ss=1, zoom="punch"), "pop"),
    S("screamed at", C("C01", ss=2, zoom="in"), ("thump", 0, .7)),
    S("got thrown out", C("C01", ss=4, zoom="out"), "door_slam"),
    S("He has been", C("C23", zoom="in", fx="vhs"), ("whoosh_short", -.1, .5)),
    S("Twenty-seven years", C("C23", ss=2, zoom="in")),
    S("Same door", C("C02", zoom="punch"), "thump"),
    S("Same crab", C("C40", zoom="punch"), "thump"),
    S("He's married", C("C04", zoom="in"), ("shutter", 0, .4)),
    S("pet amoeba", C("C05", zoom="in"), "bloop"),
    S("He owns a restaurant", G("map_street"), ("whoosh", -.15, .6)),
    S("his one regular", C("C06", zoom="in")),
    S("secretly being paid", C("C06", ss=2, freeze=True), ("stamp", .1, .8)),
]

T["02"] = [
    S("And the crab", C("C40", zoom="in"), ("whoosh_short", -.12, .5)),
    S("best friend", C("C07", freeze=True, fx="sepia", zoom="punch", tag=FOF), ("scratch", -.05, .8)),
    S("They grew up", C("C07", ss=2, fx="sepia", zoom="in")),
    S("invented the Krabby", C("C18", zoom="punch", fx="sepia"), ("thump", 0, .6)),
    S("We'll get to that", C("C17", fx="vhs", zoom="in"), ("shutter", 0, .4)),
    S("I went back", G("watchlist"), ("type_burst", 0, .4)),
    S("dresses up", C("C31", freeze=True, zoom="punch"), ("thump", 0, .8)),
    S("psychologically", C("C31", ss=2, zoom="punch"), ("thump", 0, .6)),
    S("I realized", C("C02", zoom="in")),
    S("This rivalry", G("heartbreak", text=""), ("rip", .55, .8)),
    S("Two guys", C("C17", fx="sepia", zoom="in")),
    S("garbage dump", C("C15", fx="sepia", zoom="punch"), "thump"),
    S("spent the rest", C("C23", ss=2, zoom="in")),
    S("And one of them", G("verdict", title=""), ("thump", 0, .6)),
    S("evil laugh", C("C43", zoom="punch"), ("thump", .5, .7)),
]

T["03"] = [
    S("Quick refresher", G("title_card", num="PART 1", title="THE SMALLEST VILLAIN ON TELEVISION", accent=PLANK), ("boom", 0, .5)),
    S("Sheldon J", C("C20", zoom="in"), "shutter"),
    S("Owner of", C("C03", zoom="in"), ("whoosh_short", -.12, .6)),
    S("directly across", G("map_street", note=""), "pop"),
    S("bold business", C("C03", freeze=True, zoom="punch"), "thump"),
    S("That's opening", C("C03", ss=2, zoom="out")),
    S("Fun fact", C("C20", ss=1, zoom="in")),
    S("so small", G("magnify"), ("bloop", .5, .7), ("scribble", 1.4, .5)),
    S("The animators", C("C20", ss=2, zoom="in")),
    S("only supposed", C("C43", zoom="in")),
    S("Nickelodeon wanted", C("C20", ss=3, zoom="in")),
    S("Doug Lawrence", C("C43", ss=1, zoom="punch")),
    S("every single one", C("C23", zoom="in"), ("slide_down", .2, .5)),
]

T["04"] = [
    S("And the plan", C("C21", zoom="in"), ("whoosh_short", -.12, .4)),
    S("Steal the secret", C("C41", zoom="in")),
    S("Make Krabby", C("C03", ss=1, zoom="in")),
    S("Put Mr", C("C40", zoom="punch")),
    S("rule the world", C("C25", ss=1, zoom="in")),
    S("It never works", G("scoreboard", p="0", k="∞"), ("thump", 0, .5)),
    S("Except one", C("C25", fx="vhs", zoom="in"), ("shutter", 0, .6)),
    S("that time went", G("scoreboard", p="1*", k="∞", note="*see part 3"), ("tick", 0, .4)),
]

T["05"] = [
    S("So how do", C("C23", ss=3, zoom="in"), ("whoosh", -.15, .6)),
    S("The show actually", G("title_card", num="PART 2", title="THREE LIARS AND A COMPUTER", accent=YELLOW), ("boom", 0, .5)),
    S("Season five", G("polaroid", still="C08", caption="Friend or Foe (season 5, 2007)", rot=2)),
    S("SpongeBob asks", C("C08", ss=2, zoom="in")),
    S("the same story", G("three_versions", stills=("C09", "C11", "C12")), "pop", ("pop", .12, .8), ("pop", .24, .8)),
    S("A DVD reviewer", C("C08", ss=3, zoom="in")),
    S("The Kurosawa", C("C09", fx="sepia", zoom="in")),
    S("About a SpongeBob", C("C08", ss=4, zoom="punch"), "pop"),
    S("nobody in this story", C("C12", zoom="in"), ("shutter", .4, .4)),
]

T["06"] = [
    S("Version one", G("three_versions", stills=("C09", "C11", "C12"), active=0), ("stamp", 0, .6)),
    S("In Krabs's version", C("C09", fx="sepia", zoom="in", label=("VERSION 1 · KRABS", KRABS))),
    S("Krabs tries", C("C10", fx="sepia", zoom="in", label=("VERSION 1 · KRABS", KRABS)), ("thump", .6, .5)),
    S("Very noble", C("C09", freeze=True, fx="sepia", zoom="punch"), "ding"),
    S("Weird how", C("C40", zoom="in")),
    S("Version two", G("three_versions", stills=("C09", "C11", "C12"), active=1, unreliable=(0,)), ("whoosh_short", -.2, .5), ("stamp", .3, .7)),
    S("It's the same", C("C11", fx="sepia", zoom="in", label=("VERSION 2 · PLANKTON", PLANK))),
    S("except now", C("C11", ss=3, fx="sepia", zoom="punch", label=("VERSION 2 · PLANKTON", PLANK)), ("thump", 0, .7)),
    S("He just swapped", C("C11", ss=5, fx="sepia", zoom="in", label=("VERSION 2 · PLANKTON", PLANK))),
    S("And then there's", G("three_versions", stills=("C09", "C11", "C12"), active=2, unreliable=(0, 1)), ("stamp", .35, .7)),
    S("Karen. The only", C("C12", zoom="in", label=("VERSION 3 · KAREN", KAREN))),
    S("can't stand", C("C12", ss=3, zoom="punch", label=("VERSION 3 · KAREN", KAREN)), "thump"),
]

T["07"] = [
    S("So, according", C("C12", ss=1, zoom="in", label=("VERSION 3 · KAREN", KAREN)), ("shutter", 0, .4)),
    S("best friends", C("C07", fx="sepia", zoom="in", tag=FOF)),
    S("both outcasts", C("C07", ss=3, fx="sepia", zoom="in")),
    S("the other kids", C("C45", fx="sepia", zoom="in")),
    S("There's a moment", C("C16", fx="sepia", zoom="in")),
    S("finds a penny", G("coins", text="", n=1), "coin"),
    S("the same man", C("C33", fx="vhs", zoom="in", tag="BORN AGAIN KRABS · 2003"), ("whoosh_short", -.1, .5)),
    S("spends it", C("C07", ss=1, fx="sepia", zoom="in")),
    S("For Plankton", C("C16", ss=7, freeze=True, fx="sepia", zoom="in")),
    S("Remember the balloon", G("balloon", text=""), "thump"),
]

T["08"] = [
    S("So the two", C("C14", fx="sepia", zoom="in"), ("whoosh_short", -.12, .5)),
    S("And the owner", C("C14", ss=3, fx="sepia", zoom="in"), ("stamp", .4, .8)),
    S("Then the health", C("C14", ss=6, fx="sepia", zoom="punch"), ("stamp", .3, .8)),
    S("and the boys", C("C15", fx="sepia", zoom="in")),
    S("At the dump", C("C15", ss=2, fx="sepia", zoom="punch"), "thump"),
    S("They call it", C("C15", ss=1, fx="sepia", zoom="punch")),
    S("Nobody comes", C("C15", ss=4, fx="sepia", zoom="in"), ("tick", 0, .25, 4, .5)),
    S("an old man", C("C16", fx="sepia", zoom="in")),
    S("takes one bite", C("C16", ss=2, fx="sepia", zoom="punch")),
    S("and collapses", C("C16", ss=4, fx="sepia", zoom="punch"), ("thump", 0, .8)),
    S("The burger poisoned", C("C16", ss=5, freeze=True, fx="bw", zoom="in"), ("ring", .1, .3)),
]

T["09"] = [
    S("And instead", C("C17", fx="sepia", zoom="in")),
    S("It's your recipe", C("C17", ss=2, fx="sepia", zoom="punch"), ("whoosh_short", -.1, .6)),
    S("No, it's your", C("C17", ss=3, fx="sepia", zoom="punch"), ("whoosh_short", -.1, .6)),
    S("They grab", G("rip_paper", rip_at=1.0), ("rip", .9, .9)),
    S("During the fight", C("C18", fx="sepia", zoom="in"), ("thump", .3, .7)),
    S("Ingredients go", C("C18", ss=2, fx="sepia", zoom="punch"), ("bubbles", 0, .5)),
    S("And that accident", C("C18", ss=3, fx="sepia", zoom="in")),
    S("is the Krabby", C("C18", ss=4, freeze=True, fx="sepia", zoom="punch"), ("thump", 0, .7), ("ding", .05, .5)),
    S("Krabs is the one", C("C18", ss=5, fx="sepia", zoom="in"), "thump"),
    S("So Krabs keeps", C("C41", zoom="in"), "cha_ching"),
    S("Plankton storms", C("C19", fx="sepia", zoom="in")),
    S("Chum Burger", C("C19", ss=2, fx="sepia", zoom="punch"), ("thump", .2, .4)),
    S("And that's the day", C("C19", ss=4, fx="sepia", zoom="in"), ("thump", .4, .6)),
]

T["10"] = [
    S("Now, to be fair", C("C30", zoom="in", tag="ENEMY IN-LAW · 2005"), ("shutter", 0, .4)),
    S("Another episode", C("C30", ss=2, zoom="in")),
    S("I'm choosing", C("C40", zoom="in")),
    S("So let's say", C("C17", fx="sepia", zoom="in")),
    S("invented by two", C("C07", ss=1, fx="sepia", zoom="in")),
    S("By accident", C("C18", ss=2, fx="sepia", zoom="punch")),
    S("While they were", C("C17", ss=3, fx="sepia", zoom="in")),
    S("And one of them", C("C41", zoom="in")),
    S("Which means", C("C23", ss=1, zoom="in")),
    S("something he was", C("C18", ss=4, freeze=True, fx="sepia", zoom="in"), ("thump", 0, .6)),
]

T["11"] = [
    S("So. How's", G("title_card", num="PART 3", title="THE LOSING STREAK", accent=KRABS), ("boom", 0, .5)),
    S("Badly", G("scoreboard", p="0", k="∞"), ("thump", 0, .5)),
    S("In his very first", C("C20", zoom="in", tag="PLANKTON! · 1999"), ("whoosh_short", -.12, .5)),
    S("He's built", C("C21", zoom="in", tag="IMITATION KRABS"), ("shutter", 0, .4)),
    S("He's tried being", C("C22", zoom="in", tag="F.U.N."), "pop"),
    S("He's tried disguises", C("C23", zoom="punch"), ("whoosh_short", -.1, .5)),
    S("flat-out lies", C("C23", ss=2, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("more lasers", C("C23", ss=4, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("flying out", C("C01", ss=4, zoom="in"), ("slide_down", 0, .7)),
    S("The one time", G("polaroid", still="C24", caption="The SpongeBob SquarePants Movie (2004)", rot=2)),
    S("Plan Z", C("C24", ss=1, zoom="punch")),
    S("Which, of course", C("C04", zoom="punch"), "pop"),
    S("Plankton steals", C("C24", ss=2, zoom="in")),
    S("frames Mr", C("C24", ss=4, zoom="punch"), "thump"),
    S("sticks a bucket", C("C25", zoom="in"), "pop"),
    S("Planktopolis", C("C25", ss=3, zoom="punch"), "ding"),
    S("He finally wins", G("scoreboard", p="1", k="∞"), ("cha_ching", 0, .7)),
    S("And it lasts", C("C26", zoom="in")),
    S("with a guitar", C("C26", ss=2, zoom="punch"), ("thump", 0, .8), ("thump", .05, .6)),
]

T["12"] = [
    S("And when he gets", G("scoreboard", p="0", k="∞", note="win revoked"), ("thump", 0, .5)),
    S("In Single Cell", C("C27", zoom="in", tag="SINGLE CELL ANNIVERSARY"), ("whoosh_short", -.12, .5)),
    S("Karen just goes", C("C27", ss=2, zoom="in")),
    S("And Plankton is the one", C("C27", ss=4, zoom="punch"), ("thump", .3, .4)),
    S("Then there's Plankton's", C("C06", zoom="in", tag="PLANKTON'S REGULAR"), ("whoosh_short", -.12, .5)),
    S("One guy", C("C06", ss=1, freeze=True, zoom="punch"), "ding"),
    S("Comes in every", C("C06", ss=2, zoom="in")),
    S("Turns out", C("C28", zoom="punch"), ("cha_ching", 0, .7)),
    S("Which is bleak", C("C28", ss=2, freeze=True, fx="bw", zoom="in"), "thump"),
    S("Now watch", C("C40", zoom="in"), ("riser", .2, .5)),
]

T["13"] = [
    S("He puts chum", C("C29", zoom="in"), ("thump", 0, .8)),
    S("To steal the one", C("C29", ss=2, zoom="punch"), ("thump", 0, .6)),
    S("He runs the most", C("C02", zoom="in")),
    S("he cannot let", C("C40", zoom="in")),
    S("Not even a fake", C("C28", ss=2, freeze=True, zoom="punch"), ("stamp", .1, .8)),
    S("And once you see", G("title_card", num="PART 4", title="OKAY, ABOUT KRABS", accent=KRABS), ("boom", 0, .5)),
    S("In Enemy In-Law", C("C30", zoom="in", tag="ENEMY IN-LAW · 2005")),
    S("dating Mr", C("C30", ss=2, zoom="punch"), ("thump", 0, .7)),
    S("Krabs loses", C("C30", ss=4, zoom="punch"), ("thump", 0, .6)),
    S("which, fair", C("C30", ss=5, freeze=True, zoom="in")),
    S("But his first", C("C40", zoom="in")),
    S("But it never", G("pie"), ("pop", .2, .6), ("pop", 1.3, .8)),
]

T["14"] = [
    S("Then there's One", C("C31", zoom="in", tag="ONE COARSE MEAL"), ("whoosh_short", -.12, .5)),
    S("Krabs finds out", C("C31", ss=1, zoom="in")),
    S("Pearl, is a whale", C("C44", zoom="punch"), "bloop"),
    S("So Krabs starts", C("C31", ss=3, zoom="punch"), ("thump", 0, .6)),
    S("Over and over", C("C31", ss=5, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("Popping up", C("C31", ss=6, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("And it stops", C("C31", ss=7, fx="bw", zoom="in"), "thump"),
    S("genuinely dark", C("C31", ss=8, fx="dark", zoom="in")),
    S("Dark enough", C("C32", zoom="in")),
    S("gone too far", C("C32", ss=2, zoom="punch"), ("thump", 0, .6)),
    S("This is also", C("C33", zoom="in", tag="BORN AGAIN KRABS · 2003")),
    S("sixty-two cents", C("C33", ss=2, zoom="punch"), "coin"),
    S("when Squidward", C("C34", zoom="in")),
    S("whether he could've", C("C34", ss=2, freeze=True, zoom="punch"), ("thump", .3, .7)),
    S("So yeah", C("C43", zoom="in")),
    S("He's got the laugh", C("C43", ss=1, zoom="punch"), "thump"),
    S("But if you just", C("C29", ss=1, zoom="punch"), "shutter"),
    S("episode after", C("C31", ss=4, zoom="punch"), "shutter"),
    S("the crab has", C("C40", zoom="in", fx="dark"), ("thump", 0, .7)),
]

T["15"] = [
    S("And here's the", G("title_card", num="PART 5", title="NEITHER OF THEM WANTS IT TO END", accent=KAREN), ("boom", 0, .5)),
    S("Plankton Retires", G("polaroid", still="C35", caption="Plankton Retires (2017)")),
    S("Written, by the way", C("C35", ss=1, zoom="in")),
    S("Plankton announces", C("C35", ss=2, zoom="in")),
    S("moving into", C("C35", ss=4, zoom="punch"), "ding"),
    S("And Mr. Krabs cannot", C("C36", zoom="in"), ("whoosh", -.15, .5)),
    S("spies on", C("C36", ss=2, zoom="punch"), "pop"),
    S("And he's right", C("C37", zoom="in"), ("shutter", 0, .5)),
    S("The real one", C("C37", ss=2, zoom="in")),
    S("But then Krabs", C("C37", ss=4, zoom="punch"), ("scratch", 0, .8)),
    S("Both of them", G("watch_loop"), "pop", ("pop", .3, .8), ("pop", .6, .8), ("pop", .9, .8)),
    S("At that point", G("phone"), "pop", ("pop", 1.0, .6), ("pop", 1.5, .6), ("pop", 2.0, .6)),
    S("And Plankton did", C("C38", zoom="in", tag="PLANKTON: THE MOVIE · 2025"), ("whoosh", -.15, .5)),
    S("Twenty-six years", C("C38", ss=1, zoom="in")),
    S("and the villain", C("C38", ss=3, zoom="punch"), ("thump", 0, .8)),
]

T["16"] = [
    S("So. Who's", G("verdict", title=""), ("riser", 0, .4)),
    S("Remember how", C("C39", zoom="in", tag=FOF)),
    S("actually make up", C("C39", ss=2, zoom="in"), ("ding", .2, .4)),
    S("And then Plankton", C("C39", ss=4, zoom="punch"), ("thump", 0, .8)),
    S("right back", C("C39", ss=6, zoom="in"), ("whoosh", -.1, .6)),
    S("They had the chance", C("C39", ss=7, freeze=True, fx="bw", zoom="in")),
    S("But only one", G("verdict", title=""), "thump"),
    S("And it's Krabs", G("verdict", lit=0, title=""), ("thump", 0, .8)),
    S("He's got the formula", C("C41", zoom="in")),
    S("the money", C("C40", zoom="punch"), ("cha_ching", 0, .5)),
    S("He could hand", G("rip_paper", rip_at=-1), ("rip", 0, .4)),
    S("Plankton was there", C("C18", ss=4, freeze=True, fx="sepia", zoom="in")),
    S("He never will", C("C40", zoom="in", fx="dark")),
    S("Because the day", C("C02", zoom="in")),
    S("no reason to come", C("C03", zoom="out")),
    S("Remember the balloon", G("balloon", text=""), ("squeak", .3, .3)),
    S("The first penny", G("coins", text="", n=1), ("coin", .2, .6)),
    S("he spent on Plankton", C("C16", ss=7, freeze=True, fx="sepia", zoom="in")),
    S("Every penny", G("coins", text=""), ("coin", 0, .5), ("coin", .4, .5), ("coin", .9, .5), ("coin", 1.3, .4)),
    S("he kept", C("C41", zoom="in", fx="dark"), ("thump", 0, .8)),
]

T["17"] = [
    S("Twenty-seven years", C("C23", ss=4, zoom="in")),
    S("Same door", C("C02", zoom="punch"), "thump"),
    S("Same crab", C("C40", zoom="punch"), "thump"),
    S("Still no formula", G("scoreboard", p="0", k="∞"), ("thump", 0, .4)),
    S("But in his defense", C("C01", ss=1, zoom="in", tag="PLANKTON! · 1999")),
    S("he did go", C("C01", ss=2, zoom="punch")),
    S("@+1.2", C("C01", ss=4, zoom="out"), "door_slam", ("slide_down", .15, .6)),
    S("@+2.6", G("end_black"), ),
]
