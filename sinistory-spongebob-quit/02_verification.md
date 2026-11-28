# Stage 2 verification log

Method: each episode was pulled from an Internet Archive DVD or Blu-ray rip and transcribed with Whisper (word timestamps). Every quoted line was fuzzy-matched against that audio. "Heard" means the line is in the actual episode audio; the timestamp is the clip in-point in the segment file. Who is speaking, the context and the objects on screen were then checked on frames taken at those timestamps (sheets in `verification/`).

## Footage sources

| Key | Episode | Source (Internet Archive) | Clean? |
|---|---|---|---|
| chum | Welcome to the Chum Bucket (S2, Jan 21 2002) | first-and-second-seasons-dvd-rip, S2 Disc 2 ch 11 | yes |
| strike | Squid on Strike (S2, Oct 12 2001) | same item, S2 Disc 3 ch 9 | yes |
| training | Krusty Krab Training Video (S3, May 10 2002) | sb-s-3-d-1, S3 Disc 2 ch 3 | yes |
| bornagain | Born Again Krabs (S3, Oct 4 2003) | sb-s-3-d-1, S3 Disc 2 ch 12 | yes |
| bummer | Bummer Vacation (S4, Oct 13 2006) | sb-s-3-d-1, S4 Disc 3 ch 6 | yes |
| fired | SpongeBob, You're Fired (S9, Nov 11 2013) | sb-s-10-d-1, S9 Disc 2 ch 6 | yes |
| movie | The SpongeBob SquarePants Movie (Nov 19 2004) | the-spongebob-squarepants-movie_202506 (1080p Blu-ray; subtitles are a separate track) | yes |
| helpwanted | Help Wanted (S1, May 1 1999) | First 100 Episodes disc 01 | **burned-in captions, cropped out** (top 72%, 16:9). Crop test in `verification/helpwanted_caption_crop_test.jpg` |
| naturepants | Nature Pants (S1, Sept 11 1999) | First 100 Episodes disc 02 | **burned-in captions, cropped out** (same crop) |
| rail1946 | "Rail Strike Paralyzes Entire U.S." (May 23 1946) | Universal Newsreels, public domain (CC PD mark) | yes |

Help Wanted isn't on the original Season 1 DVD rip, and every Nature Pants and Help Wanted copy I could find has burned-in captions, so those two are crops. The other clean-looking copies were either broken (`spongebob-pilot`) or duplicates of rips I already had.

## Quotes (all heard in the episode audio)

