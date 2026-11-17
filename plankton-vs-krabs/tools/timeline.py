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

# chapter labels shown top-right on clip shots
CH = {
    "03": "CH.1 · THE SMALLEST VILLAIN", "05": "CH.2 · THREE LIARS", "11": "CH.3 · THE LOSING STREAK",
    "13": "CH.4 · OKAY, ABOUT KRABS", "15": "CH.5 · NEITHER WANTS IT TO END", "16": "THE VERDICT",
}

TAIL = {"02": .5, "04": .7, "10": .8, "12": .5, "14": .6, "15": .5, "16": 1.6, "17": 3.8}

T = {}

T["01"] = [
    S("On July", G("typewriter", lines=("JULY 31, 1999",), sub="")),
    S("a guy about", C("C01", zoom="in", tag="PLANKTON! · 1999"), ("whoosh_short", -.15, .6)),
    S("sesame seed", C("C01", ss=1, zoom="punch", text="≈ 1 SESAME SEED"), "pop"),
    S("screamed at", C("C01", ss=2, zoom="in"), ("impact", 0, .7)),
    S("got thrown out", C("C01", ss=4, zoom="out"), "door_slam", ("slide_down", .2, .5)),
    S("He has been", C("C23", zoom="in", fx="vhs"), ("rewind", -.1, .5)),
    S("Twenty-seven years", G("counter", a=1999, b=2026, label="YEARS OF GETTING THROWN OUT"), ("tick", 0, .4, 10, .12)),
    S("Same door", C("C02", zoom="punch"), "thump"),
    S("Same crab", C("C40", zoom="punch"), "thump"),
    S("He's married", C("C04", zoom="in", text="MARRIED TO A COMPUTER"), ("glitch", 0, .4)),
    S("pet amoeba", C("C05", zoom="in"), "bloop"),
    S("He owns a restaurant", G("map_street"), ("whoosh", -.15, .6)),
    S("his one regular", C("C06", zoom="in")),
    S("secretly being paid", C("C06", ss=2, freeze=True, stamp="PAID ACTOR"), ("stamp", .1, .8)),
]

T["02"] = [
    S("And the crab", C("C40", zoom="in"), ("whoosh_short", -.12, .5)),
    S("best friend", C("C07", freeze=True, fx="sepia", zoom="punch", tag=FOF), ("scratch", -.05, .8)),
    S("They grew up", C("C07", ss=2, fx="sepia", zoom="in")),
    S("invented the Krabby", C("C18", zoom="punch", fx="sepia", text="TOGETHER?"), ("impact", 0, .6)),
    S("We'll get to that", C("C17", fx="vhs", zoom="in"), ("glitch", 0, .4)),
    S("I went back", G("watchlist"), ("type_burst", 0, .4)),
    S("dresses up", C("C31", freeze=True, zoom="punch", text="HIS OWN DAUGHTER"), ("scratch", 0, .8)),
    S("psychologically", C("C31", ss=2, zoom="punch"), ("impact", 0, .6)),
    S("I realized", G("big_text", text="I WAS WATCHING IT WRONG", color=WHITE), ("glitch", 0, .5)),
    S("This rivalry", G("heartbreak"), ("rip", .55, .8)),
    S("Two guys", C("C17", fx="sepia", zoom="in")),
    S("garbage dump", C("C15", fx="sepia", zoom="punch"), "thump"),
    S("spent the rest", C("C23", ss=2, zoom="in")),
    S("And one of them", G("verdict"), ("boom", 0, .7)),
    S("evil laugh", C("C43", zoom="punch"), ("scratch", .5, .7)),
]

