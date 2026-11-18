"""Write the YouTube description in the channel's format, with chapter times taken from the last render.
Run after tools/render.py:  python3 tools/description.py  -> 05_DESCRIPTION.md + output/description.txt"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

HOOK = """July 31, 1999: a guy the size of a sesame seed tells Mr. Krabs he went to college and gets thrown out of the Krusty Krab. He's been getting thrown out ever since.

The show's own origin story says Plankton and Krabs were best friends, and that the Krabby Patty was invented by both of them, by accident, during the fight that ended the friendship. I went back through Friend or Foe, Plankton's Regular, Enemy In-Law, One Coarse Meal and Plankton Retires to figure out who the actual bad guy is."""

EPISODES = """Episodes referenced:
Plankton! (S1, 1999) · The Algae's Always Greener (S3) · Born Again Krabs (S3) · Plankton's Regular · Enemy In-Law (S4) · F.U.N. · Imitation Krabs · Plankton's Pet · Friend or Foe (S5, 2007) · Single Cell Anniversary · One Coarse Meal (S7) · Plankton Retires (S10, 2017) · The SpongeBob SquarePants Movie (2004) · Plankton: The Movie (Netflix, 2025)"""

SOURCES = """Sources:
Friend or Foe (episode, reception incl. the DVD Talk Rashomon comparison): https://en.wikipedia.org/wiki/Friend_or_Foe_(SpongeBob_SquarePants)
Plankton & Karen (creation, Mr. Lawrence casting, "it's Doug", original microscopic design): https://en.wikipedia.org/wiki/Plankton_and_Karen
Plankton: The Movie (Netflix, March 7, 2025): https://en.wikipedia.org/wiki/Plankton:_The_Movie
Plankton Retires recap (written by Mr. Lawrence): https://tvtropes.org/pmwiki/pmwiki.php/Recap/SpongeBobSquarePantsS10E7PlanktonRetiresTridentTrouble
Born Again Krabs recap (the 62 cents): https://tvtropes.org/pmwiki/pmwiki.php/Recap/SpongeBobSquarePantsS3E15BornAgainKrabsIHadAnAccident

The verdict at the end (that Krabs keeps the war going because it's the only thing still connecting them) is my own read, not something the show or the writers have said. And yes, Enemy In-Law calls it a Krabs family recipe. I'm going with Friend or Foe."""

OUTRO = """Who do you think is actually the bad guy here, Krabs or Plankton?

SpongeBob SquarePants and all clips belong to Nickelodeon / Paramount. Used here for commentary and criticism under fair use.

#SpongeBob #Plankton #MrKrabs"""


def fmt(t):
    t = int(t); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main():
    ch = json.load(open(os.path.join(ROOT, "build", "chapters.json")))
    keep = []
    for t, name in sorted(ch):
        if keep and t - keep[-1][0] < 10: continue  # YouTube needs >= 10 s per chapter
        keep.append((t, name))
    keep[0] = (0, keep[0][1])
    chapters = "\n".join(f"{fmt(t)} {n}" for t, n in keep)
    text = "\n\n".join([HOOK, chapters, EPISODES, SOURCES, OUTRO]) + "\n"
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    open(os.path.join(ROOT, "output", "description.txt"), "w").write(text)
    md = ["# YouTube upload copy", "",
          "## Title (pick one; channel format: a curiosity statement, occasional CAPS word or trailing `..`)",
          "1. **Plankton Helped Make the Krabby Patty..** (recommended; pairs with thumbnail A or B)",
          "2. SpongeBob's MOST Toxic Friendship (mirrors your best performer, \"Spongebob's MOST Tragic Character\")",
          "3. Mr. Krabs Is Hiding Something About Plankton..", "",
          "## Description (paste as-is; chapter times come from the last render)", "", "```", text.rstrip(), "```", ""]
    open(os.path.join(ROOT, "05_DESCRIPTION.md"), "w").write("\n".join(md))
    print(chapters)


if __name__ == "__main__":
    main()
