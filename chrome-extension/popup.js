const captureButton = document.querySelector("#capture");
const downloadSupplementsButton = document.querySelector("#download-supplements");
const statusBox = document.querySelector("#status");
const openReaderLink = document.querySelector("#open-reader");

function setStatus(message) {
  statusBox.textContent = message;
}

function filenameFromUrl(url) {
  try {
    const pathname = new URL(url).pathname;
    return decodeURIComponent(pathname.split("/").filter(Boolean).pop() || "");
  } catch {
    return "";
  }
}

async function runPageCapture() {
  async function imageAttachmentFromLink(link) {
    const response = await fetch(link.href, { credentials: "include" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const contentType = response.headers.get("content-type") || "image/jpeg";
    const buffer = await response.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const chunkSize = 0x8000;
    for (let cursor = 0; cursor < bytes.length; cursor += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(cursor, cursor + chunkSize));
    }
    return {
      name: `${link.id || "figure"}.jpg`,
      url: link.href,
      contentType,
      dataBase64: btoa(binary),
    };
  }

  const anchors = Array.from(document.querySelectorAll("a[href]"));
  const links = anchors
    .map((anchor) => {
      let href = "";
      try {
        href = new URL(anchor.getAttribute("href"), location.href).href;
      } catch {
        href = "";
      }
      return {
        text: anchor.textContent.replace(/\s+/g, " ").trim(),
        href,
      };
    })
    .filter((link) => link.href);

  const figureImageLinks = Array.from(
    document.querySelectorAll("figure[id], div.figure[id], div.fig[id], div[data-test='figure'][id], div[id^='F'], div[id^='fig']"),
  )
    .map((figure) => {
      const id = figure.id || "";
      if (!/^fig|^F/.test(id)) return null;
      const image =
        figure.querySelector("img[src]") ||
        figure.querySelector("img[data-src]") ||
        figure.querySelector("img[data-original]") ||
        figure.querySelector("a[data-supp-info-image]") ||
        figure.querySelector("source[srcset]");
      const label = figure.querySelector(".figure__label, .caption__label, .fig-label, .figure-label, strong")?.textContent || id;
      const rawUrl =
        image?.getAttribute("src") ||
        image?.getAttribute("data-src") ||
        image?.getAttribute("data-original") ||
        image?.getAttribute("srcset") ||
        image?.getAttribute("data-supp-info-image") ||
        "";
      const imageUrl = rawUrl.includes(",") ? rawUrl.split(",").pop().trim().split(/\s+/)[0] : rawUrl;
      if (!imageUrl) return null;
      let href = "";
      try {
        href = new URL(imageUrl, location.href).href;
      } catch {
        href = "";
      }
      return href
        ? {
            id,
            label: label.replace(/\s+/g, " ").trim(),
            href,
          }
        : null;
    })
    .filter(Boolean);
  const figureImageAttachments = [];
  for (const link of figureImageLinks.slice(0, 12)) {
    try {
      figureImageAttachments.push(await imageAttachmentFromLink(link));
    } catch {
      // The extension-context fetch gets a second chance after the page snapshot returns.
    }
  }

  return {
    url: location.href,
    title: document.title,
    bodyText: document.body.innerText,
    html: document.documentElement.outerHTML,
    links,
    figureImageLinks,
    figureImageAttachments,
  };
}

function attachmentLinksFromLinks(links) {
  return links.filter((link) => {
    const combined = `${link.text} ${link.href}`;
    return (
      /\.pdf(?:[?#].*)?$/i.test(link.href) &&
      (/document\s+s\d+/i.test(combined) ||
        /figures?\s+s\d+/i.test(combined) ||
        /supplement(?:ary|al)?/i.test(combined) ||
        /supporting\s+information/i.test(combined) ||
        /\/suppl(?:ement(?:ary|al)?)?[_/-]/i.test(link.href) ||
        /_sm\.pdf/i.test(link.href) ||
        /\/attachment\//i.test(link.href) ||
        /mmc\d+\.pdf/i.test(link.href))
    );
  });
}

function primarySupplementLinks(links) {
  return attachmentLinksFromLinks(links).filter((link) => {
    const href = link.href.toLowerCase();
    return !href.includes("mdar") && !href.endsWith(".zip");
  });
}

async function fetchAttachment(link, index) {
  const response = await fetch(link.href, { credentials: "include" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const contentType = response.headers.get("content-type") || "application/octet-stream";
  const buffer = await response.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let cursor = 0; cursor < bytes.length; cursor += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(cursor, cursor + chunkSize));
  }
  return {
    name: filenameFromUrl(link.href) || link.text || `attachment-${index}.pdf`,
    url: link.href,
    contentType,
    dataBase64: btoa(binary),
  };
}

async function fetchFigureImage(link, index) {
  const response = await fetch(link.href, { credentials: "include" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const contentType = response.headers.get("content-type") || "image/jpeg";
  const buffer = await response.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let cursor = 0; cursor < bytes.length; cursor += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(cursor, cursor + chunkSize));
  }
  return {
    name: `${link.id || `figure-${index}`}.jpg`,
    url: link.href,
    contentType,
    dataBase64: btoa(binary),
  };
}

async function addAttachments(snapshot) {
  const attachments = [...(snapshot.figureImageAttachments || [])];
  const capturedUrls = new Set(attachments.map((attachment) => attachment.url).filter(Boolean));
  const attachmentLinks = attachmentLinksFromLinks(snapshot.links || []);
  for (const [index, link] of attachmentLinks.slice(0, 4).entries()) {
    try {
      attachments.push(await fetchAttachment(link, index + 1));
    } catch (error) {
      attachments.push({
        name: link.text || "unfetched attachment",
        url: link.href,
        error: error.message || "Could not fetch this attachment from the extension session.",
      });
    }
  }
  for (const [index, link] of (snapshot.figureImageLinks || []).slice(0, 12).entries()) {
    if (capturedUrls.has(link.href)) continue;
    try {
      attachments.push(await fetchFigureImage(link, index + 1));
    } catch (error) {
      attachments.push({
        name: `${link.id || "figure"} image`,
        url: link.href,
        error: error.message || "Could not fetch this figure image from the extension session.",
      });
    }
  }
  return { ...snapshot, attachments };
}

async function downloadSupplementLinks(links) {
  const supplementLinks = primarySupplementLinks(links || []);
  let started = 0;
  for (const link of supplementLinks.slice(0, 4)) {
    try {
      await chrome.downloads.download({
        conflictAction: "uniquify",
        filename: `SciReader/${filenameFromUrl(link.href) || `supplement-${started + 1}.pdf`}`,
        saveAs: false,
        url: link.href,
      });
      started += 1;
    } catch {
      // Keep trying the remaining files; status reports the count below.
    }
  }
  return started;
}

async function postSnapshot(snapshot) {
  const response = await fetch("http://127.0.0.1:4174/api/import-snapshot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(snapshot),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "SciReader could not import this capture.");
  return payload;
}

captureButton.addEventListener("click", async () => {
  captureButton.disabled = true;
  setStatus("Capturing visible text and supplements...");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("No active tab was found.");

    const [{ result: rawSnapshot }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: runPageCapture,
    });

    setStatus("Downloading supplement files...");
    const snapshot = await addAttachments(rawSnapshot);
    const payload = await postSnapshot(snapshot);
    const supplementCount = (payload.figures || []).filter((figure) => figure.id?.startsWith("supp-")).length;
    const downloadedCount = (snapshot.attachments || []).filter((attachment) => attachment.dataBase64).length;
    const failedCount = (snapshot.attachments || []).filter((attachment) => attachment.error).length;
    openReaderLink.href = `http://127.0.0.1:4174/index.html?url=${encodeURIComponent(payload.sourceUrl || tab.url)}`;
    setStatus(
      `Captured: ${payload.title}\nFigures: ${(payload.figures || []).length}, supplementary: ${supplementCount}\nDownloaded files: ${downloadedCount}${failedCount ? `, failed: ${failedCount}` : ""}`,
    );
  } catch (error) {
    setStatus(error.message);
  } finally {
    captureButton.disabled = false;
  }
});

downloadSupplementsButton.addEventListener("click", async () => {
  downloadSupplementsButton.disabled = true;
  setStatus("Starting supplement downloads...");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("No active tab was found.");
    const [{ result: rawSnapshot }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: runPageCapture,
    });
    const started = await downloadSupplementLinks(rawSnapshot.links || []);
    setStatus(
      started
        ? `Started ${started} supplement download${started === 1 ? "" : "s"}.\nAfter the PDF appears in Downloads/SciReader, send it to me or place it in the article cache folder.`
        : "No downloadable supplement PDFs were found on this page.",
    );
  } catch (error) {
    setStatus(error.message);
  } finally {
    downloadSupplementsButton.disabled = false;
  }
});

openReaderLink.addEventListener("click", (event) => {
  event.preventDefault();
  chrome.tabs.create({ url: openReaderLink.href });
});