T["03"] = [
    S("Quick refresher", G("title_card", num="CHAPTER 1", title="THE SMALLEST VILLAIN ON TELEVISION", accent=PLANK), ("boom", 0, .8)),
    S("Sheldon J", C("C20", zoom="in", text="SHELDON J. PLANKTON", textpos="lower"), "shutter"),
    S("Owner of", C("C03", zoom="in"), ("whoosh_short", -.12, .6)),
    S("directly across", G("map_street", note="SAME STREET. ON PURPOSE."), "pop"),
    S("bold business", C("C03", freeze=True, zoom="punch", text="BOLD."), "thump"),
    S("That's opening", G("vs_card"), "pop", ("pop", .45, .8)),
    S("Fun fact", G("big_text", text="FUN FACT", bg="yellow"), "ding"),
    S("so small", G("magnify"), ("bloop", .5, .7), ("scribble", 1.4, .5)),
    S("The animators", C("C20", ss=2, zoom="in")),
    S("only supposed", G("strike"), ("scribble", .5, .6), ("stamp", .9, .7)),
    S("Nickelodeon wanted", G("chat", step=1.6), "pop", ("pop", 1.6, .9)),
    S("Doug Lawrence", G("nameplate"), "shutter"),
    S("every single one", C("C23", zoom="in"), ("slide_down", .2, .5)),
]

T["04"] = [
    S("And the plan", G("checklist", reveal=(9, 9, 9, 9)), ("whoosh", -.15, .5)),
    S("Steal the secret", G("checklist", reveal=(0, 9, 9, 9)), "type"),
    S("Make Krabby", G("checklist", reveal=(-1, 0, 9, 9)), "type"),
    S("Put Mr", G("checklist", reveal=(-1, -1, 0, 9)), "type"),
    S("rule the world", G("checklist", reveal=(-1, -1, -1, 0)), "type"),
    S("It never works", G("checklist", reveal=(-1, -1, -1, -1), stamp_at=0.05), ("stamp", 0, .9), ("buzzer", .1, .5)),
    S("Except one", C("C25", fx="vhs", zoom="in"), ("glitch", 0, .6)),
    S("that time went", G("scoreboard", p="1*", k="∞", note="*see chapter 3"), ("tick", 0, .4)),
]

T["05"] = [
    S("So how do", C("C23", ss=3, zoom="in"), ("whoosh", -.15, .6)),
    S("The show actually", G("title_card", num="CHAPTER 2", title="THREE LIARS AND A COMPUTER", accent=YELLOW), ("boom", 0, .8)),
    S("Season five", C("C08", zoom="in", tag="S5 · " + FOF), "shutter"),
    S("SpongeBob asks", C("C08", ss=2, zoom="in")),
    S("the same story", G("three_versions"), "pop", ("pop", .12, .8), ("pop", .24, .8)),
    S("A DVD reviewer", G("typewriter", lines=("\"...it resembles", "Rashomon.\""), size=100, sub="paraphrasing a DVD Talk review, 2007", cps=22), ("type_burst", 0, .5)),
    S("The Kurosawa", G("big_text", text="RASHOMON (1950)", sub="a Kurosawa classic", color=WHITE), "shutter"),
    S("About a SpongeBob", C("C08", ss=4, zoom="punch"), "pop"),
    S("nobody in this story", C("C12", zoom="in"), ("glitch", .4, .4)),
]

T["06"] = [
    S("Version one", G("three_versions", active=0), ("stamp", 0, .6)),
    S("In Krabs's version", C("C09", fx="sepia", zoom="in", label=("VERSION 1 · KRABS", KRABS))),
    S("Krabs tries", C("C10", fx="sepia", zoom="in", label=("VERSION 1 · KRABS", KRABS)), ("impact", .6, .5)),
    S("Very noble", C("C09", freeze=True, fx="sepia", zoom="punch", text="VERY NOBLE."), "ding"),
    S("Weird how", C("C40", zoom="in")),
    S("Version two", G("three_versions", active=1, unreliable=(0,)), ("rewind", -.2, .5), ("stamp", .3, .7)),
    S("It's the same", C("C11", fx="sepia", zoom="in", label=("VERSION 2 · PLANKTON", PLANK))),
    S("except now", C("C11", ss=3, fx="sepia", zoom="punch", label=("VERSION 2 · PLANKTON", PLANK)), ("scratch", 0, .7)),
    S("He just swapped", G("chat", msgs=(("FIND", "Plankton"), ("REPLACE WITH", "Krabs")), note="[ REPLACE ALL ]", step=.6), ("type_burst", 0, .4), ("pop", .7, .7)),
    S("And then there's", G("three_versions", active=2, unreliable=(0, 1)), ("stamp", .35, .7)),
    S("Karen. The only", C("C12", zoom="in", label=("VERSION 3 · KAREN", KAREN))),
    S("can't stand", C("C12", ss=3, zoom="punch", label=("VERSION 3 · KAREN", KAREN)), "thump"),
]

