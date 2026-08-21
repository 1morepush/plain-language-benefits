# Images for the README

`gui-screenshot.png` — the shot used at the top of the README. It shows the real app with
`sample_docs/snap_recertification.txt` loaded, just before the Translate button is pressed.

## Replacing it

Keep the same filename and the README picks up the new version automatically. Worth
re-shooting whenever the interface changes noticeably.

1. Launch the app: `bash run_gui.sh` (or `run_gui.bat` on Windows). It opens in your browser.
2. Paste your API key, drag in `sample_docs/snap_recertification.txt` (or any notice), and
   pick an output format.
3. Take a screenshot of the app window (Mac: Shift+Cmd+4 · Windows: Win+Shift+S) showing the
   key box, the drag area, the format picker, and ideally the preview after a translation.
4. Save it as `docs/images/gui-screenshot.png` and commit it.

If you shoot one showing a completed translation, make sure the preview holds **real** model
output, not a mock-up — every other example in this repo is a genuine run, and the README
says so.

Tip: a short animated GIF (e.g. via Kap or ScreenToGif) of the drag → download flow is even
more compelling — save it as `gui-demo.gif` and swap the image link in the README.
