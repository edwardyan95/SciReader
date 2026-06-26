# SciReader Prototype

This is the first local prototype for a context-preserving scientific reader.

Run the local importer server, then open the app at
`http://127.0.0.1:4174/index.html`:

```powershell
.\start-local.ps1
```

Opening `index.html` directly still shows the bundled Nature Neuroscience sample,
but URL import needs the local server because the browser app calls `/api/import`.

## Use From Another Device On The Same Network

Run the server in LAN mode on the main computer:

```powershell
.\start-lan.ps1
```

The server prints one or more LAN URLs, for example:

```text
LAN URL: http://192.168.1.25:4174/index.html
```

Open that URL on another device connected to the same Wi-Fi. The main computer
does the paper importing, account storage, note storage and AI calls. The other
device is just a browser client.

If the other device cannot connect:

- Make sure both devices are on the same Wi-Fi/network.
- Allow Python through Windows Defender Firewall for private networks.
- Confirm the main computer did not go to sleep.
- Try the local URL on the main computer first:
  `http://127.0.0.1:4174/index.html`.

Use local-only mode again with:

```powershell
.\start-local.ps1
```

## Develop On Another Computer

Clone or copy the project folder, then install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Set an API key on that computer if you want AI calls from that computer:

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_key_here", "User")
```

Open a new PowerShell window, then run:

```powershell
.\start-local.ps1
```

Local account data and paper notes live in `data/scireader-data.json`. That file
is intentionally ignored by git. If you want to move your local library/notes to
another computer, copy the `data` folder manually.

## What works now

- Clean article view with journal metadata.
- Synchronized figure rail that reacts as visible paragraphs change.
- Main, extended data and supplementary slots share one figure model.
- Independent figure zoom in the side rail.
- Optional "Follow text" mode for synchronizing the rail with the text, while
  still allowing independent manual scrolling.
- Pinning figures so they stay near the top while reading.
- Citation popovers instead of jumping to the reference section.
- Supplementary Fig. 1 rendered from the Nature supplementary PDF into a local
  image asset.
- A longer full-paper test flow with main text, results, discussion, main
  figures, extended data and rendered supplementary material.
- Nature article import for open-access `nature.com/articles/...` URLs, including
  cached article HTML, parsed sections, main figures, extended data figures,
  supplementary figure PDF rendering and reference extraction.
- Nature-family and Cell Press import through direct/open snapshots and an
  optional local Chrome extension for authenticated university-access pages.
- bioRxiv and eLife import for open-access article pages, including inline
  figures, tables where exposed by the publisher, and eLife figure supplements
  from the publisher figures page.
- Science import through the local Chrome extension capture route for
  authenticated `science.org/doi/...` pages.

## Authenticated browser capture

The unpacked extension lives in `chrome-extension`.

1. Open `chrome://extensions` in Chrome.
2. Enable Developer mode.
3. Click Load unpacked and select
   `C:\Users\dirk\Documents\Codex\2026-05-11\i-want-to-start-a-project\chrome-extension`.
4. Open a Nature-family, Cell Press or Science article in the Chrome profile
   where university access works.
5. Click the SciReader extension, then Capture article.
6. Open SciReader and load the same paper URL. The importer will prefer the
   captured local browser snapshot and any captured Document S1 PDFs.

## Next implementation step

Broaden the importer beyond Nature:

1. Add adapters for journal-specific article HTML layouts.
2. Improve supplementary PDF segmentation from page-level crops to figure-level
   crops.
3. Persist normalized article JSON separately from downloaded source assets.
4. Add a small import status panel so long supplementary processing feels calm.