T["07"] = [
    S("So, according", C("C12", ss=1, zoom="in", label=("VERSION 3 · KAREN", KAREN)), ("glitch", 0, .4)),
    S("best friends", C("C07", fx="sepia", zoom="in", tag=FOF)),
    S("both outcasts", C("C07", ss=3, fx="sepia", zoom="in")),
    S("the other kids", C("C45", fx="sepia", zoom="in")),
    S("There's a moment", C("C13", fx="sepia", zoom="in"), ("bubbles", 0, .4)),
    S("finds a penny", C("C13", ss=1.5, freeze=True, fx="sepia", zoom="punch", text="1¢"), "coin"),
    S("the same man", C("C33", fx="vhs", zoom="in", text="62¢", tag="BORN AGAIN KRABS · 2003"), ("rewind", -.1, .5)),
    S("spends it", C("C13", ss=3, fx="sepia", zoom="in"), ("squeak", .1, .4)),
    S("For Plankton", C("C13", ss=4, freeze=True, fx="sepia", zoom="punch")),
    S("Remember the balloon", G("balloon", text=""), "thump"),
]

T["08"] = [
    S("So the two", C("C14", fx="sepia", zoom="in"), ("whoosh_short", -.12, .5)),
    S("And the owner", C("C14", ss=3, fx="sepia", zoom="in", stamp="BAD FOR BUSINESS"), ("stamp", .4, .8)),
    S("Then the health", C("C14", ss=6, fx="sepia", zoom="punch", stamp="CLOSED"), ("stamp", .3, .8)),
    S("and the boys", C("C15", fx="sepia", zoom="in")),
    S("At the dump", C("C15", ss=2, fx="sepia", zoom="punch"), "thump"),
    S("They call it", G("equation", times=(.6, 1.4, 1.7, 2.3, 2.5)), ("pop", .6, .8), ("pop", 1.7, .8), ("ding", 2.5, .7)),
    S("Nobody comes", C("C15", ss=4, fx="sepia", zoom="in"), ("tick", 0, .25, 4, .5)),
    S("an old man", C("C16", fx="sepia", zoom="in")),
    S("takes one bite", C("C16", ss=2, fx="sepia", zoom="punch")),
    S("and collapses", C("C16", ss=4, fx="sepia", zoom="punch"), ("boom", 0, .8)),
    S("The burger poisoned", C("C16", ss=5, freeze=True, fx="bw", zoom="in", text="POISONED."), ("ring", .1, .3)),
]

T["09"] = [
    S("And instead", C("C17", fx="sepia", zoom="in")),
    S("It's your recipe", C("C17", ss=2, fx="sepia", zoom="punch"), ("whoosh_short", -.1, .6)),
    S("No, it's your", C("C17", ss=3, fx="sepia", zoom="punch"), ("whoosh_short", -.1, .6)),
    S("They grab", G("rip_paper", rip_at=1.0, halves=(("KRABS", KRABS), ("PLANKTON", PLANK))), ("rip", .9, .9)),
    S("During the fight", C("C18", fx="sepia", zoom="in"), ("boom", .3, .7)),
    S("Ingredients go", C("C18", ss=2, fx="sepia", zoom="punch"), ("bubbles", 0, .5)),
    S("And that accident", C("C18", ss=3, fx="sepia", zoom="in")),
    S("is the Krabby", C("C18", ss=4, freeze=True, fx="sepia", zoom="punch", text="THE KRABBY PATTY"), ("impact", 0, .7), ("ding", .05, .5)),
    S("Krabs is the one", C("C18", ss=5, fx="sepia", zoom="in"), "thump"),
    S("So Krabs keeps", C("C41", zoom="in"), "cha_ching"),
    S("Plankton storms", C("C19", fx="sepia", zoom="in")),
    S("Chum Burger", C("C19", ss=2, fx="sepia", zoom="punch", text="CHUM BURGER"), ("buzzer", .2, .4)),
    S("And that's the day", C("C19", ss=4, fx="sepia", zoom="in"), ("boom", .4, .6)),
]

