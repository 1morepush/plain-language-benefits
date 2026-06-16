# Plain Language — the drag-and-drop app (experimental)

A friendly window for people who don't use a terminal. Drag in a benefits letter, and
download an easy-to-read version. No coding needed.

> **Experimental.** This GUI lives on the `claude/gui-experimental` branch. The core
> command-line tool and evals on `main` are unaffected.

## Start it (one time setup)

1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Double-click **`run_gui.sh`** (macOS/Linux) or **`run_gui.bat`** (Windows).
   - Or, in a terminal: `bash run_gui.sh`
   - The first run installs what it needs and then opens the app in your web browser.

## Use it

1. **Paste your Anthropic API key** in the box at the top (get one at
   [console.anthropic.com](https://console.anthropic.com)). Tick "Remember on this
   computer" if you don't want to paste it again — it's saved only on your machine, in a
   file that is never shared or uploaded.
2. **Drag your notice** into the box (a `.pdf`, `.docx`, or `.txt` file).
3. **Pick an output format** — "Same as input", or TXT / DOCX / PDF.
4. Click **Translate my notice**.
5. Read the preview, and **download** the plain-language file.

## What you get

- The notice rewritten in clear, ~6th-grade language.
- A list of what you need to do, and by when.
- The exact quotes from your letter that each point comes from.
- A safety note: if the letter is high-stakes (a termination, overpayment, denial, or
  anything confusing), the app tells you to **see a caseworker or legal aid** instead of
  guessing.

## Good to know

- It is **not legal advice** — it's a plain-language summary to help you understand a letter.
- It never invents dates or dollar amounts; everything traces back to your notice.
- Scanned images / photos of letters won't work yet (the text isn't selectable). Use a file
  you can copy text from, or paste the text into a `.txt` file.
- Your key and your file stay on your computer; only the notice text is sent to the Claude
  API to do the rewrite.
