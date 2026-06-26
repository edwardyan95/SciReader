# SciReader Capture Extension

This unpacked Chrome extension captures the article text, figure images, and available supplement PDF links from an authenticated Nature-family, Cell Press, or Science page, then sends them to the local SciReader server at `http://127.0.0.1:4174`.

## Install

1. Open `chrome://extensions` in Chrome.
2. Turn on Developer mode.
3. Click Load unpacked.
4. Select this folder:
   `C:\Users\dirk\Documents\Codex\2026-05-11\i-want-to-start-a-project\chrome-extension`

## Use

1. Start the SciReader local server.
2. Open the Nature-family, Cell Press, or Science paper in your normal Chrome profile where university access works.
3. Click the SciReader extension icon.
4. Click Capture article.
5. Open SciReader and load the same paper URL. It will use the captured local snapshot.
