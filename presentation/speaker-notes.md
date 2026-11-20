# PROWL capstone: speaker notes

Working file for the speech. We write and edit everything here, then copy the final text into each slide's notes in PowerPoint.

- **Deck:** `PROWL-Capstone-Presentation.pptx` (same folder)
- **Talk:** 10 minutes + 5 minutes of Q&A. Wednesday, December 9, 3:00 PM
- **Pace:** about 130–150 spoken words per minute. Word budgets below follow that.
- **Placeholders:** anything in `[brackets]` is waiting on final numbers or a decision.

**Status key:** ⬜ not started · 🟨 draft · ✅ final (copied into PowerPoint)

---

## Timing plan

You can't see Presenter View during the demo, because the screen is mirrored and shows the app. So the timing runs on **four checkpoints** instead of watching the clock the whole time.

| Checkpoint | Clock | Where you should be |
|---|---|---|
| A | **1:10** | Done with the intro, saying "Let me show you" |
| B | **5:25** | Done with the demo, back on PowerPoint (slide 7) |
| C | **7:25** | Starting the results slide (slide 9) |
| D | **9:40** | On the Questions slide |

**How to keep time:**
1. Start a stopwatch on your phone (or watch) on the podium when you begin. PowerPoint's timer is fine for slides 1–6, but you won't see it during the demo.
2. Better option: set a **countdown timer for 4:15** and start it the moment you switch to the app. When it buzzes, finish the step you're on and switch back.
3. After the demo, look at Presenter View's timer and follow the "If you're behind" rules below.

**If you're behind after the demo:**
| Behind by | Cut |
|---|---|
| Up to 30 s | Slide 8: say only the first and last beats |
| 30–60 s | Also slide 10: talk through only "What went well" and "What was hard" |
| Over 60 s | Also slide 7: one sentence ("Two pipelines feed one app: the model and the literature assistant") |

Never cut slide 9 (results) or slide 11 (conclusion).

---

# VOICE MEMO PROMPTS

**How to record:**
- One memo per numbered topic, 1–3 minutes each. Name them by number, like `03 grandfather`.
- Talk as if you're explaining it to a friend who isn't technical. Don't aim for a speech.
- Don't restart when you stumble; keep going. Rambling is fine, and we'll trim it later.
- If a question doesn't spark anything, skip it.
- Voice Memos on the iPhone can transcribe for you. Paste the transcripts in here, under each memo, or send them to me.

**Priority:** memos 1–6 first (the intro), then the others whenever you have time.

---

## Intro (most important)

### Memo 1: Who you are and what PROWL is → slide 1
1. Introduce yourself the way you would to someone at a career fair.
2. Explain what PROWL does in two sentences to someone who's never heard of it.
3. Now explain it again as if you were talking to your grandma.
4. Who would use it, and what would they do with it?

> _transcript:_

### Memo 2: The name → slide 1
1. What does PROWL stand for?
2. Tell the story of picking it. Which model names did you see on the leaderboard? Why did you want an acronym?
3. How did the panther theme come out of it?

> _transcript:_

### Memo 3: Your grandfather → slide 2
1. What happened in 1998? What did the scan miss?
2. What did that mean for him and for your family afterward?
3. What did he do at Intermountain?
4. How does his story connect to wanting a medical project?
5. Why do you think healthcare is a good use of AI?

> _transcript:_