| Line in script | Speaker | Source @ seconds | Match |
|---|---|---|---|
| "I bet your contract, and I lost." | Krabs, to SpongeBob outside the KK | chum 87.28 | exact |
| "Every Thursday night for fifteen years" / "I never lose!" | Krabs | chum 41.90 / 46.40 | exact |
| Plankton threw the games ("For fifteen years, I've been throwin' those card games") | Plankton | chum 165.60 | exact |
| "Tell you what, half-pint, why don't you ask me later?" | SpongeBob | chum 536.70 | exact |
| "I rubbed your putrid feet!" (the foot rub is never shown, only stated) | Plankton | chum 534.92 | exact |
| "How 'bout you give me fifty bucks…" | Krabs | chum 629.66 | exact |
| "I'm workin' all day for free! My treat!" / "That's what I thought you said." | SpongeBob / Krabs | chum 663.16 | exact |
| "This kitchen's not the same without you" (duet) | SpongeBob & Krabs | chum 296.90 | exact |
| "For years I've been dreaming of this moment." | SpongeBob | helpwanted 151.48 | exact |
| "Whose first words were 'May I take your order?'" / "Mine were." | Patrick / SpongeBob | helpwanted 173.82 | exact (caption confirms "Mine were.") |
| "I can't accept your money, Mr. Krabs." … "Grilling is my passion." | SpongeBob | strike 76.64 | exact |
| "…this should cover all my nonsense… extra fifty cents for when I was tying my shoe." | SpongeBob | strike 98.04 | exact |
| "That's more than I make in a year!" / "Don't be askin' me for a raise." | SpongeBob / Krabs | bummer 636.40 | exact |
| "Can I have a raise?" / "No." / "Good job, Mr. SquarePants!" | SpongeBob / Krabs / Narrator | training 417.46 | exact |
| "How much money are we talking about?" / "62 cents." / "I'll take the money." | Krabs / Dutchman / Krabs | bornagain 584.54 | exact |
| "You think I could've gotten more?" | Krabs, to Squidward | bornagain 613.02 | exact |
| Krabs cries ("I want SpongeBob back!"), Dutchman returns him | Krabs | bornagain 632.28 | exact + frames |
| "Fourth time this week I've had to scrape you off of something" | Krabs | naturepants 142.52 | exact |
| "giving up my cold industrial life…among the jellyfish" | SpongeBob | naturepants 149.96 | exact |
| "Oh, he'll be back, alright. He'll be back." | Krabs | naturepants 202.56 | exact |
| "And I'll see you at work, first thing tomorrow morning." | Krabs | naturepants 669.78 | exact |
| Fry Cooks Union letter, fine for unused vacation | Krabs | bummer 25.28–37.86 | exact |
| "What's a vacation?" / "a vacation is when you don't come into work." | SpongeBob / Krabs | bummer 96.00 | exact |
| "unpaid intern as your temporary replacement" | Krabs | bummer 115.40 | exact |
| "I told him to stay home and watch television." | SpongeBob (in Patrick suit) | bummer 604.34 | exact |
| "I love the putrid grease of the Krusty Krab so much…" | SpongeBob | bummer 614.92 | exact |
| "I'll save a whole nickel if I cut your salary. Completely." | Krabs | fired 158.44 | exact |
| "You can't argue with a nickel." | Krabs | fired 180.76 | exact |
| "Unemployment may be fun for you, but I need to get a job." | SpongeBob, to Patrick | fired 689.16 | exact |
| "Fired five times in one day" (Krabs + 4 restaurants) | SpongeBob | fired 959.44 | exact |
| "I'm pretty sure this is illegal." | SpongeBob, chained at Weenie Hut | fired 1077.34 | exact |
| "Now my life has purpose again!" | SpongeBob | fired 1247.58 | exact |
| Pay toilet for the lost nickel | Krabs | fired 1295.46 + frame | exact |
| "You're just a kid. And to be a manager, you have to be a man." | Krabs | movie 507.92 | exact |
| Wakes at Goofy Goober's: "It's eight in the morning" / "I'm late for work." | Waiter / SpongeBob | movie 891.48 / 904.96 | exact |
| "he's a great big jerk!" | SpongeBob | movie2 151.32 | exact |
| "Would you spare Mr. Krabs' life if I went to get your crown back?" (same scene, ~95 s later) | SpongeBob | movie2 248.90 | exact |
| "No one who's gone to Shell City has ever returned." | King Neptune | movie2 262.22 | exact |
| "We've got to unite as workers…" | Squidward | strike 120.42 | exact |
| "I still don't know what strike means." | SpongeBob | strike 150.40 | exact |
| "You didn't tell me I was gonna get fired!…" | SpongeBob, at glass door | strike 176.96 | exact |
| Krabs begs at Squidward's door: "I'm ruined without you and the little yellow guy." | Krabs | strike 549.22 | exact |
| Deal reached: "I'm glad you saw it our way" / "get me two golden boys back" | Squidward / Krabs | strike 629.74 / 633.34 | exact |
| "I will restore the working man…" / "saw the tables of tyranny in half…" | SpongeBob | strike 604.68 / 613.44 | exact |
| "you two are gonna work for me forever!" | Krabs | strike 681.72 | exact |
| "Yahoo! The strike worked… Forever!" | SpongeBob | strike 690.72 | exact |
| "One eternity later…" | French Narrator | strike 700.52 | exact |
| "The wheels of the country's railroads grind slowly to a halt, as 250,000 trainmen and engineers walk off the job." | Newsreel narrator | rail1946 54.04 | exact |

