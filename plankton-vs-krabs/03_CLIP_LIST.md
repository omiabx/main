# CLIP LIST: what I need from the show

I can't pull episodes from the internet for you, so the footage comes from your own copy. Each clip only needs to be **5–10 seconds**, starting just before the moment described. The renderer pans across it, freezes it and zooms it, and **mutes its audio** (show audio carries the score, and this video has no music).

**Two ways to hand them over:**
1. Put trimmed files in `clips/` named by ID: `clips/C01.mp4`, `clips/C07.mkv`, …
2. Or put whole episodes in `clips/` and list timestamps in `clips/clips.csv`:
```
id,file,start,end
C13,friend_or_foe.mp4,03:12,03:20
C16,friend_or_foe.mp4,05:40,05:48
```
Any clip you skip renders as a labelled placeholder card, so you can fill gaps in later.

*Fair use:* short clips with commentary and transformation are standard for this kind of channel, but the call is yours. Keep each clip short and keep the voiceover talking over it, which the edit already does.

| ID | Episode | Year | Moment | Used in chunks |
|---|---|---|---|---|
| **C01** | Plankton! | 1999 | Plankton's first scene in the Krusty Krab: yelling at Krabs ('I went to college!') and being thrown out the door | 01, 11, 17 |
| **C02** | any episode |  | Krusty Krab exterior wide shot, front door visible | 01, 13, 16, 17 |
| **C03** | any episode |  | Chum Bucket exterior wide shot (ideally with the Krusty Krab across the road) | 03, 16 |
| **C04** | The Algae's Always Greener | 2002 | Karen on her monitor talking to Plankton | 01, 11 |
| **C05** | Plankton's Pet |  | Plankton with Spot the amoeba | 01 |
| **C06** | Plankton's Regular |  | the regular customer happily eating chum at the Chum Bucket | 01, 12 |
| **C07** | Friend or Foe | 2007 | young Krabs and young Plankton together as kids | 02, 07 |
| **C08** | Friend or Foe | 2007 | opening: SpongeBob asks Mr. Krabs about Plankton | 05 |
| **C09** | Friend or Foe | 2007 | Krabs's version: kid Plankton as the evil one | 06 |
| **C10** | Friend or Foe | 2007 | Krabs's version: Krabs tossed into the garbage pile | 06 |
| **C11** | Friend or Foe | 2007 | Plankton's version: same scenes, roles swapped | 06 |
| **C12** | Friend or Foe | 2007 | Karen starts telling the real version | 05, 06, 07 |
| **C13** | Friend or Foe | 2007 | carnival: little Krabs finds the penny and buys Plankton the balloon | 07, 16 |
| **C14** | Friend or Foe | 2007 | Stinky's Burgers at the dump, owner refuses to serve them | 08 |
| **C15** | Friend or Foe | 2007 | Plabs Burgers stand at the dump, no customers | 02, 08 |
| **C16** | Friend or Foe | 2007 | Old Man Jenkins takes a bite and collapses | 08 |
| **C17** | Friend or Foe | 2007 | the two blame each other and rip the recipe in half | 02, 09 |
| **C18** | Friend or Foe | 2007 | shelf falls, ingredients spill into the mix; Krabs left with the new recipe | 02, 09, 16 |
| **C19** | Friend or Foe | 2007 | Plankton storms off; his Chum Burger fails; he vows revenge | 09 |
| **C20** | Plankton! | 1999 | Plankton inside SpongeBob's head controlling him | 03, 11 |
| **C21** | Imitation Krabs |  | Plankton's robot Mr. Krabs | 11 |
| **C22** | F.U.N. |  | SpongeBob and Plankton being friends | 11 |
| **C23** | montage |  | 4-6 quick moments of Plankton schemes failing / being flung out (any episodes) | 01, 02, 03, 05, 10, 11 |
| **C24** | The SpongeBob SquarePants Movie | 2004 | Plankton steals Neptune's crown / Krabs gets frozen | 11 |
| **C25** | The SpongeBob SquarePants Movie | 2004 | bucket helmets on everyone, Planktopolis | 04, 11 |
| **C26** | The SpongeBob SquarePants Movie | 2004 | SpongeBob's guitar rock moment, buckets blow off | 11 |
| **C27** | Single Cell Anniversary |  | Karen steals the formula herself; Plankton messes it up | 12 |
| **C28** | Plankton's Regular |  | the reveal that Karen pays the regular | 12, 13 |
| **C29** | Plankton's Regular |  | Mr. Krabs adds chum to the Krusty Krab menu | 13, 14 |
| **C30** | Enemy In-Law | 2005 | Plankton dating Mama Krabs; Mr. Krabs freaking out | 10, 13 |
| **C31** | One Coarse Meal |  | Mr. Krabs in the Pearl/whale disguise scaring Plankton | 02, 14 |
| **C32** | One Coarse Meal |  | SpongeBob telling Krabs he's gone too far | 14 |
| **C33** | Born Again Krabs | 2003 | Krabs trades SpongeBob to the Flying Dutchman for 62 cents | 07, 14 |
| **C34** | Born Again Krabs | 2003 | Squidward calls Krabs out | 14 |
| **C35** | Plankton Retires | 2017 | Plankton announces his retirement / retirement home | 15 |
| **C36** | Plankton Retires | 2017 | Krabs and SpongeBob spying from the ceiling fan | 15 |
| **C37** | Plankton Retires | 2017 | robot reveal: Plankton's robot, then Krabs's robots | 15 |
| **C38** | Plankton: The Movie (trailer) | 2025 | Karen as the villain / giant Karen | 15 |
| **C39** | Friend or Foe | 2007 | ending: they make up, Plankton snatches the formula, chase | 16 |
| **C40** | any episode |  | Mr. Krabs close-up (scowl / counting money) | 01, 02, 06, 12, 13, 14, 16, 17 |
| **C41** | any episode |  | the Krabby Patty secret formula bottle or safe | 09, 16 |
| **C43** | any episode |  | Plankton evil laugh | 02, 14 |
| **C44** | any episode |  | Pearl on screen | 14 |
| **C45** | Friend or Foe | 2007 | kids picking on young Krabs and Plankton | 07 |

### Thumbnail frames
- `thumb/krabs.png`: Mr. Krabs looking guilty or side-eyeing, as big and clean as possible (a background-removed PNG is best).
- `thumb/plankton.png`: Plankton angry or yelling.