### Memo 4: Johns Hopkins and the dataset → slide 3
1. Tell the story of talking with someone from Johns Hopkins: what you asked, what they said, and how it led to this project. (Just tell it naturally; we'll choose the framing later.)
2. What is PanTS, and why did they make it public?
3. What did it feel like to pick a problem a top research center is working on?

> _transcript:_

### Memo 5: Why the pancreas is hard → slides 3–4
1. Explain to someone non-technical why the pancreas is hard to find on a CT scan.
2. Why is finding a lesion on it, and outlining it, even harder?
3. What was your goal, and why 0.50?

> _transcript:_

### Memo 6: Your aunt → slide 5, demo and conclusion
1. Who is she, and what does she do at the hospital?
2. Walk me through the session. What did you show her first? What surprised her?
3. What did she say about the AI they use now (the circles on mammograms)?
4. What did she say about 3D, and about centimeters?
5. What did you change after talking to her?
6. What was her reaction that stuck with you most? Try to remember her exact words.

> _transcript:_

---

## Demo

### Memo 7: Practice narration → slide 6
Open the app and click through the demo path (Studies → 9005 → 3D → findings → compare → Ask PROWL → summary), talking out loud as if you were presenting. Record your voice only. This gives us natural wording for each step and a rough time.

> _transcript:_

---

## Technologies

### Memo 8: How PROWL works → slide 7
1. Explain to a classmate how PROWL works under the hood: where the data comes from, how the model learns, and how the outlines end up in the app.
2. How does Ask PROWL work, and why does it only answer from papers?
3. Why does everything run on your own machines?

> _transcript:_

### Memo 9: Building the model → slide 8
1. Why STU-Net? In your own words, what does "pretrained" mean, and why does it help?
2. What was training actually like: two machines, how long it took, anything that broke?
3. What's one moment from training you'll remember?

> _transcript:_

---

## Retrospective and conclusion

### Memo 10: The results → slide 9
1. How do you feel about where your score landed compared with Johns Hopkins?
2. What does a Dice around 0.48 mean in practice? What does the model get right, and where does it struggle?

> _transcript:_

### Memo 11: Looking back → slide 10
1. When did you realize how hard this project would be?
2. Was there a moment it felt impossible? A moment it clicked?
3. What are you proudest of?
4. Honestly, what happened with the UI timeline?
5. If you started over tomorrow, what would you do differently?
6. What's the biggest thing you learned?

> _transcript:_

### Memo 12: The ending → slide 11
1. If the audience remembers one thing about PROWL, what should it be?
2. Where could PROWL go next?
3. How do you feel about the project now, compared with when you started?

> _transcript:_

---

## Q&A practice

### Memo 13: Rapid-fire answers (keep each under 30 seconds)
1. Why the pancreas?
2. Is your score really comparable to Johns Hopkins'?
3. Does it ever get it wrong? What happens then?
4. Could a hospital use this today?
5. Why not just use Johns Hopkins' own model?
6. What would it take for a hospital to trust a tool like this?
7. How do you stop the AI assistant from making things up?
8. How did you use AI tools to build this? (Judges often ask this one.)
9. What was the hardest bug or problem you hit?
10. What would you do with another month?

> _transcript:_

---

# INTRO (0:00–1:10)

This section gets a full script, memorized. Memorize the first two sentences word for word.

**Voice memos:** memos 1–6 in the "Voice memo prompts" section feed this section.

---

## Slide 1: Title ⬜
**Time:** 0:00–0:15 · **Budget:** ~35 words

**On the slide:** spinning 3D model of the pancreas, lesion and vessels · silver panther · "PROWL" · "Pancreatic Review and Outlining Workflow for Lesions" · your name and date

**Draft beats:**
- Hi, I'm Quinton, and this is PROWL.
- It stands for Pancreatic Review and Outlining Workflow for Lesions.
- Name story: every model on the leaderboard had a cool acronym name, so mine needed one too.

**Script:**
> _(to write from the voice memo)_

---

## Slide 2: Why this matters to me ⬜
**Time:** 0:15–0:35 · **Budget:** ~45 words

**On the slide:** a large "1998" · "A stroke, a scan, and a clot no one found" · a card with three points: my grandfather; a family in healthcare; where AI can do the most good

**Draft beats:**
- In 1998 my grandfather had a stroke. A scan was taken, but the clot wasn't found, and the damage was permanent.
- He'd spent his whole career in healthcare leadership at Intermountain.
- That gap between what a scan shows and what a doctor sees is why medical imaging matters to me.
- I think healthcare is one of the best things AI can be used for.

**Delivery:** slow down here.

**Script:**
> _(to write from the voice memo)_

---

## Slide 3: Can you find the pancreas? ⬜
**Time:** 0:35–0:45 · **Budget:** ~30 words + a pause

**On the slide:** one CT slice, no overlay

**Draft beats:**
- Johns Hopkins line (pick one):
  - **A:** "When I was looking at grad schools, someone at Johns Hopkins told me the best thing I could do was work on a problem their researchers care about. That stuck with me."
  - **B:** "Johns Hopkins released a huge public pancreas CT dataset because this problem is so hard, and they published their scores, so I had something real to aim for."
- "This is one slice of a CT scan. Can you find the pancreas?"
- **Pause about 2 seconds, then click.**

**Script:**
> _(to write)_

---

## Slide 4: PROWL can ⬜
**Time:** 0:45–0:55 · **Budget:** ~30 words

**On the slide:** the same CT slice, with PROWL's outline (teal = pancreas, red = lesion) and a small legend

**Draft beats:**
- The pancreas is some of the softest tissue in the body, and it barely stands out on CT.
- Finding it is hard. Finding a lesion on it and outlining it is harder.
- Teal is the pancreas and red is the lesion, both drawn by PROWL's model.

**Script:**
> _(to write)_

---

## Slide 5: Outlines, not circles ⬜
**Time:** 0:55–1:10 · **Budget:** ~40 words

**On the slide:** close-up of the lesion (solid = PROWL, dashed = expert, Dice 0.916 on this scan) · "Today: hospital AI marks a spot with a circle" vs "PROWL: outlines the pancreas and the lesion, in 2D and 3D" · goal card: **0.50**

**Draft beats:**
- At my aunt's hospital, the AI they use for mammograms puts little circles on the screen for radiologists to check.
- PROWL doesn't circle. It outlines the organ and the lesion, in 2D and 3D.
- Dice measures how well an outline overlaps the expert's, and 1.0 is perfect. My goal was 0.50.
- **Transition (memorize):** "Let me show you what that looks like."

**Script:**
> _(to write)_

---

# DEMO (1:10–5:25)

## Slide 6: Let me show you ⬜
**On the slide:** spinning 3D model · "Let me show you"

Not scripted. Run sheet below; we'll lock it after the Monday demo.

**Before the talk:**
- [ ] App running, PanTS 9005 loaded, browser zoom about 125%
- [ ] Ask PROWL model loaded (ask one test question beforehand)
- [ ] Ask PROWL question chosen: `[question]`
- [ ] Do Not Disturb on, other apps closed, charger plugged in

**Switch in:** Cmd+F1 (mirroring on) → Cmd+Tab to the browser → **start the 4:15 countdown**

| # | Step | Time | Say (beats) | If behind |
|---|---|---|---|---|
| 1 | Studies page → open PanTS 9005, 2D overlay, scroll to the lesion | 0:30 | "Here's a real CT from the test set." | Keep |
| 2 | 3D view, vessels colored by distance | 0:45 | Aunt: hospitals are moving to 3D, but the software is expensive and they needed new machines. This runs in a browser. | Keep |
| 3 | Findings card in cm | 0:45 | 3.6 × 2.9 cm lesion in the pancreatic body; celiac artery 228° contact = encasement; dilated ducts. Aunt: the hospital talks in centimeters, so I changed every measurement. | Shorten to the size + celiac |
| 4 | Compare with reference + Dice | 0:30 | "Dashed is the expert, solid is PROWL. They overlap at `[Dice]`." | Keep |
| 5 | Ask PROWL: one question, open a citation | 1:00 | "It only answers from real papers, and every claim links to its source." | **Cut first** |
| 6 | Review summary | 0:30 | "PROWL drafts; the radiologist decides." | **Cut second** |

**Switch out:** Cmd+Tab to PowerPoint → Cmd+F1 (mirroring off) → you're on slide 7.

**If the live demo breaks:** stay calm, say "Let me show you the screenshots instead," type **21** and press Enter, then click through demo backups 1–7 (slides 21–27).

---

# TECHNOLOGIES (5:25–7:25)

## Slide 7: How PROWL fits together ⬜
**Time:** 5:25–6:25 · **Budget:** ~140 words

**On the slide:** two rows of boxes leading to one app. Segmentation model: PanTS CT scans → Training (STU-Net · PyTorch + MONAI · MLflow) → Predictions (saved outlines + FastAPI). Literature assistant: PubMed/PMC → Search index (PostgreSQL + pgvector) → Local LLM (Qwen3 via Ollama). Both feed the PROWL app (React + NiiVue).

**Draft beats:**
- Two pipelines feed one app.
- Top: Johns Hopkins' CT scans → training STU-Net with PyTorch and MONAI, tracked in MLflow → saved outlines served through FastAPI.
- Bottom: open-access PubMed papers → a search index in PostgreSQL with pgvector → a local Qwen3 model through Ollama. Everything runs on my own machines.
- Both come together in a React app, with NiiVue for the 2D and 3D viewer.

**Open:** confirm the tool list before December 4.

**Script:**
> _(to write)_

---

## Slide 8: How the model was built ⬜
**Time:** 6:25–7:25 · **Budget:** ~140 words

**On the slide:** "STU-Net, pretrained on large CT datasets, fine-tuned to outline the pancreas and lesions" · four stat cards: `[1,333]` training scans · `[~740 h]` of compute · 2 machines (Mac + Lenovo GPU) · `[24,000]` training updates · Training page screenshot

**Draft beats:**
- STU-Net is a model already pretrained on a lot of CT data. I fine-tuned it to outline the pancreas and lesions.
- Trained across two machines: my Mac and a Lenovo with an NVIDIA GPU.
- `[one sentence on scale, using the confirmed numbers]`
- Every run is tracked, and the Training page in the app shows the history.
- **Transition:** "So how close did I get?"

**Open:** confirm the three numbers · recapture the Training screenshot before December 4.

**Script:**
> _(to write)_

---

# RETROSPECTIVE (7:25–8:55)

## Slide 9: How close did I get? ⬜ (waits for the Dec 4 freeze)
**Time:** 7:25–8:10 · **Budget:** ~100 words

**On the slide:** bar chart: PROWL `[0.48]` vs JHU models A/B/C `[0.51 / 0.52 / 0.54]`, dashed goal line at 0.50 · cards: `[0.48]` PROWL lesion Dice · `[0.03–0.06]` behind Johns Hopkins

**Draft beats:**
- My goal was 0.50 lesion Dice. I landed at `[final]`.
- Johns Hopkins' published models score `[A]`, `[B]` and `[C]`.
- So PROWL is within `[gap]` of a team at one of the best medical research centers in the world.
- If 0.50 isn't reached: "I didn't hit 0.50 yet, and that's part of the story."

**Open:** final number · real model names from the Codex breakdown · remove the DRAFT pill.

**Script:**
> _(to write after the freeze)_

---

## Slide 10: Looking back ⬜
**Time:** 8:10–8:55 · **Budget:** ~100 words

**On the slide:** three cards.
- **What went well:** results close to Johns Hopkins · real user feedback changed the product (cm, 3D) · `[your pick]`
- **What was hard:** a bold choice, the hardest organ to outline · I put the UI off; ML was the fun part · catching up on the app at the end
- **Next time:** build the app alongside the model from week 1 · time-box experiments · `[your pick]`

**Draft beats:**
- Frame each one as "I learned", not as an apology.
- Showing it to my aunt changed the product: centimeters, and leaning into 3D.
- I knew the ML would take the most time, and honestly it's the part I enjoy, so the app got pushed back.

**Open:** two "your pick" items.

**Script:**
> _(to write)_

---

# CONCLUSION (8:55–9:40)

## Slide 11: PROWL today ⬜
**Time:** 8:55–9:40 · **Budget:** ~100 words

**On the slide:** 1 Outlines the pancreas and lesions in 2D and 3D · 2 Measures in centimeters, with vessel contact, for a radiologist to review · 3 Scores `[0.48]` lesion Dice, close to Johns Hopkins · quote card: "She'd never seen anything outline the organs like this." (my aunt) · 3D render

**Draft beats:**
- Call back to the opening: a scan can hold the answer, and the hard part is seeing it.
- The three takeaways.
- Close with my aunt's reaction.
- Optional one line of future work: run on any CT, not just this dataset.
- **Last line (memorize):** "Thank you. I'm happy to take questions."

**Open:** confirm the quote wording with your aunt's actual words · final score.

**Script:**
> _(to write)_

---

## Slide 12: Questions? ⬜
**On the slide:** panther · "Questions?" · "Thank you · Quinton Evans"

Jump to any backup slide by typing its number and pressing Enter.

---

# Q&A PREP (5 minutes)

Aim for answers of about 20 seconds each. Practice them out loud.

| Likely question | Short answer (draft) | Slide |
|---|---|---|
| What does Dice mean? | How much my outline overlaps the expert's, from 0 to 1. Small lesions are hard because a few pixels of disagreement is a big share of the lesion. | 13 |
| Is your score comparable to Johns Hopkins'? | `[conditions: same 901-scan test set; say exactly what matches and what doesn't]` | 14 |
| Does it ever get it wrong? | Yes. Here it flagged a healthy scan, and here it missed a small lesion. That's why a human reviews every result. | 15, 16 |
| How do you know when the model is unsure? | It runs 8 flipped copies of the scan; where they disagree, the boundary is uncertain. | 17 |
| How long did training take? | `[confirmed hours]` across two machines, every run tracked. | 18 |
| How do you stop the AI assistant from making things up? | It searches real papers first, answers only from those passages, cites every claim, and says so when the evidence isn't there. | 19 |
| What would you do next? | Run on any CT end to end, train the anatomy outlines, hospital file import, a reader study with radiologists. | 20 |
| Could a hospital use this today? | No. It's a research tool, not a diagnosis. The goal is to support a radiologist's review. | — |
| Why the pancreas? | `[your answer: Johns Hopkins + hardest problem + healthcare]` | — |
| Why not just use Johns Hopkins' model? | `[your answer]` | — |
| How did you use AI tools to build this? | `[your answer]` | — |
| What was the hardest part? | `[your answer]` | — |

**Backup slide numbers:** 13 Dice · 14 Johns Hopkins comparison · 15 false alarm · 16 small lesion · 17 confidence · 18 training history · 19 Ask PROWL · 20 what's next · 21–27 demo backups 1–7 · 28 curved view · 29 outline editor · 30 confidence map

---

# Open items

- [ ] Voice memos 1–6 (this weekend) → intro script, slides 1–5
- [ ] Voice memos 7–13 (as time allows)
- [ ] Johns Hopkins wording: A or B
- [ ] Lock the demo run sheet after Monday's class demo
- [ ] Ask PROWL question + screenshots (slides 19 and 26)
- [ ] Confirm the slide 8 numbers; recapture the Training page
- [ ] Final Dice + JHU model names (December 4 freeze)
- [ ] Two "your pick" items on slide 10
- [ ] Aunt's exact words for the quote
- [ ] Test Cmd+F1 at home; ask the professor about the commons setup
- [ ] Record a backup demo video before December 2