## Visual and object claims (see `verification/visual_claims_closeups.jpg`)

| Claim | Result |
|---|---|
| Training Video title card is over an electric chair | ✔ wooden chair with arm and leg straps and buckles, cord into a wall outlet, knife switch, barred window |
| Squidward's bill: breathing a dollar, existing two | ✔ (it's **Squidward's** bill; SpongeBob pays his own) |
| SpongeBob's "extra fifty cents" | ✔ two 25¢ coins in his hand |
| Skeleton ending | ✔ skeleton Squidward with a broom; skeleton SpongeBob in the register boat |
| Plankton pays Krabs | ✔ green banknotes handed up to Krabs |
| SpongeBob returns bandaged | ✔ bandage on head beside Krabs at the register |
| Bummer Vacation coin | ⚠ a single silver coin; its value isn't shown. The wiki calls it a dime, so **the script now says "one coin"** |
| Dutchman's 62 cents | ✔ handful of coins marked ¢ |
| Chained to the grill | ✔ chain from the grill to his wrist |
| Hat on the ground, then put back on | ✔ both |
| Krabs at Squidward's door in a nightgown | ✔ |
| Pampering montage: replica kitchen, fancy shoes, bubble bath + ice cream cone, toy seahorse, bedtime story | ✔ all on screen. I removed "vibrating" from the shoes (wiki wording, not visible) |
| SpongeBob's face against the glass door | ✔ |
| Hammer and saw | ✔ |
| Patrick costume | ✔ |

There are **no "same character" or "reused background" claims** in the script, so no side-by-side identity comparisons were needed.

## Claims checked and changed or cut
- **"He never quits"**: false. In *Nature Pants* he quits. The script now says "I could only find one time he walks out on his own." I searched all 668 episode transcripts on the wiki for SpongeBob quitting or resigning, and for stage directions of him taking off his hat. The only voluntary exit is *Nature Pants*.
- **"Tie Patrick up"** (Bummer Vacation): not in the episode as written. Replaced with the verified line about telling Patrick to stay home and watch TV.
- **"He lasts one night"** (Nature Pants): the timeline isn't stated, so the script describes only what's on screen (nightfall, cave, walks home).
- **"No work?! What'll I do all day?"**: the audio was unclear on the rip, so it isn't used.
- **"Dime"**: changed to "coin" (see above).
- **"His ninth episode"**: it depends on how you count, so it now says "back in the first season."
- **Study wording**: "seven studies" became "a series of studies," because the abstract says seven but numbers them up to Study 8.

## Outside sources
- Kim, Campbell, Shepherd & Kay (2020), *J. Personality & Social Psychology* 118(1):121–148, doi:10.1037/pspi0000190. Claims used: unpaid extra hours and demeaning off-role tasks are judged more legitimate for "passionate" workers; two mechanisms ("would have volunteered," "work is its own reward"); the reverse direction (exploited workers are assumed to be passionate, Study 7). All from the abstract.
- 2013 controversy: Media Matters (Oct 31 2013) and Mother Jones (Nov 5 2013) quote the NY Post's Oct 30 piece ("mooching off the social services of Bikini Bottom") and Fox & Friends' Heather Nauert. Mother Jones covers Al Sharpton's MSNBC reply. The U.S. premiere was Nov 11 2013, after the Post piece.
- 1946 rail strike: newsreel narration (above). Wikipedia's "United States strike wave of 1945–1946" also gives 250,000 railroad engineers and trainmen.
- "Debt bondage": the 1956 UN Supplementary Convention on the Abolition of Slavery (Art. 1a) defines it as labor pledged for a debt where "the length and nature of those services are not respectively limited and defined." "Work for me forever" to pay off damages fits that definition.
