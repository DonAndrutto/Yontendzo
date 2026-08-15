# Yontendzo
Structural outline of the Treasury of Precious Qualities, connected with the root text.
Developed by Andrzej R. Rybszleger. 

## Naming the controls

The **?** at the end of the toolbar dims and blurs the text and names every
control that is on screen at that moment, so the interface explains itself at a
glance. Tap anywhere, press Escape, or tap the **?** again to put it away. It
opens only when asked — never on its own — and changes nothing: no setting, no
scroll position, nothing remembered.

Which controls get named is worked out each time it opens, so it follows the
app: the reading-position bar and the return-to-chapter button are named when
they are up, and controls scrolled behind the header are left alone. Labels are
too wide to sit under their own controls — a label runs about twice the width of
the control it names, and controls within a group sit two pixels apart — so they
are packed into a staircase of rows with a hairline drawn back to each control.

## Installing it as an app

The site is a progressive web app, so it can be kept on a phone or tablet home
screen and opened full screen, with or without a connection:

- **Android / Chrome, Edge** — tap **Install** on the strip that appears near
  the bottom, or use the browser menu's *Install app*.
- **iPhone / iPad** — tap **Share**, then **Add to Home Screen**.
- **Desktop** — use the install icon in the address bar.

The strip only appears on touch devices, waits until the welcome screen is out
of the way, withdraws on its own if ignored, and stops asking once it has been
waved away a few times.

## Icons

Every icon is derived from `IMG_8733.jpeg` by `tools/make-icons.py`, which
crops the artwork's white margin and rounded corners away (platforms apply
their own mask), then writes three families into `icons/`: full-bleed icons for
the home screen, emblem-only maskable icons for Android's adaptive shapes, and
a tight crop of the tree and wheel for the browser tab, where the wordmarks
would be too small to read. Regenerate them with:

```sh
python3 tools/make-icons.py    # requires Pillow and NumPy
```
