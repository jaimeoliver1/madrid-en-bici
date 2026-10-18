# 24h of BiciMAD (video)

These are the scenes of the standalone 24-hour animation, built as a Claude Motion film. Each file is one scene:

- `scene-open.js`
- `scene-day.js`
- `scene-end.js`

`shared.js` holds the helpers the scenes share, `score.js` the soundtrack, and `base.css` and `scenes.json` the look and timing. The data comes from `site/film-data.js`.

The website does not use these files. Its player (`site/player.js`) redraws the same animation in the page, so you can pause it, scrub through the day and zoom. Use these files if you want to export the video as an MP4.
