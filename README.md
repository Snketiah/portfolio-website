# stevenketiah — portfolio site

Plain static HTML/CSS/JS. No build step, no framework.

```
index.html                 homepage (photo, bio, project grid)
projects/<slug>/index.html one page per project
assets/css/style.css       all styling (one typeface: Hanken Grotesk)
assets/js/site.js          project filter, contents list, read time, lightbox, video autoplay
assets/img|video|files/<slug>/   media for each project
tools/                     media.py (resize photos/videos), page-template.html, BUILD_GUIDE.md — not needed on the live site
```

## Preview locally
```
python3 tools/serve.py
```
then open http://localhost:8080. (Opening the files directly with file:// breaks the folder-style links.)

## Publish
Any static host works. Upload the contents of this folder (the `tools/` folder can be left out).

- **GitHub Pages:** push this folder to a repo, then Settings → Pages → deploy from the `main` branch, root folder. `.nojekyll` is already here.
- **Netlify / Cloudflare Pages:** drag this folder onto the dashboard, or connect the repo with no build command and `/` as the publish directory.

## Adding a project
1. Copy `tools/page-template.html` to `projects/<new-slug>/index.html` and fill it in.
2. Make `assets/img/<new-slug>/cover.jpg` (≈2000 px wide) and `thumb.jpg` (1200×900) with `python3 tools/media.py img …`.
3. Add a card to the grid in `index.html` (`data-tags` drives the filter: robotics, power, embedded).
