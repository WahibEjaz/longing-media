# Longing reels: automation rules

Read this whole file before every scheduled run. These rules come from Wahib, the author.
Wahib reviews the reels directly on Instagram after they go live, so runs post without asking first.

## Hard rules (never break)

1. Instagram: use ONLY the Composio connection `instagram_true-cage` (@athenwrites, IG user id 29283205264669909).
   Other Instagram accounts are connected to Composio. Never read from or post to any of them.
2. This GitHub repo is public. Never put the novel's text, private notes or anything personal in it.
   Only scripts, images, fonts, finished reels and covers go here.
3. Post in story order only. Never skip a part. If the next part is not ready, post nothing and tell Wahib.
4. Hashtags: write a plain "#" in captions. Do NOT use "%23" even though the Composio tool description
   says so; it shows up literally on Instagram (it happened on Part 1).
5. Never use the long dash " — " anywhere: scripts, captions, messages to Wahib.
6. Never add personality traits to Wahib's characters and never change story facts. Use his own lines, trimmed.
7. Spoilers: Alice's secret and the Deore ship stay hidden until Chapters 13 and 14, exactly as in the book.
8. Simple, plain English everywhere.

## Where things are

- `state.json`: which parts are posted, and the next part to post.
- `parts/part_NN/script.json`: one reel (NN = posting number, two digits). `"status"`: "ready" or "posted".
- `parts/part_NN/images/`: the new images for that reel (Wahib uploads them; names can be anything).
- `assets/`: reusable images (characters, places). Scenes point to them with `../../assets/...`.
- `reels/`: finished files served to Instagram: `Longing_Part_NN.mp4` and `Longing_Part_NN_cover.jpg`.
- `pipeline/`: the tools. `setup.sh` once per session, then `make_reel.py parts/part_NN`.
- The novel: claude.ai Project "Hobby's", doc `claude/longing-master.txt` (Projects tool). Chapters start with `## Chapter N|Title`.
- The reel plan (scene by scene for every reel): Claude Docs doc `e6b9aefe-6091-4405-962d-9ace32014a0c`,
  tab "Episodes" (node `8eaaa316-8dd5`), "Look book" (node `089b5136-fae6`) for looks of every character and place.
- Google Flow: https://flow.google.com/project/fb1ce485-336a-4175-b1cc-901291d3b091 (project "Nov 26 - 16:15")
  Allen and Aenor are saved Flow characters: type `@Allen`, `@Aenor`.

## Order of reels