T["10"] = [
    S("Now, to be fair", C("C30", zoom="in", tag="ENEMY IN-LAW · 2005"), ("glitch", 0, .4)),
    S("Another episode", G("error_card", stamp_at=9), ("buzzer", 0, .3)),
    S("I'm choosing", G("error_card", stamp_at=0.1), ("stamp", .1, .9)),
    S("So let's say", G("evidence", n=0), ("whoosh", -.15, .5)),
    S("invented by two", G("evidence", n=1), ("type_burst", 0, .4)),
    S("By accident", G("evidence", n=2), ("type_burst", 0, .4)),
    S("While they were", G("evidence", n=3), ("type_burst", 0, .4)),
    S("And one of them", G("evidence", n=4), ("type_burst", 0, .4), ("stamp", .7, .8)),
    S("Which means", C("C23", ss=1, zoom="in")),
    S("something he was", G("big_text", text="HE WAS IN THE ROOM.", color=WHITE), ("boom", 0, .9), ("ring", .3, .25)),
]

T["11"] = [
    S("So. How's", G("title_card", num="CHAPTER 3", title="THE LOSING STREAK", accent=KRABS), ("boom", 0, .8)),
    S("Badly", G("scoreboard", p="0", k="∞"), ("buzzer", 0, .5)),
    S("In his very first", C("C20", zoom="in", tag="PLANKTON! · 1999"), ("whoosh_short", -.12, .5)),
    S("He's built", C("C21", zoom="in", tag="IMITATION KRABS"), ("glitch", 0, .4)),
    S("He's tried being", C("C22", zoom="in", tag="F.U.N."), "pop"),
    S("He's tried disguises", C("C23", zoom="punch"), ("whoosh_short", -.1, .5)),
    S("flat-out lies", C("C23", ss=2, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("more lasers", C("C23", ss=4, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("flying out", C("C01", ss=4, zoom="in"), ("slide_down", 0, .7)),
    S("The one time", C("C24", zoom="in", tag="THE SPONGEBOB SQUAREPANTS MOVIE · 2004"), ("riser", 0, .5)),
    S("Plan Z", G("big_text", text="PLAN Z", color=PLANK), ("impact", 0, .8)),
    S("Which, of course", C("C04", zoom="punch", text="(KAREN'S)"), "pop"),
    S("Plankton steals", C("C24", ss=2, zoom="in")),
    S("frames Mr", C("C24", ss=4, zoom="punch"), "thump"),
    S("sticks a bucket", C("C25", zoom="in"), "pop"),
    S("Planktopolis", C("C25", ss=3, zoom="punch", text="PLANKTOPOLIS"), "ding"),
    S("He finally wins", G("scoreboard", p="1", k="∞"), ("cha_ching", 0, .7)),
    S("And it lasts", C("C26", zoom="in")),
    S("with a guitar", C("C26", ss=2, zoom="punch"), ("scratch", 0, .8), ("impact", .05, .6)),
]

T["12"] = [
    S("And when he gets", G("scoreboard", p="0", k="∞", note="win revoked"), ("buzzer", 0, .5)),
    S("In Single Cell", C("C27", zoom="in", tag="SINGLE CELL ANNIVERSARY"), ("whoosh_short", -.12, .5)),
    S("Karen just goes", C("C27", ss=2, zoom="in")),
    S("And Plankton is the one", C("C27", ss=4, zoom="punch"), ("buzzer", .3, .4)),
    S("Then there's Plankton's", C("C06", zoom="in", tag="PLANKTON'S REGULAR"), ("whoosh_short", -.12, .5)),
    S("One guy", C("C06", ss=1, freeze=True, zoom="punch", text="1 CUSTOMER"), "ding"),
    S("Comes in every", C("C06", ss=2, zoom="in")),
    S("Turns out", C("C28", zoom="punch", stamp="PAID"), ("cha_ching", 0, .7)),
    S("Which is bleak", C("C28", ss=2, freeze=True, fx="bw", zoom="in"), "thump"),
    S("Now watch", C("C40", zoom="in"), ("riser", .2, .5)),
]

T["13"] = [
    S("He puts chum", C("C29", zoom="in"), ("scratch", 0, .8)),
    S("To steal the one", C("C29", ss=2, zoom="punch", text="TO STEAL THE ONE GUY"), ("impact", 0, .6)),
    S("He runs the most", C("C02", zoom="in")),
    S("he cannot let", C("C40", zoom="in")),
    S("Not even a fake", C("C28", ss=2, freeze=True, zoom="punch", stamp="PAID ACTOR"), ("stamp", .1, .8)),
    S("And once you see", G("title_card", num="CHAPTER 4", title="OKAY, ABOUT KRABS", accent=KRABS), ("boom", 0, .8)),
    S("In Enemy In-Law", C("C30", zoom="in", tag="ENEMY IN-LAW · 2005")),
    S("dating Mr", C("C30", ss=2, zoom="punch", text="HIS MOM."), ("scratch", 0, .7)),
    S("Krabs loses", C("C30", ss=4, zoom="punch"), ("impact", 0, .6)),
    S("which, fair", C("C30", ss=5, freeze=True, zoom="in")),
    S("But his first", C("C40", zoom="in")),
    S("But it never", G("pie"), ("pop", .2, .6), ("pop", 1.3, .8)),
]

T["14"] = [
    S("Then there's One", C("C31", zoom="in", tag="ONE COARSE MEAL"), ("whoosh_short", -.12, .5)),
    S("Krabs finds out", C("C31", ss=1, zoom="in")),
    S("Pearl, is a whale", C("C44", zoom="punch"), "bloop"),
    S("So Krabs starts", C("C31", ss=3, zoom="punch"), ("scratch", 0, .6)),
    S("Over and over", C("C31", ss=5, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("Popping up", C("C31", ss=6, zoom="punch"), ("whoosh_short", -.1, .5)),
    S("And it stops", C("C31", ss=7, fx="bw", zoom="in"), "thump"),
    S("genuinely dark", C("C31", ss=8, fx="dark", zoom="in")),
    S("Dark enough", C("C32", zoom="in")),
    S("gone too far", C("C32", ss=2, zoom="punch"), ("impact", 0, .6)),
    S("This is also", C("C33", zoom="in", tag="BORN AGAIN KRABS · 2003")),
    S("sixty-two cents", G("exchange"), "coin", ("coin", .8, .8)),
    S("when Squidward", C("C34", zoom="in")),
    S("whether he could've", C("C34", ss=2, freeze=True, zoom="punch"), ("scratch", .3, .7)),
    S("So yeah", C("C43", zoom="in")),
    S("He's got the laugh", C("C43", ss=1, zoom="punch"), "thump"),
    S("But if you just", C("C29", ss=1, zoom="punch"), "shutter"),
    S("episode after", C("C31", ss=4, zoom="punch"), "shutter"),
    S("the crab has", C("C40", zoom="in", fx="dark"), ("boom", 0, .7)),
]

T["15"] = [
    S("And here's the", G("title_card", num="CHAPTER 5", title="NEITHER OF THEM WANTS IT TO END", accent=KAREN), ("boom", 0, .8)),
    S("Plankton Retires", C("C35", zoom="in", tag="PLANKTON RETIRES · 2017")),
    S("Written, by the way", G("nameplate", name="WRITTEN BY: MR. LAWRENCE", role="the voice of Plankton himself"), "shutter"),
    S("Plankton announces", C("C35", ss=2, zoom="in")),
    S("moving into", C("C35", ss=4, zoom="punch"), "ding"),
    S("And Mr. Krabs cannot", C("C36", zoom="in"), ("whoosh", -.15, .5)),
    S("spies on", C("C36", ss=2, zoom="punch", text="FROM A CEILING FAN"), "pop"),
    S("And he's right", C("C37", zoom="in"), ("glitch", 0, .5)),
    S("The real one", C("C37", ss=2, zoom="in")),
    S("But then Krabs", C("C37", ss=4, zoom="punch"), ("scratch", 0, .8)),
    S("Both of them", G("watch_loop"), "pop", ("pop", .3, .8), ("pop", .6, .8), ("pop", .9, .8)),
    S("At that point", G("phone"), "pop", ("pop", 1.0, .6), ("pop", 1.5, .6), ("pop", 2.0, .6)),
    S("And Plankton did", C("C38", zoom="in", tag="PLANKTON: THE MOVIE · 2025"), ("whoosh", -.15, .5)),
    S("Twenty-six years", G("counter", a=0, b=26, label="YEARS OF LOSING TO A CRAB", roll=1.0, color=PLANK), ("tick", 0, .35, 8, .12)),
    S("and the villain", C("C38", ss=3, zoom="punch", text="HIS WIFE."), ("boom", 0, .8)),
]

T["16"] = [
    S("So. Who's", G("verdict"), ("riser", 0, .5)),
    S("Remember how", C("C39", zoom="in", tag=FOF)),
    S("actually make up", C("C39", ss=2, zoom="in"), ("ding", .2, .4)),
    S("And then Plankton", C("C39", ss=4, zoom="punch"), ("scratch", 0, .8)),
    S("right back", C("C39", ss=6, zoom="in"), ("whoosh", -.1, .6)),
    S("They had the chance", C("C39", ss=7, freeze=True, fx="bw", zoom="in")),
    S("But only one", G("verdict"), "thump"),
    S("And it's Krabs", G("verdict", lit=0), ("boom", 0, .9)),
    S("He's got the formula", C("C41", zoom="in")),
    S("the money", C("C40", zoom="punch"), ("cha_ching", 0, .5)),
    S("He could hand", G("rip_paper", rip_at=-1, halves=(("KRABS'S HALF", KRABS), ("PLANKTON'S HALF", PLANK))), ("rip", 0, .4)),
    S("Plankton was there", C("C18", ss=4, freeze=True, fx="sepia", zoom="in")),
    S("He never will", C("C40", zoom="in", fx="dark")),
    S("Because the day", C("C02", zoom="in")),
    S("no reason to come", C("C03", zoom="out")),
    S("Remember the balloon", G("balloon", text=""), ("squeak", .3, .3)),
    S("The first penny", C("C13", ss=2, fx="sepia", zoom="in")),
    S("he spent on Plankton", C("C13", ss=4, freeze=True, fx="sepia", zoom="in")),
    S("Every penny", G("coins", text="every penny after that..."), ("coin", 0, .5), ("coin", .4, .5), ("coin", .9, .5), ("coin", 1.3, .4)),
    S("he kept", G("big_text", text="HE KEPT.", color=WHITE), ("thump", 0, .8)),
]

T["17"] = [
    S("Twenty-seven years", G("typewriter", lines=("27 YEARS.",), bg="ink", cps=18), ("type_burst", 0, .4)),
    S("Same door", C("C02", zoom="punch"), "thump"),
    S("Same crab", C("C40", zoom="punch"), "thump"),
    S("Still no formula", G("scoreboard", p="0", k="∞"), ("buzzer", 0, .4)),
    S("But in his defense", C("C01", ss=1, zoom="in", tag="PLANKTON! · 1999")),
    S("he did go", C("C01", ss=2, zoom="punch", text="HE WENT TO COLLEGE.")),
    S("@+1.2", C("C01", ss=4, zoom="out"), "door_slam", ("slide_down", .15, .6)),
    S("@+2.6", G("end_black"), ),
]
