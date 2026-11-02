# fledgeview.com

The FledgeView website: a home page, the app, and a downloadable single-file copy.

```
index.html               Home page
app/index.html           FledgeView itself (fledgeview.com/app/)
app/manifest.webmanifest Lets Chrome and Edge install FledgeView as an app
app/sw.js                Offline support (works without internet after the first visit)
download/FledgeView.html Single-file copy with everything built in (works fully offline)
assets/                  Fonts, the EXIF and ZIP libraries, icons, and screenshots
robots.txt, sitemap.xml  For search engines
```

Nothing loads from other websites: fonts and libraries are served from fledgeview.com.

## Publishing on Render

1. Put this folder in a GitHub repository (for example `fledgeview-site`). With GitHub Desktop: File → Add local repository, then Publish.
2. In Render: **New → Static Site**, choose the repository.
   - Build command: leave empty
   - Publish directory: `.` (the repository root)
3. Render gives the site an address like `fledgeview-site.onrender.com`. Check that it works there first.

## Connecting fledgeview.com (GoDaddy)

1. In Render, open the site → **Settings → Custom Domains** → add `fledgeview.com`. Render adds `www.fledgeview.com` automatically and redirects one to the other.
2. In GoDaddy: **My Products → fledgeview.com → DNS**.
   - **A** record: Name `@`, Value `216.24.57.1`
   - **CNAME** record: Name `www`, Value `your-site-name.onrender.com` (use the exact name Render shows)
   - Delete any other A records for `@` (GoDaddy's "parked" page), and any **AAAA** records.
   - Don't use GoDaddy's **Forwarding**; it makes the address bar show the onrender.com name.
3. Back in Render, click **Verify**. DNS usually updates within minutes, sometimes a few hours. HTTPS is set up automatically.

## Adding the YouTube walkthrough

In `index.html`, near the bottom, change

```
const YOUTUBE_URL = '';
```

to your video's link, for example `const YOUTUBE_URL = 'https://youtu.be/abc123';`. The "Watch the walkthrough" buttons appear automatically.

## Publishing an update to FledgeView

1. Replace `app/index.html` (and `download/FledgeView.html`) with the new versions.
2. In `app/sw.js`, change the `CACHE` name to match the new version (for example `fledgeview-0.9.4-beta`), so returning visitors get the update.
3. Commit and push. Render republishes in about a minute.