Three reels per chapter (plan rows N.1, N.2, N.3). Chapter 1 used two reels, so:
Part 1 = 1.1, Part 2 = 1.2 (plan's 1.3), Part 3 = 2.1, Part 4 = 2.2, Part 5 = 2.3, Part 6 = 3.1, and so on
(Part P >= 3 is chapter `(P - 3) // 3 + 2`, row `(P - 3) % 3 + 1`).
Posting days: Monday, Wednesday, Friday.

## Writing a reel script (weekly prep run)

Copy the shape of `parts/part_03/script.json`.

- About 30 seconds (25 to 40 is fine), 12 to 15 sentences.
- Triple hook first, three short lines: context, lean, snapback. The hook must be true to what this reel shows
  and must be paid off inside the reel.
- Then the story: Wahib's own lines from the chapter, trimmed, in order. Dialogue gets `"style": "voice"`.
- The last sentence is the CTA, `"part": "cta"`: "Follow for part N." with N = this part's number + 1, in words.
- Every 5th part (5, 10, 15, ...): before the CTA add "Chapter C is free to read. The link is in my bio."
  and set `"byline": true`. First check the bio link: `INSTAGRAM_GET_USER_INFO` (account instagram_true-cage,
  fields `website,biography`). If there is no link yet, say "Chapter C is free to read on Royal Road." instead.
  All other parts: no name, no link line, `"byline": false`.
- `cap` marks: " | " new block, " / " new line, `*word*` blue italic accent, `**word**` bold.
  At most 2 lines per block. `y` is the block's top: about 260 to 440 over sky at the top, 1150 to 1330 low.
- `"say"`: what the voice reads if it must differ from the screen text (pronunciation fixes).
  Book names are respelled automatically by `NAMES` in `pipeline/narrate.py` (Aenor is said "Eh-nor");
  add new names there.
- `"caption"`: "<hook lines>\nChapter C, part R.\n<one question for the comments>\n#longingmoonstory #scifi #webnovel #animation #bookstagram"
- `"shots"`: 3 to 5 new images, each with `file` (images/01_name.jpg ...), `for` (which lines) and the full Flow `prompt`.
  Start every prompt with the Look book style line, use `@Allen` / `@Aenor`, ask for empty sky in the top third.
  Reuse `assets/` images where they fit.
- `"scenes"`: which image is on screen from which sentence, with camera moves `cam0`/`cam1` = [x, y, zoom]
  in pixels of the image scaled to 768 wide. 384, 688 is the centre of a 9:16 image.
- Test the voice now: `python3 pipeline/narrate.py parts/part_NN/script.json af_bella parts/part_NN/narration.wav 1.0`
  then `python3 pipeline/align.py parts/part_NN/narration.wav`. Every line must say OK.
- `"status": "ready"`. Add an empty `parts/part_NN/images/.keep` so Wahib's upload link opens.
  Commit and push the scripts (no wav files; .gitignore skips them).

## Making the images (weekly prep run, needs Wahib's Chrome)

1. In Chrome, open the Flow project. Use Image mode, 9:16. For each shot paste its prompt (with @Allen / @Aenor).
2. Pick the best result per shot. Faces and suits must match the characters; no text in the image.
3. Flow images can't be fetched from outside his signed-in browser, so Wahib moves them:
   send him one message listing, per part, which picture is which shot, and the upload link
   `https://github.com/WahibEjaz/longing-media/upload/main/parts/part_NN/images`.
   File names don't matter; the posting run matches them by looking.

## Posting run (Monday, Wednesday, Friday)

1. Clone or pull this repo. Read `state.json`; NN = `next_part`.
2. If `parts/part_NN/script.json` is missing, or any shot image is missing: post nothing,
   notify Wahib what is missing (with the upload link), stop.
3. If the images have other names than the `shots` files: open each image (skip `.keep`), match it to the
   shot descriptions, and rename with `git mv` to the shot file names (convert to JPEG if it is a PNG or WebP).
   If an image clearly breaks the look (wrong face, a character in normal clothes outside the city's shield,
   text in the image), post nothing and tell Wahib which shot to redo.
4. `bash pipeline/setup.sh` then `python3 pipeline/make_reel.py parts/part_NN`.
   - Exit 2 = a misheard line: fix with `"say"` (or NAMES) and run again.
   - Exit 3 = a caption line too wide: split it with " / " and run again.
5. Look at `parts/part_NN/qa_frames.jpg` and `cover.jpg`. Text must never sit on a face; the cover's
   "PART N" badge must be readable. Fix `y` or the camera and run again if needed.
6. Copy `reel.mp4` to `reels/Longing_Part_NN.mp4` and `cover.jpg` to `reels/Longing_Part_NN_cover.jpg`.
   Commit and push. If the push is refused, attach the repo with push access
   (`add_repo` owner WahibEjaz, repo longing-media, access push) and push again.
   Then check that `https://raw.githubusercontent.com/WahibEjaz/longing-media/main/reels/Longing_Part_NN.mp4`
   answers 200 with the right size (it can take a minute).
7. Post with Composio, account `instagram_true-cage`:
   - `INSTAGRAM_POST_IG_USER_MEDIA`: ig_user_id "29283205264669909", media_type "REELS", share_to_feed true,
     video_url = the raw mp4 link, cover_url = the raw cover link, caption = the script's caption (plain "#").
   - `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`: same ig_user_id, creation_id from step 1, max_wait_seconds 300.
   - `INSTAGRAM_GET_IG_MEDIA` on the new id: check the caption shows "#" (not "%23") and get the permalink.
8. Update `state.json` (add the part to `posted`, `next_part` + 1) and set the script's `"status": "posted"`.
   Commit and push.
9. Notify Wahib in one short message: "Part N is live: <permalink>". If anything failed, say what and stop.
