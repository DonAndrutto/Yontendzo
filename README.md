# Yontendzo
Structural outline of the Treasury of Precious Qualities, connected with the root text.
Developed by Andrzej R. Rybszleger. 

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
