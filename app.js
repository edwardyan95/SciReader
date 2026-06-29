const demoArticle = {
  sourceUrl: "https://www.nature.com/articles/s41593-026-02258-4",
  title:
    "Laminar organization of cellular microcircuits modulating human interictal epileptiform discharges",
  journal: "Nature Neuroscience",
  published: "30 April 2026",
  doi: "10.1038/s41593-026-02258-4",
  authors:
    "Alexander B. Silva, Siddharth A. Marathe, Quinn R. Greicius, Duo Xu, Shailee Jain, Jason E. Chung, Xiaofang Yang, Ankit N. Khambhati, Matthew K. Leonard, Jonathan K. Kleen, Edward F. Chang",
  sections: [
    {
      id: "abstract",
      title: "Abstract",
      paragraphs: [
        {
          id: "p-abstract-1",
          text:
            "Interictal epileptiform discharges (IEDs) are pathological bursts of brain activity between seizures in people with epilepsy. Despite their importance in diagnosis, cognitive comorbidities and therapeutic implications as biomarkers for neurostimulation, it is unknown how IEDs arise from structured large-scale neuronal firing across human cortical lamina.",
          figures: [],
          citations: [],
        },
        {
          id: "p-abstract-2",
          text:
            "We used high-density Neuropixels probes to record from epileptogenic tissue in patients undergoing resective surgery, sampling 1,152 neurons during 1,094 IEDs across nine neocortical sites. We identified microcircuits for IEDs organized by firing pattern, neocortical depth and putative cell type.",
          figures: [],
          citations: [],
        },
      ],
    },
    {
      id: "main",
      title: "Main",
      paragraphs: [
        {
          id: "p-main-1",
          text:
            "Epilepsy is a common neurological condition defined by seizures affecting over 50 million people worldwide [1]. Between seizures, abnormal neural circuits emit brief pathological bursts of electrical activity, termed interictal epileptiform discharges (IEDs) [2].",
          figures: [],
          citations: ["1", "2"],
        },
        {
          id: "p-main-2",
          text:
            "IEDs are helpful for localizing epileptogenic tissue [3] but may themselves contribute substantial cognitive comorbidities for patients with epilepsy, even when seizures are controlled [4,5]. Further, cyclical fluctuations in IED rate have been shown to forecast periods of heightened seizure risk [6,7].",
          figures: [],
          citations: ["3", "4", "5", "6", "7"],
        },
        {
          id: "p-main-3",
          text:
            "A particularly relevant clinical application of IEDs is closed-loop responsive neurostimulation (RNS) [8]. RNS requires several years of therapy to demonstrate optimal efficacy, and each day a typical patient receives thousands of electrical brain stimulations in response to IEDs.",
          figures: [],
          citations: ["8", "9", "10"],
        },
        {
          id: "p-main-4",
          text:
            "The motivating question is whether IEDs are random synchronous bursts or whether they reflect structured laminar microcircuits with predictable phases, cell types and depths. The prototype uses these figure references to test whether a reader can keep the mechanistic chain visible while the text advances.",
          figures: [],
          citations: ["14", "15", "16", "17"],
        },
      ],
    },
    {
      id: "results-recordings",
      title: "Neuropixels recordings and IED processing",
      paragraphs: [
        {
          id: "p-recordings-1",
          text:
            "To understand how human single neurons, distributed across neocortical depth, give rise to IEDs, the authors leveraged Neuropixels probes to record from cortical lamina during awake brain surgeries. Each probe had 384 active electrodes inserted trans-laminarly across the neocortical depths (Fig. 1a).",
          figures: ["fig-1"],
          citations: ["35", "36"],
        },
        {
          id: "p-recordings-2",
          text:
            "Local field potential recordings from these electrodes enabled identification of IEDs using a semi-automated detection algorithm followed by manual verification (Fig. 1b). IED waveform profiles were generally similar among contacts spanning the neocortical depth (Fig. 1c,d and Extended Data Fig. 1).",
          figures: ["fig-1", "ext-1"],
          citations: [],
        },
        {
          id: "p-recordings-3",
          text:
            "All recordings took place in tissue clinically determined to be in the epileptogenic zone and subsequently resected (Supplementary Fig. 1 and Supplementary Table 1). The study identified nine distinct Neuropixels insertion sites across four patients who showed occasional to frequent IEDs.",
          figures: ["supp-1"],
          citations: [],
        },
        {
          id: "p-recordings-4",
          text:
            "Spike sorting and waveform clustering separated regular-spiking, fast-spiking and positive-spiking units, setting up later analyses of whether firing pattern components align with putative cell classes (Extended Data Fig. 2).",
          figures: ["ext-2"],
          citations: ["35", "37", "38", "39"],
        },
      ],
    },
    {
      id: "results-single-neuron",
      title: "Single-neuron activity during IEDs",
      paragraphs: [
        {
          id: "p-single-1",
          text:
            "Temporal heterogeneity in neuronal responses was evident in raw rasters (Fig. 1i,j and Extended Data Fig. 3). Across cortical insertion sites, 22.6 to 85.1% of neurons were modulated during IEDs (Fig. 2a-c).",
          figures: ["fig-1", "fig-2", "ext-3"],
          citations: ["17", "29"],
        },
        {
          id: "p-single-2",
          text:
            "Firing rates across neurons were asynchronous and tiled the peri-IED interval, evident in single insertion sites and when aggregated across all neurons (Fig. 2c,d). This contrasts with classic paroxysmal depolarization models of IEDs.",
          figures: ["fig-2"],
          citations: ["14", "15", "16"],
        },
        {
          id: "p-single-3",
          text:
            "Unsupervised clustering revealed three specific firing patterns: early activation, suppression and late activation (Fig. 2e-g and Extended Data Fig. 4). Components 1 and 3 were dominated by regular-spiking cell types, whereas the suppression component had relatively more fast-spiking cells.",
          figures: ["fig-2", "ext-4"],
          citations: ["45", "46", "47"],
        },
      ],
    },
    {
      id: "results-microcircuits",
      title: "Cellular-laminar microcircuits for IEDs",
      paragraphs: [
        {
          id: "p-circuit-1",
          text:
            "Neurons across neocortical depth showed varying peak activation times from -300 to 300 ms relative to IED maximal slope (Fig. 2j). Each of the three neuronal firing patterns was found across cortical depth, but early-activation neurons were more concentrated superficially (Fig. 2l,m).",
          figures: ["fig-2"],
          citations: [],
        },
        {
          id: "p-circuit-2",
          text:
            "The authors computed IED-aligned average firing rate patterns as a three-dimensional dynamic trajectory (Fig. 3a,b). Up to 1,000 ms before the IED, firing of suppression neurons decreased, suggesting an antecedent change in inhibitory dynamics.",
          figures: ["fig-3"],
          citations: ["18", "20", "48"],
        },
        {
          id: "p-circuit-3",
          text:
            "This prototype keeps the main figure, extended data and supplementary material in the same rail, which is the reading behavior we want to generalize across journals.",
          figures: ["fig-3", "supp-1"],
          citations: [],
        },
        {
          id: "p-circuit-4",
          text:
            "Cross-correlation analyses suggested that even neurons assigned to the same functional component did not behave as a perfectly synchronous block (Fig. 3d,e and Extended Data Fig. 5). Additional sorting by peak activation time emphasized asynchronous firing within each component (Extended Data Fig. 6).",
          figures: ["fig-3", "ext-5", "ext-6"],
          citations: ["49"],
        },
        {
          id: "p-circuit-5",
          text:
            "Time-lagged models connected neuronal firing to IED features including amplitude and slow-wave structure. Example neurons and coding summaries appear in Fig. 3f-m, with supporting examples in Extended Data Fig. 7 and Extended Data Fig. 8.",
          figures: ["fig-3", "ext-7", "ext-8"],
          citations: ["50", "51", "52"],
        },
      ],
    },
    {
      id: "results-cognition",
      title: "Neurocognitive correlates of IED generation circuit",
      paragraphs: [
        {
          id: "p-cognition-1",
          text:
            "The paper then asks whether neurons recruited during IEDs also participate in normal cognitive processing. Spike-field coherence analyses showed that IED-modulated neurons were more coupled to low-frequency oscillations, especially early-activation neurons (Fig. 4a-f).",
          figures: ["fig-4"],
          citations: ["55", "56", "57", "58"],
        },
        {
          id: "p-cognition-2",
          text:
            "The authors connect this physiological coupling to IED amplitude coding, with additional support from Extended Data Fig. 9. This is a useful stress test for the reader because the same conceptual thread points backward to Fig. 3 and sideways to an extended data figure.",
          figures: ["fig-3", "fig-4", "ext-9"],
          citations: ["48"],
        },
        {
          id: "p-cognition-3",
          text:
            "During a speech perception task, many neurons that were modulated by IEDs also encoded acoustic-phonetic information. Fig. 5 summarizes shared neuronal substrates across IED modulation and cognitive encoding.",
          figures: ["fig-5"],
          citations: ["59", "60"],
        },
        {
          id: "p-cognition-4",
          text:
            "The overlap between IED-modulated neurons and task-encoding neurons provides a possible cellular basis for transient cognitive impairment: the same neurons needed for ongoing computation can be diverted into pathological discharge dynamics (Fig. 5c-f).",
          figures: ["fig-5"],
          citations: ["26", "27", "54"],
        },
      ],
    },
    {
      id: "results-prediction",
      title: "Antecedent IED prediction",
      paragraphs: [
        {
          id: "p-prediction-1",
          text:
            "The final results section evaluates whether IEDs can be detected before they are obvious on macroelectrode recordings. ECoG and Neuropixels line-length models establish a baseline for prediction from field potentials (Fig. 6a,b).",
          figures: ["fig-6"],
          citations: ["61", "62"],
        },
        {
          id: "p-prediction-2",
          text:
            "Single-neuron firing produced earlier predictive signals than the LFP-only line-length approach, with suppression neurons contributing strongly to the decoder (Fig. 6c-h). This part is a good test of whether the rail keeps a large, multi-panel figure readable while the text continues.",
          figures: ["fig-6"],
          citations: ["33", "63", "64", "65"],
        },
        {
          id: "p-prediction-3",
          text:
            "The same predictive framing was extended to pathological IED features, including whether an event would remain isolated or become part of a series and whether an upcoming IED would have low or high amplitude (Fig. 6i-n and Extended Data Fig. 10).",
          figures: ["fig-6", "ext-10"],
          citations: ["51", "66", "67"],
        },
      ],
    },
    {
      id: "discussion",
      title: "Discussion",
      paragraphs: [
        {
          id: "p-discussion-1",
          text:
            "The discussion reframes the main result: human IEDs are not simply abrupt synchronous bursts but structured, asynchronous cellular-laminar events that tile a long peri-IED interval. Fig. 2 and Fig. 3 are the main anchors for this claim.",
          figures: ["fig-2", "fig-3"],
          citations: ["14", "15", "16", "23"],
        },
        {
          id: "p-discussion-2",
          text:
            "The clinical implication is that future neurostimulation might shift from reactive stimulation after a detected discharge toward proactive stimulation informed by antecedent single-neuron signatures (Fig. 6).",
          figures: ["fig-6"],
          citations: ["68", "69", "70"],
        },
        {
          id: "p-discussion-3",
          text:
            "The authors also emphasize limitations: small intraoperative cohorts, sampling constrained to epileptogenic lateral temporal neocortex, uncertainty about propagation versus local generation, and the need for future simultaneous high-density recordings.",
          figures: ["fig-1", "ext-1"],
          citations: ["75", "76", "77"],
        },
        {
          id: "p-discussion-4",
          text:
            "For this reader prototype, the full-paper flow now exercises recurring figures, backward references, extended data, supplementary material and a long end-to-end scroll, which is closer to the real use case than the initial short demo.",
          figures: ["fig-1", "fig-3", "fig-6", "supp-1"],
          citations: [],
        },
      ],
    },
  ],
  figures: [
    {
      id: "fig-1",
      label: "Fig. 1",
      type: "Main figure",
      title:
        "Neocortical neuron firing rates across depth are modulated immediately before, during and after local IEDs.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig1_HTML.png",
      caption:
        "Neuropixels probe placement, IED traces, neuron waveforms and example neurons across neocortical depth. Relevant when the text introduces recording geometry, IED detection and Fig. 1 panels.",
    },
    {
      id: "fig-2",
      label: "Fig. 2",
      type: "Main figure",
      title: "Peri-IED firing patterns of single neurons across neocortical depth.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig2_HTML.png",
      caption:
        "Proportions of modulated neurons, normalized peri-event time histograms, firing-pattern clusters and depth relationships.",
    },
    {
      id: "fig-3",
      label: "Fig. 3",
      type: "Main figure",
      title:
        "Cellular-laminar microcircuits for IED generation based on excitatory-inhibitory dynamics.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig3_HTML.png",
      caption:
        "Dynamic trajectory view of firing patterns and their relationship to IED prediction and amplitude coding.",
    },
    {
      id: "fig-4",
      label: "Fig. 4",
      type: "Main figure",
      title: "Spike-field coherence of IED microcircuits.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig4_HTML.png",
      caption:
        "Spike-field coherence across neurons, frequency bands, firing-pattern components and neocortical depth.",
    },
    {
      id: "fig-5",
      label: "Fig. 5",
      type: "Main figure",
      title: "Shared neuronal substrates for IEDs and cognition.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig5_HTML.png",
      caption:
        "Speech task encoding and overlap between neurons modulated by IEDs and neurons involved in ongoing cognitive processing.",
    },
    {
      id: "fig-6",
      label: "Fig. 6",
      type: "Main figure",
      title: "Predicting IEDs and their pathological features from single-neuron activity.",
      image:
        "https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig6_HTML.png",
      caption:
        "Prediction of IED occurrence, series formation and amplitude features from LFP line length and neuronal firing.",
    },
    {
      id: "ext-1",
      label: "Extended Data Fig. 1",
      type: "Extended data",
      title: "Characteristics of IED LFP waveforms across recording sites.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig7_ESM.jpg",
      caption:
        "Waveform heterogeneity, k-means clustering, raw IED waveforms, average IED waveforms and current source density summaries.",
    },
    {
      id: "ext-2",
      label: "Extended Data Fig. 2",
      type: "Extended data",
      title: "Unsupervised clustering of spatiotemporal neuronal spike waveforms.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig8_ESM.jpg",
      caption:
        "UMAP embedding, waveform clusters, trough-peak timing and examples of positive-spiking neurons.",
    },
    {
      id: "ext-3",
      label: "Extended Data Fig. 3",
      type: "Extended data",
      title: "Additional examples of single-neuron firing aligned to IEDs.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig9_ESM.jpg",
      caption:
        "Additional rasters and peri-event time histograms that reinforce the temporal heterogeneity described beside Fig. 2.",
    },
    {
      id: "ext-4",
      label: "Extended Data Fig. 4",
      type: "Extended data",
      title: "Number of firing rate clusters using K-means algorithm.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig10_ESM.jpg",
      caption:
        "Cluster count diagnostics supporting the three firing-pattern components used in the main analysis.",
    },
    {
      id: "ext-5",
      label: "Extended Data Fig. 5",
      type: "Extended data",
      title: "Cross-correlations within suppression and late excitatory neurons.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig11_ESM.jpg",
      caption:
        "Cross-correlograms among neurons within firing-pattern components, supporting the asynchronous microcircuit interpretation.",
    },
    {
      id: "ext-6",
      label: "Extended Data Fig. 6",
      type: "Extended data",
      title: "Asynchronous neuronal firing within activation pattern components.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig12_ESM.jpg",
      caption:
        "Sorted component firing rates showing variance in activation timing within early, suppression and late-activation components.",
    },
    {
      id: "ext-7",
      label: "Extended Data Fig. 7",
      type: "Extended data",
      title: "Additional examples of neurons coding IED amplitude.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig13_ESM.jpg",
      caption:
        "Example neurons with firing differences between high-amplitude and low-amplitude IEDs.",
    },
    {
      id: "ext-8",
      label: "Extended Data Fig. 8",
      type: "Extended data",
      title: "Coding of fast and slow components of IEDs.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig14_ESM.jpg",
      caption:
        "LFP slope-triggered averages and relationships between firing groups and slow-wave components.",
    },
    {
      id: "ext-9",
      label: "Extended Data Fig. 9",
      type: "Extended data",
      title: "Correlation between amplitude coding and spike-field coherence.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig15_ESM.jpg",
      caption:
        "Relationship between spike-field coherence and IED amplitude coding, grouped by component firing pattern.",
    },
    {
      id: "ext-10",
      label: "Extended Data Fig. 10",
      type: "Extended data",
      title: "LFP characteristics of series and isolated IED.",
      image:
        "https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41593-026-02258-4/MediaObjects/41593_2026_2258_Fig16_ESM.jpg",
      caption:
        "LFP heat maps and averages for isolated versus series IEDs, supporting the prediction analysis.",
    },
    {
      id: "supp-1",
      label: "Supplementary Fig. 1",
      type: "Supplementary figure",
      title: "Characteristic LFP signal at the pial surface.",
      image: "./assets/supplementary-fig-1-graph.png",
      sourceUrl: "./assets/41593_2026_2258_MOESM1_ESM.pdf",
      caption:
        "Extracted from the supplementary PDF. Shown is the LFP from a recording segment with P1-S1, marking the pial-saline interface at the cortical surface.",
    },
  ],
  references: {
    1: "World Health Organization. Epilepsy fact sheet.",
    2: "Fisher et al. Operational classification of seizure types.",
    3: "Clinical localization work connecting IEDs and epileptogenic tissue.",
    4: "Evidence linking IEDs with cognitive comorbidities.",
    5: "Additional evidence on cognitive effects of interictal activity.",
    8: "Closed-loop responsive neurostimulation clinical background.",
    14: "Prior animal-model work on paroxysmal depolarization mechanisms.",
    17: "Human microelectrode study showing heterogeneous neuronal firing patterns.",
    35: "Neuropixels-related recording protocol reference.",
    45: "Fast-spiking / inhibitory neuron waveform reference.",
  },
};

let article = null;

const state = {
  activeParagraphId: null,
  activeParagraphIndex: -1,
  activeFigures: new Set(),
  primaryFigureId: null,
  activeMentionByFigure: {},
  pinnedFigures: new Set(),
  nearestFigureId: null,
  syncFigures: true,
  programmaticFigureScroll: false,
  figureRailScrollSettleTimer: null,
  programmaticTextScrollUntil: 0,
  activeSelectionQueued: false,
  panByFigure: {},
  failedImages: new Set(),
  openLegendFigures: new Set(),
  zoom: 1,
  aiContext: null,
  aiRegionModeFigureId: null,
  aiSelectionRect: null,
  aiSelectionTimer: null,
  aiConversation: [],
  lastAiQuestion: "",
  lastAiAnswer: "",
  user: null,
  savedPapers: [],
  currentPaperId: null,
  currentNotes: [],
};

const elements = {
  form: document.querySelector("#paper-form"),
  url: document.querySelector("#paper-url"),
  article: document.querySelector("#article"),
  figureRail: document.querySelector(".figure-rail"),
  figureList: document.querySelector("#figure-list"),
  zoom: document.querySelector("#figure-zoom"),
  sync: document.querySelector("#sync-figures"),
  supplementPdf: document.querySelector("#supplement-pdf"),
  uploadSupplement: document.querySelector("#upload-supplement"),
  activeContext: document.querySelector("#active-context"),
  activeMentions: document.querySelector("#active-mentions"),
  metadata: document.querySelector("#metadata"),
  outlineTitle: document.querySelector("#outline-title"),
  sectionNav: document.querySelector("#section-nav"),
  popover: document.querySelector("#reference-popover"),
  imageViewer: document.querySelector("#image-viewer"),
  imageViewerTitle: document.querySelector("#image-viewer-title"),
  imageViewerImg: document.querySelector("#image-viewer-img"),
  imageViewerClose: document.querySelector("#image-viewer-close"),
  aiSelectionToolbar: document.querySelector("#ai-selection-toolbar"),
  aiSelectionAsk: document.querySelector("#ai-selection-ask"),
  aiPanel: document.querySelector("#ai-panel"),
  aiClose: document.querySelector("#ai-close"),
  aiContextTitle: document.querySelector("#ai-context-title"),
  aiContextPreview: document.querySelector("#ai-context-preview"),
  aiRegionPreview: document.querySelector("#ai-region-preview"),
  aiScope: document.querySelector("#ai-scope"),
  aiQuestion: document.querySelector("#ai-question"),
  aiAsk: document.querySelector("#ai-ask"),
  aiCopy: document.querySelector("#ai-copy"),
  aiSave: document.querySelector("#ai-save"),
  aiAnswer: document.querySelector("#ai-answer"),
  aiAnswerStatus: document.querySelector("#ai-answer-status"),
  accountBar: document.querySelector("#account-bar"),
  libraryPanel: document.querySelector("#library-panel"),
  libraryClose: document.querySelector("#library-close"),
  libraryList: document.querySelector("#library-list"),
  notesPanel: document.querySelector("#notes-panel"),
  notesClose: document.querySelector("#notes-close"),
  notesTitle: document.querySelector("#notes-title"),
  noteText: document.querySelector("#note-text"),
  saveNote: document.querySelector("#save-note"),
  notesList: document.querySelector("#notes-list"),
};

let mentionIndex = {};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function figureNumber(figure) {
  const match = figure.label.match(/(\d+)/);
  return match ? match[1] : null;
}

function figureMentionRegex(figure) {
  const number = figureNumber(figure);
  if (!number) return new RegExp(`${escapeRegExp(figure.label)}(?:[a-z](?:[,-][a-z])?)?`, "gi");
  const elifeSupplement = figure.label.match(/Figure\s+(\d+)\s*[\u2013\u2014-]\s*figure\s+supplement\s+(\d+)/i);
  if (figure.id.startsWith("table-")) {
    return new RegExp(`Tables?\\s*${number}`, "gi");
  }
  if (figure.id.startsWith("ext-")) {
    return new RegExp(`Extended\\s+Data\\s+(?:Fig\\.?\\s*)?${number}(?:[a-z](?:[,-][a-z])?)?`, "gi");
  }
  if (elifeSupplement) {
    return new RegExp(
      `Figure\\s*${elifeSupplement[1]}\\s*[\\u2013\\u2014-]\\s*figure\\s+supplement\\s+${elifeSupplement[2]}(?:[a-z](?:[,-][a-z])?)?`,
      "gi",
    );
  }
  if (figure.id.startsWith("supp-")) {
    return new RegExp(`(?:(?:Supplementary|Supp\\.?)\\s*Fig(?:ure)?\\.?\\s*${number}|Fig\\.?\\s*S${number}|Figure\\s*S${number})(?:[a-z](?:[,-][a-z])?)?`, "gi");
  }
  return new RegExp(`(?:Fig\\.?|Figure)\\s*${number}(?:[a-z](?:[,-][a-z])?)?`, "gi");
}

function isMainFigureMention(text, index) {
  const prefix = text.slice(Math.max(0, index - 24), index).toLowerCase();
  return !/(extended\s+data|supplementary|supp\.?)\s*$/.test(prefix);
}

function mentionPriority(figure) {
  if (figure.id.startsWith("ext-")) return 0;
  if (figure.id.startsWith("supp-")) return 1;
  if (figure.id.startsWith("table-")) return 3;
  return 2;
}

function rangesOverlap(a, b) {
  return a.start < b.end && b.start < a.end;
}

function addRange(ranges, range) {
  if (ranges.some((existing) => rangesOverlap(existing, range))) return;
  ranges.push(range);
}

function addGroupedMainFigureRanges(ranges, text) {
  const groupRegex =
    /\b(?:(?:Supplementary|Supp\.?)\s*Fig(?:ure)?s?\.?|Figs\.|Figures?)\s*((?:S?\d+[a-z]?(?:\s*[\u2013-]\s*(?:S?\d+)?[a-z]?)?)(?:\s*(?:,|and)\s*S?\d+[a-z]?(?:\s*[\u2013-]\s*(?:S?\d+)?[a-z]?)?)*)/gi;
  let groupMatch;
  while ((groupMatch = groupRegex.exec(text))) {
    const afterGroup = text.slice(groupMatch.index + groupMatch[0].length, groupMatch.index + groupMatch[0].length + 40);
    if (/^\s*[\u2013\u2014-]\s*figure\s+supplement/i.test(afterGroup)) continue;
    const groupText = groupMatch[1];
    const groupStart = groupMatch.index;
    const isSupplementGroup = /(?:supplementary|supp\.?)\s*fig/i.test(groupMatch[0]) || /^S/i.test(groupText.trim());
    const itemRegex = /S?\d+[a-z]?(?:\s*[\u2013-]\s*(?:S?\d+)?[a-z]?)?/gi;
    let itemMatch;
    let itemIndex = 0;
    while ((itemMatch = itemRegex.exec(groupText))) {
      const token = itemMatch[0];
      const number = token.match(/\d+/)?.[0];
      const figureId = isSupplementGroup || /^S/i.test(token) ? `supp-${number}` : `fig-${number}`;
      const figure = article.figures.find((candidate) => candidate.id === figureId);
      if (!figure) continue;
      const itemStart = groupStart + groupMatch[0].indexOf(groupText) + itemMatch.index;
      addRange(ranges, {
        start: itemIndex === 0 ? groupStart : itemStart,
        end: itemStart + itemMatch[0].length,
        type: "figure",
        figureId: figure.id,
      });
      itemIndex += 1;
    }
  }
}

function collectFigureMentionRanges(text, figureIds = null) {
  const ranges = [];
  addGroupedMainFigureRanges(ranges, text);
  const candidateFigures = figureIds
    ? [...new Set(figureIds)]
        .map((id) => article.figures.find((figure) => figure.id === id))
        .filter(Boolean)
    : [...article.figures];
  const figures = candidateFigures
    .sort(
      (a, b) =>
        mentionPriority(a) - mentionPriority(b) ||
        b.label.length - a.label.length,
    );

  figures.forEach((figure) => {
    const regex = figureMentionRegex(figure);
    let match;
    while ((match = regex.exec(text))) {
      if (figure.id.startsWith("fig-") && !isMainFigureMention(text, match.index)) continue;
      addRange(ranges, {
        start: match.index,
        end: match.index + match[0].length,
        type: "figure",
        figureId: figure.id,
      });
    }
  });
  return ranges;
}

function collectCitationRanges(paragraph, text) {
  const ranges = [];
  const seen = new Set();

  (paragraph.citations || []).forEach((citation) => {
    if (typeof citation !== "object" || !citation.text || !citation.key) return;
    const key = String(citation.key);
    const label = String(citation.text);
    const marker = `${key}:${label}`;
    if (seen.has(marker)) return;
    seen.add(marker);
    const regex = new RegExp(escapeRegExp(label), "g");
    let match;
    while ((match = regex.exec(text))) {
      addRange(ranges, {
        start: match.index,
        end: match.index + match[0].length,
        type: "citation",
        citations: key,
      });
    }
  });

  let citationMatch;
  const citationRegex = /\[(\d+(?:,\d+)*)\]/g;
  while ((citationMatch = citationRegex.exec(text))) {
    addRange(ranges, {
      start: citationMatch.index,
      end: citationMatch.index + citationMatch[0].length,
      type: "citation",
      citations: citationMatch[1],
    });
  }

  return ranges;
}

function renderInlineText(paragraph) {
  if (paragraph.kind === "equation" && paragraph.html) {
    return paragraph.html;
  }

  const text = paragraph.text || "";
  const ranges = collectFigureMentionRanges(text);
  collectCitationRanges(paragraph, text).forEach((range) => addRange(ranges, range));

  let formulaMatch;
  const formulaRegex = /\{\{formula:([^}]+)\}\}/g;
  while ((formulaMatch = formulaRegex.exec(text))) {
    addRange(ranges, {
      start: formulaMatch.index,
      end: formulaMatch.index + formulaMatch[0].length,
      type: "formula",
      url: formulaMatch[1],
    });
  }

  ranges.sort((a, b) => a.start - b.start || b.end - a.end);
  let cursor = 0;
  let output = "";
  ranges.forEach((range) => {
    output += escapeHtml(text.slice(cursor, range.start));
    const value = escapeHtml(text.slice(range.start, range.end));
    if (range.type === "figure") {
      output += `<button class="mention" data-figure="${range.figureId}">${value}</button>`;
    } else if (range.type === "citation") {
      output += `<button class="citation" data-citations="${range.citations}">${value}</button>`;
    } else if (range.type === "formula") {
      output += `<span class="inline-formula-shell"><img class="inline-formula" src="${escapeHtml(range.url)}" alt="Formula" loading="lazy" /></span>`;
    }
    cursor = range.end;
  });
  output += escapeHtml(text.slice(cursor));
  return output;
}

function notesForAnchor(anchorType, anchorId) {
  return state.currentNotes.filter((note) =>
    note.anchorType === anchorType &&
    (anchorType === "paragraph" ? note.paragraphId === anchorId : note.figureId === anchorId),
  );
}

function renderAnchorNotes(anchorType, anchorId) {
  const notes = notesForAnchor(anchorType, anchorId);
  if (!notes.length) return "";
  return `
    <button
      type="button"
      class="note-anchor"
      data-open-anchor-notes="${anchorType}:${anchorId}"
      title="${notes.length} saved note${notes.length === 1 ? "" : "s"}"
    >${notes.length}</button>
  `;
}

function renderArticle() {
  if (!article) return;
  elements.outlineTitle.textContent = article.title;
  elements.metadata.innerHTML = `
    <span>${escapeHtml(article.journal)}</span>
    <span>Published ${escapeHtml(article.published)}</span>
    <span>DOI ${escapeHtml(article.doi)}</span>
  `;

  elements.sectionNav.innerHTML = article.sections
    .map((section) => `<a href="#${section.id}">${escapeHtml(section.title)}</a>`)
    .join("");

  const sections = article.sections
    .map((section) => {
      const paragraphs = section.paragraphs
        .map(
          (paragraph) => `
            <p
              id="${paragraph.id}"
              class="paragraph${paragraph.kind === "equation" ? " paragraph--equation" : ""}"
              data-section="${section.id}"
              data-figures="${paragraph.figures.join(",")}"
            >${renderInlineText(paragraph)}${renderAnchorNotes("paragraph", paragraph.id)}</p>
          `,
        )
        .join("");

      return `
        <section id="${section.id}" class="section" data-section-id="${section.id}">
          <h2>${escapeHtml(section.title)}</h2>
          ${paragraphs}
        </section>
      `;
    })
    .join("");

  elements.article.innerHTML = `
    <header class="article-header">
      <p class="eyebrow">${escapeHtml(article.journal)}</p>
      <h1>${escapeHtml(article.title)}</h1>
      <p class="authors">${escapeHtml(article.authors)}</p>
    </header>
    ${sections}
  `;

  let mathStyle = document.querySelector("#article-math-styles");
  if (!mathStyle) {
    mathStyle = document.createElement("style");
    mathStyle.id = "article-math-styles";
    document.head.appendChild(mathStyle);
  }
  mathStyle.textContent = article.mathStyles || "";
}

function renderStartPage() {
  document.body.classList.add("is-start");
  elements.url.value = "";
  elements.outlineTitle.textContent = "No paper loaded";
  elements.metadata.innerHTML = "";
  elements.sectionNav.innerHTML = "";
  elements.activeContext.textContent = "No paper loaded";
  elements.activeMentions.innerHTML = "";
  elements.figureList.innerHTML = "";
  elements.article.innerHTML = `
    <section class="start-page" aria-labelledby="start-title">
      <div class="start-mark" aria-hidden="true">SR</div>
      <h1 id="start-title">SciReader</h1>
      <p>Paste a Nature, Cell Press, bioRxiv, eLife, or Science URL to build a synchronized text, figure, supplement and reference reader.</p>
      <div id="start-account" class="start-account"></div>
      <form id="start-form" class="start-form">
        <input
          id="start-paper-url"
          type="url"
          placeholder="https://www.science.org/doi/10.1126/science.aea6425"
          aria-label="Paper URL"
          required
        />
        <button type="submit">Load paper</button>
      </form>
    </section>
  `;
  renderAccountBar();
  window.setTimeout(() => document.querySelector("#start-paper-url")?.focus(), 0);
}

function figureMentionCount(figureId) {
  return mentionIndex[figureId]?.length || 0;
}

function buildMentionIndex(sourceArticle) {
  const index = {};
  sourceArticle.sections.forEach((section) => {
    section.paragraphs.forEach((paragraph) => {
      paragraph.figures.forEach((figureId) => {
        if (!index[figureId]) index[figureId] = [];
        index[figureId].push({
          figureId,
          paragraphId: paragraph.id,
          sectionId: section.id,
          sectionTitle: section.title,
          text: paragraph.text,
        });
      });
    });
  });
  return index;
}

function normalizeArticle(source) {
  const safeSource = source || {};
  return {
    sourceUrl: safeSource.sourceUrl || "",
    title: safeSource.title || "Untitled article",
    journal: safeSource.journal || "Unknown journal",
    published: safeSource.published || "unknown date",
    doi: safeSource.doi || "unknown",
    authors: safeSource.authors || "Authors unavailable",
    cacheKey: safeSource.cacheKey || "",
    sourceFamily: safeSource.sourceFamily || "",
    mathStyles: safeSource.mathStyles || "",
    sections: (safeSource.sections || []).map((section, sectionIndex) => ({
      id: section.id || `section-${sectionIndex + 1}`,
      title: section.title || `Section ${sectionIndex + 1}`,
      paragraphs: (section.paragraphs || []).map((paragraph, paragraphIndex) => ({
        id: paragraph.id || `p-${sectionIndex + 1}-${paragraphIndex + 1}`,
        text: paragraph.text || "",
        kind: paragraph.kind || "text",
        html: paragraph.html || "",
        figures: Array.isArray(paragraph.figures) ? paragraph.figures : [],
        citations: Array.isArray(paragraph.citations)
          ? paragraph.citations
              .map((citation) => {
                if (typeof citation === "object" && citation !== null) {
                  return {
                    key: String(citation.key || ""),
                    text: String(citation.text || ""),
                  };
                }
                return String(citation);
              })
              .filter((citation) => typeof citation === "string" || (citation.key && citation.text))
          : [],
      })),
    })),
    figures: (safeSource.figures || []).map((figure, index) => ({
      id: figure.id || `figure-${index + 1}`,
      label: figure.label || `Figure ${index + 1}`,
      type: figure.type || "Figure",
      title: figure.title || "",
      image: figure.image || "",
      sourceUrl: figure.sourceUrl || "",
      caption: figure.caption || "",
    })),
    references: safeSource.references || {},
  };
}

function resetReaderState() {
  state.activeParagraphId = null;
  state.activeParagraphIndex = -1;
  state.activeFigures = new Set();
  state.primaryFigureId = null;
  state.activeMentionByFigure = {};
  state.pinnedFigures = new Set();
  state.nearestFigureId = null;
  state.programmaticFigureScroll = false;
  window.clearTimeout(state.figureRailScrollSettleTimer);
  state.figureRailScrollSettleTimer = null;
  state.programmaticTextScrollUntil = 0;
  state.activeSelectionQueued = false;
  state.panByFigure = {};
  state.failedImages = new Set();
  state.openLegendFigures = new Set();
  state.zoom = 1;
  state.aiContext = null;
  state.aiRegionModeFigureId = null;
  state.aiSelectionRect = null;
  state.currentPaperId = null;
  state.currentNotes = [];
  elements.aiSelectionToolbar.hidden = true;
  closeAiPanel();
  elements.notesPanel.hidden = true;
  elements.zoom.value = 100;
  elements.figureList.scrollTop = 0;
}

function loadArticle(nextArticle, { updateUrl = true } = {}) {
  article = normalizeArticle(nextArticle);
  mentionIndex = buildMentionIndex(article);
  resetReaderState();
  document.body.classList.remove("is-start");
  if (updateUrl && article.sourceUrl) elements.url.value = article.sourceUrl;
  renderArticle();
  renderFigures();
  renderActiveMentions();
  renderAccountBar();
  elements.popover.hidden = true;
  closeImageViewer();
  window.history.replaceState(null, "", window.location.pathname);
  window.scrollTo({ top: 0, behavior: "auto" });
  window.setTimeout(() => {
    selectActiveParagraph();
    const firstFigure = article.figures[0];
    if (firstFigure) scrollFigureIntoView(firstFigure.id, "auto");
  }, 0);
}

function figureCaptionBody(figure) {
  const caption = String(figure.caption || "").replace(/\s+/g, " ").trim();
  if (!caption) return "";
  const title = String(figure.title || "").replace(/\s+/g, " ").trim();
  const labels = [
    figure.label,
    figure.label.replace(/^Fig\./i, "Figure"),
    figure.label.replace(/^Figure/i, "Fig."),
  ]
    .map((label) => String(label || "").replace(/\s+/g, " ").trim())
    .filter(Boolean);

  for (const label of labels) {
    let pattern = new RegExp(`^${escapeRegExp(label)}\\s*[:.]?\\s*`, "i");
    let next = caption.replace(pattern, "").trim();
    if (title && next !== caption) {
      next = next.replace(new RegExp(`^${escapeRegExp(title)}\\s*[:.]?\\s*`, "i"), "").trim();
    }
    if (next !== caption && next) return next;
  }
  if (title) {
    const next = caption.replace(new RegExp(`^${escapeRegExp(title)}\\s*[:.]?\\s*`, "i"), "").trim();
    if (next && next !== caption) return next;
  }
  return caption;
}

function normalizeLegendPanelKey(label) {
  return String(label || "")
    .replace(/\s+and\s+/gi, "+")
    .replace(/[\u2010-\u2015]/g, "-")
    .replace(/\s+/g, "");
}

function legendSegments(figure) {
  const body = figureCaptionBody(figure);
  const panelLabel = "[A-Z](?:\\s*(?:,|and|&|\\+|\\/|[\\u2010-\\u2015-])\\s*[A-Z])*";
  const pattern = new RegExp(`(^|[.;:]\\s+)(?:\\((${panelLabel})\\)|(${panelLabel})\\))`, "g");
  const matches = [...body.matchAll(pattern)].map((match) => {
    const label = match[2] || match[3] || "";
    const labelStart = match.index + match[1].length;
    const labelText = body.slice(labelStart, labelStart + match[0].length - match[1].length);
    return {
      index: labelStart,
      end: labelStart + labelText.length,
      label: labelText,
      key: normalizeLegendPanelKey(label),
    };
  });
  if (!matches.length) return { intro: "", segments: [], body };

  const seenKeys = new Set();
  const panelMatches = matches
    .filter((item) => {
      if (seenKeys.has(item.key)) return false;
      seenKeys.add(item.key);
      return true;
    });
  const intro = body.slice(0, panelMatches[0].index).trim();
  const segments = panelMatches.map((item, index) => {
    const start = item.end;
    const end = index + 1 < panelMatches.length ? panelMatches[index + 1].index : body.length;
    return {
      key: item.key,
      label: item.label,
      text: body.slice(start, end).trim(),
    };
  });
  return { intro, segments, body };
}

function renderLegendChips(figure, segments) {
  if (!segments.length) return "";
  const buttons = segments
    .slice(0, 14)
    .map(
      (segment) =>
        `<button type="button" class="legend-chip" data-legend-panel="${escapeHtml(segment.key)}" data-legend-figure="${figure.id}" title="Show ${escapeHtml(segment.label)} legend">${escapeHtml(segment.key)}</button>`,
    )
    .join("");
  return `<div class="legend-chip-list" aria-label="${escapeHtml(figure.label)} legend panels">${buttons}</div>`;
}

function renderLegendDrawerContent(figure, details) {
  if (details.segments.length) {
    const intro = details.intro ? `<p class="legend-intro">${escapeHtml(details.intro)}</p>` : "";
    const segments = details.segments
      .map(
        (segment) => `
          <div class="legend-segment" data-legend-segment="${escapeHtml(segment.key)}">
            <span class="legend-segment-label">${escapeHtml(segment.label)}</span>
            <p>${escapeHtml(segment.text)}</p>
          </div>
        `,
      )
      .join("");
    return `${intro}${segments}`;
  }
  return `<p class="legend-intro">${escapeHtml(details.body || figure.caption || "No legend available.")}</p>`;
}

function renderLegendBlock(figure) {
  const details = legendSegments(figure);
  const body = details.body || figure.caption || "";
  const preview = truncateText(body, 260);
  const isOpen = state.openLegendFigures.has(figure.id);
  return `
    <div class="legend-shell">
      <div class="legend-preview">
        <p class="caption caption-preview">${escapeHtml(preview || "No legend available.")}</p>
        <div class="legend-controls">
          ${renderLegendChips(figure, details.segments)}
          <button
            type="button"
            class="legend-toggle"
            data-toggle-legend="${figure.id}"
            aria-expanded="${isOpen ? "true" : "false"}"
            aria-controls="legend-drawer-${figure.id}"
          >${isOpen ? "Hide legend" : "Legend"}</button>
        </div>
      </div>
      <div id="legend-drawer-${figure.id}" class="legend-drawer" ${isOpen ? "" : "hidden"}>
        <div class="legend-drawer__head">
          <span>Full legend</span>
          <button type="button" class="legend-close" data-toggle-legend="${figure.id}" aria-expanded="${isOpen ? "true" : "false"}">Close</button>
        </div>
        ${renderLegendDrawerContent(figure, details)}
      </div>
    </div>
  `;
}

function renderFigures() {
  elements.figureList.innerHTML = article.figures
    .map((figure) => {
      const image = figure.image
        ? `<img src="${figure.image}" alt="${escapeHtml(figure.title)}" loading="lazy" />`
        : `<div class="figure-fallback"><div><strong>${escapeHtml(figure.label)}</strong><span>${escapeHtml(figure.id.startsWith("table-") ? "Table card" : "Supplementary PDF extraction target")}</span></div></div>`;

      return `
        <section class="figure-card" data-figure-card="${figure.id}" style="--zoom:${state.zoom}; --pan-x:0px; --pan-y:0px">
          <header>
            <div>
              <h3>${escapeHtml(figure.label)}: ${escapeHtml(figure.title)}</h3>
              <span class="figure-type">${escapeHtml(figure.type)} | ${figureMentionCount(figure.id)} mention${figureMentionCount(figure.id) === 1 ? "" : "s"}</span>
            </div>
            ${renderAnchorNotes("figure", figure.id)}
            <button class="pin-button" data-pin="${figure.id}" title="Pin figure">Pin</button>
          </header>
          ${renderFigureMentionNav(figure)}
          <div class="figure-stage">${image}</div>
          ${renderLegendBlock(figure)}
          ${renderFigureActions(figure)}
        </section>
      `;
    })
    .join("");

  document.querySelectorAll(".figure-stage img").forEach(attachFigureImageHandlers);
  updateFigureCards();
}

function setLegendOpen(figureId, open, focusPanel = "") {
  const card = document.querySelector(`[data-figure-card="${figureId}"]`);
  if (!card) return;
  if (open) state.openLegendFigures.add(figureId);
  else state.openLegendFigures.delete(figureId);
  card.classList.toggle("is-legend-open", open);
  const drawer = card.querySelector(".legend-drawer");
  if (drawer) drawer.hidden = !open;
  card.querySelectorAll(`[data-toggle-legend="${figureId}"]`).forEach((button) => {
    button.setAttribute("aria-expanded", open ? "true" : "false");
    if (button.classList.contains("legend-close")) return;
    button.textContent = open ? "Hide legend" : "Legend";
  });
  if (!open || !focusPanel) return;
  window.setTimeout(() => {
    const segment = [...card.querySelectorAll("[data-legend-segment]")].find(
      (item) => item.dataset.legendSegment === focusPanel,
    );
    if (!segment) return;
    card.querySelectorAll(".legend-segment.is-focused").forEach((item) => {
      item.classList.remove("is-focused");
    });
    segment.classList.add("is-focused");
    segment.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, 0);
}

function renderFigureMentionNav(figure) {
  const mentions = mentionIndex[figure.id] || [];
  if (!mentions.length) return "";

  const buttons = mentions
    .map((mention, index) => {
      const label = index + 1;
      return `<button type="button" data-mention-target="${mention.paragraphId}" data-mention-figure="${figure.id}" title="${escapeHtml(mention.sectionTitle)} mention ${label}">${label}</button>`;
    })
    .join("");

  return `
    <div class="figure-mention-nav" data-mention-nav="${figure.id}">
      <span data-mention-status="${figure.id}">Mentions</span>
      <div>${buttons}</div>
    </div>
  `;
}

function createFigureFallback(figure) {
  const fallback = document.createElement("div");
  fallback.className = "figure-fallback";
  const isBiorxiv = article.sourceFamily === "biorxiv-direct" || article.sourceUrl.includes("biorxiv.org");
  const hint = figure.id.startsWith("table-")
    ? "Table content may open on the publisher page. Inline table extraction is limited for this paper."
    : isBiorxiv
    ? "Image unavailable. Open Publisher once to allow bioRxiv image access, then retry."
    : "Image unavailable. Use Open image to retry in the in-reader viewer.";
  fallback.innerHTML = `
    <div>
      <strong>${escapeHtml(figure.label)}</strong>
      <span>${escapeHtml(hint)}</span>
      ${figure.image ? `<button type="button" data-retry-image="${figure.id}">Retry image</button>` : ""}
    </div>
  `;
  return fallback;
}

function attachFigureImageHandlers(image) {
  image.addEventListener("load", () => {
    const card = image.closest("[data-figure-card]");
    if (!card) return;
    state.failedImages.delete(card.dataset.figureCard);
    setFigurePan(card, state.panByFigure[card.dataset.figureCard] || { x: 0, y: 0 });
  });
  image.addEventListener("error", () => {
    const card = image.closest("[data-figure-card]");
    if (!card) return;
    const figure = article.figures.find((item) => item.id === card.dataset.figureCard);
    state.failedImages.add(card.dataset.figureCard);
    image.replaceWith(createFigureFallback(figure));
  });
}

function retryFigureImage(figureId) {
  const figure = article.figures.find((item) => item.id === figureId);
  const card = document.querySelector(`[data-figure-card="${figureId}"]`);
  const stage = card?.querySelector(".figure-stage");
  if (!figure?.image || !stage) return;
  const image = document.createElement("img");
  image.src = figure.image;
  image.alt = figure.title;
  image.loading = "lazy";
  attachFigureImageHandlers(image);
  stage.replaceChildren(image);
}

function renderFigureActions(figure) {
  const actions = [];
  if (figure.image) {
    actions.push(
      `<button type="button" data-ask-region="${figure.id}">Ask region</button>`,
    );
  }
  if (figure.image) {
    actions.push(
      `<button type="button" data-open-image="${figure.id}">Open image</button>`,
    );
  }
  if (figure.sourceUrl) {
    const sourceLabel = /\.pdf(?:$|[?#])/i.test(figure.sourceUrl) ? "Source PDF" : "Publisher";
    actions.push(
      `<a href="${figure.sourceUrl}" target="_blank" rel="noreferrer">${sourceLabel}</a>`,
    );
  }
  return actions.length ? `<div class="figure-actions">${actions.join("")}</div>` : "";
}

function openImageViewer(figureId) {
  const figure = article.figures.find((item) => item.id === figureId);
  if (!figure || !figure.image) return;
  elements.imageViewerTitle.textContent = `${figure.label}: ${figure.title}`;
  elements.imageViewerImg.src = figure.image;
  elements.imageViewerImg.alt = figure.title;
  elements.imageViewer.hidden = false;
}

function closeImageViewer() {
  elements.imageViewer.hidden = true;
  elements.imageViewerImg.removeAttribute("src");
}

function renderActiveMentions() {
  const figures = [...state.activeFigures]
    .map((id) => article.figures.find((figure) => figure.id === id))
    .filter(Boolean);

  const nearest = article.figures.find((figure) => figure.id === state.nearestFigureId);
  const primary = article.figures.find((figure) => figure.id === state.primaryFigureId);
  elements.activeContext.textContent = primary
    ? primary.label
    : nearest
      ? `Next: ${nearest.label}`
      : "Reading";

  elements.activeMentions.innerHTML = figures
    .map(
      (figure) =>
        `<button data-jump-figure="${figure.id}">${escapeHtml(figure.label)}</button>`,
    )
    .join("");
}

function getBridgeFigureId(paragraph) {
  if (!paragraph) return null;
  const allParagraphs = [...document.querySelectorAll(".paragraph")];
  const startIndex = allParagraphs.indexOf(paragraph);
  const nextParagraph = allParagraphs[startIndex + 1];
  if (!nextParagraph || nextParagraph.dataset.section !== paragraph.dataset.section) {
    return null;
  }
  const figures = nextParagraph.dataset.figures
    ? nextParagraph.dataset.figures.split(",").filter(Boolean)
    : [];
  if (figures.length) return choosePrimaryFigureId(nextParagraph, figures, 1);
  return null;
}

function figureSortIndex(figureId) {
  const index = article.figures.findIndex((figure) => figure.id === figureId);
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}

function findFigureMentionPosition(text, figure) {
  const regex = figureMentionRegex(figure);
  let match;
  while ((match = regex.exec(text))) {
    if (!figure.id.startsWith("fig-") || isMainFigureMention(text, match.index)) {
      return match.index;
    }
  }
  return -1;
}

function choosePrimaryFigureId(paragraph, figures, direction) {
  if (!figures.length) return null;
  if (figures.length === 1) return figures[0];

  const text = paragraph.textContent;
  const positions = figures.map((id) => {
    const figure = article.figures.find((item) => item.id === id);
    const mentionPosition = figure ? findFigureMentionPosition(text, figure) : -1;
    return {
      id,
      index: figureSortIndex(id),
      mentionPosition: mentionPosition === -1 ? Number.MAX_SAFE_INTEGER : mentionPosition,
      isMainFigure: id.startsWith("fig-"),
    };
  });

  const previousPrimaryIndex = direction >= 0 && state.primaryFigureId
    ? figureSortIndex(state.primaryFigureId)
    : -1;
  const mainPositions = positions.filter((item) => item.isMainFigure);
  const forwardMain = mainPositions
    .filter((item) => item.isMainFigure && item.index >= previousPrimaryIndex)
    .sort((a, b) => b.index - a.index || b.mentionPosition - a.mentionPosition)[0];
  if (forwardMain) return forwardMain.id;
  if (mainPositions.length) {
    return mainPositions.sort(
      (a, b) => a.mentionPosition - b.mentionPosition || b.index - a.index,
    )[0].id;
  }

  const anyForward = positions
    .filter((item) => item.index >= previousPrimaryIndex)
    .sort((a, b) => b.index - a.index || b.mentionPosition - a.mentionPosition)[0];
  if (anyForward) return anyForward.id;

  return positions.sort((a, b) => b.mentionPosition - a.mentionPosition)[0].id;
}

function updateFigureCards() {
  document.querySelectorAll(".figure-card").forEach((card) => {
    const id = card.dataset.figureCard;
    const isActive = state.activeFigures.has(id);
    const isPinned = state.pinnedFigures.has(id);
    const pan = clampPanForCard(card, state.panByFigure[id] || { x: 0, y: 0 });
    state.panByFigure[id] = pan;
    card.classList.toggle("is-relevant", isActive);
    card.classList.toggle("is-pinned", isPinned);
    card.classList.toggle("is-nearest", !isActive && state.nearestFigureId === id);
    card.classList.toggle("is-zoomed", state.zoom > 1);
    card.style.setProperty("--zoom", state.zoom);
    card.style.setProperty("--pan-x", `${pan.x}px`);
    card.style.setProperty("--pan-y", `${pan.y}px`);
    const pinButton = card.querySelector("[data-pin]");
    if (pinButton) pinButton.textContent = isPinned ? "Unpin" : "Pin";

    const mentions = mentionIndex[id] || [];
    const activeIndex = mentions.findIndex(
      (mention) => mention.paragraphId === state.activeParagraphId,
    );
    const status = card.querySelector(`[data-mention-status="${id}"]`);
    if (status) {
      status.textContent =
        activeIndex === -1 ? `${mentions.length} mentions` : `${activeIndex + 1}/${mentions.length}`;
    }
    card.querySelectorAll("[data-mention-target]").forEach((button) => {
      button.classList.toggle(
        "is-active",
        button.dataset.mentionTarget === state.activeParagraphId,
      );
    });
  });
}

function clampPanForCard(card, pan) {
  const stage = card.querySelector(".figure-stage");
  const image = card.querySelector(".figure-stage img");
  if (!stage || !image) return { x: 0, y: 0 };

  const scaledWidth = image.offsetWidth * state.zoom;
  const scaledHeight = image.offsetHeight * state.zoom;
  const maxX = Math.max(0, scaledWidth - stage.clientWidth);
  const maxY = Math.max(0, scaledHeight - stage.clientHeight);
  const limitX = maxX / 2 + (maxX > 0 ? stage.clientWidth * 0.08 : 0);
  const limitY = maxY / 2 + (maxY > 0 ? stage.clientHeight * 0.08 : 0);
  return {
    x: Math.min(limitX, Math.max(-limitX, pan.x)),
    y: Math.min(limitY, Math.max(-limitY, pan.y)),
  };
}

function setFigurePan(card, pan) {
  const id = card.dataset.figureCard;
  const clamped = clampPanForCard(card, pan);
  state.panByFigure[id] = clamped;
  card.style.setProperty("--pan-x", `${clamped.x}px`);
  card.style.setProperty("--pan-y", `${clamped.y}px`);
}

function primaryFigureId() {
  return state.primaryFigureId || state.nearestFigureId;
}

function scrollCardWithinFigureRail(card, behavior = "smooth") {
  const listRect = elements.figureList.getBoundingClientRect();
  const cardRect = card.getBoundingClientRect();
  const targetTop = elements.figureList.scrollTop + cardRect.top - listRect.top - 8;
  state.programmaticFigureScroll = true;
  window.clearTimeout(state.figureRailScrollSettleTimer);
  state.figureRailScrollSettleTimer = window.setTimeout(() => {
    state.programmaticFigureScroll = false;
  }, behavior === "smooth" ? 900 : 180);
  elements.figureList.scrollTo({
    top: Math.max(0, targetTop),
    behavior,
  });
}

function syncFigureRailToActive({ force = false } = {}) {
  if (!state.syncFigures && !force) return;
  const figureId = primaryFigureId();
  const card = figureId ? document.querySelector(`[data-figure-card="${figureId}"]`) : null;
  if (!card) return;

  scrollCardWithinFigureRail(card, force ? "smooth" : "auto");
}

function updateActiveParagraph(paragraph) {
  if (!paragraph || state.activeParagraphId === paragraph.id) return;
  const allParagraphs = [...document.querySelectorAll(".paragraph")];
  const paragraphIndex = allParagraphs.indexOf(paragraph);
  const direction =
    state.activeParagraphIndex === -1 || paragraphIndex >= state.activeParagraphIndex ? 1 : -1;
  const previousFigureId = state.primaryFigureId || state.nearestFigureId;
  state.activeParagraphId = paragraph.id;
  state.activeParagraphIndex = paragraphIndex;
  const paragraphFigures = paragraph.dataset.figures
    ? paragraph.dataset.figures.split(",").filter(Boolean)
    : [];
  state.activeFigures = new Set(paragraphFigures);
  state.primaryFigureId = choosePrimaryFigureId(paragraph, paragraphFigures, direction);
  state.nearestFigureId = paragraphFigures.length
    ? null
    : getBridgeFigureId(paragraph) || previousFigureId;

  document
    .querySelectorAll(".paragraph")
    .forEach((node) => node.classList.toggle("is-active", node.id === paragraph.id));

  document.querySelectorAll(".section-nav a").forEach((link) => {
    const isActive = link.getAttribute("href") === `#${paragraph.dataset.section}`;
    link.classList.toggle("active", isActive);
    if (isActive) keepActiveOutlineLinkVisible(link);
  });

  renderActiveMentions();
  updateFigureCards();
  syncFigureRailToActive();
}

function keepActiveOutlineLinkVisible(link) {
  const outline = link.closest(".outline-sticky");
  if (!outline) return;
  const linkTop = link.offsetTop;
  const linkBottom = linkTop + link.offsetHeight;
  const visibleTop = outline.scrollTop + 72;
  const visibleBottom = outline.scrollTop + outline.clientHeight - 18;

  if (linkTop < visibleTop) {
    outline.scrollTo({ top: Math.max(0, linkTop - 72), behavior: "smooth" });
  } else if (linkBottom > visibleBottom) {
    outline.scrollTo({
      top: linkBottom - outline.clientHeight + 18,
      behavior: "smooth",
    });
  }
}

function selectActiveParagraph() {
  const paragraphs = [...document.querySelectorAll(".paragraph")];
  if (!paragraphs.length) return;

  const focusY = window.innerHeight * 0.42;
  const ranked = paragraphs
    .map((paragraph) => {
      const rect = paragraph.getBoundingClientRect();
      const containsFocus = rect.top <= focusY && rect.bottom >= focusY;
      const distance = containsFocus
        ? Math.abs(rect.top - focusY) * 0.01
        : Math.min(Math.abs(rect.top - focusY), Math.abs(rect.bottom - focusY));
      return { paragraph, distance };
    })
    .sort((a, b) => a.distance - b.distance);

  updateActiveParagraph(ranked[0].paragraph);
}

function scheduleActiveParagraphSelection() {
  if (Date.now() < state.programmaticTextScrollUntil) return;
  if (state.activeSelectionQueued) return;
  state.activeSelectionQueued = true;
  window.requestAnimationFrame(() => {
    state.activeSelectionQueued = false;
    selectActiveParagraph();
  });
}

function setupObservers() {
  window.addEventListener("scroll", scheduleActiveParagraphSelection, { passive: true });
  window.addEventListener("resize", scheduleActiveParagraphSelection);
  selectActiveParagraph();
}

function showReferencePopover(button) {
  const citations = button.dataset.citations.split(",").map((citation) => citation.trim()).filter(Boolean);
  elements.popover.innerHTML = `
    <h3>References ${escapeHtml(citations.join(", "))}</h3>
    ${citations
      .map((citation) => `<p><strong>${citation}.</strong> ${escapeHtml(article.references[citation] || "Reference metadata will be fetched in the citation enrichment step.")}</p>`)
      .join("")}
  `;

  const rect = button.getBoundingClientRect();
  const left = Math.min(rect.left, window.innerWidth - 410);
  elements.popover.style.left = `${Math.max(16, left)}px`;
  elements.popover.style.top = `${Math.min(rect.bottom + 10, window.innerHeight - 180)}px`;
  elements.popover.hidden = false;
}

function scrollFigureIntoView(figureId, behavior = "smooth") {
  const card = document.querySelector(`[data-figure-card="${figureId}"]`);
  if (!card) return;
  scrollCardWithinFigureRail(card, behavior);
}

function jumpToMention(paragraphId, figureId) {
  const paragraph = document.getElementById(paragraphId);
  if (!paragraph) return;
  state.programmaticTextScrollUntil = Date.now() + 650;
  paragraph.scrollIntoView({ behavior: "auto", block: "center", inline: "nearest" });
  updateActiveParagraph(paragraph);
  if (figureId) scrollFigureIntoView(figureId);
}

function truncateText(value, maxLength = 1800) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1).trim()}...`;
}

function findParagraphRecord(paragraphId) {
  for (const section of article?.sections || []) {
    const paragraph = section.paragraphs.find((item) => item.id === paragraphId);
    if (paragraph) return { section, paragraph };
  }
  return null;
}

function neighborParagraphText(paragraphElement, offset) {
  const allParagraphs = [...document.querySelectorAll(".paragraph")];
  const index = allParagraphs.indexOf(paragraphElement);
  const target = allParagraphs[index + offset];
  return target ? truncateText(target.textContent, 700) : "";
}

function contextForTextSelection() {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || !selection.toString().trim()) return null;
  const range = selection.getRangeAt(0);
  const container = range.commonAncestorContainer.nodeType === Node.TEXT_NODE
    ? range.commonAncestorContainer.parentElement
    : range.commonAncestorContainer;
  if (!elements.article.contains(container)) return null;

  const paragraphElement = container.closest?.(".paragraph");
  const paragraphRecord = paragraphElement ? findParagraphRecord(paragraphElement.id) : null;
  return {
    type: "text",
    title: "Text selection",
    anchorType: "paragraph",
    paragraphId: paragraphElement?.id || "",
    anchorLabel: truncateText(selection.toString(), 120) || paragraphRecord?.section.title || "Selected paragraph",
    selection: truncateText(selection.toString(), 2200),
    sectionTitle: paragraphRecord?.section.title || "",
    paragraphText: paragraphElement ? truncateText(paragraphElement.textContent, 2200) : "",
    previousParagraph: paragraphElement ? neighborParagraphText(paragraphElement, -1) : "",
    nextParagraph: paragraphElement ? neighborParagraphText(paragraphElement, 1) : "",
    sourceUrl: article?.sourceUrl || "",
  };
}

function showSelectionToolbar() {
  const context = contextForTextSelection();
  if (!context) {
    elements.aiSelectionToolbar.hidden = true;
    state.aiSelectionRect = null;
    return;
  }
  const range = window.getSelection().getRangeAt(0);
  const rect = range.getBoundingClientRect();
  if (!rect.width && !rect.height) return;
  state.aiSelectionRect = rect;
  elements.aiSelectionToolbar.style.left = `${Math.min(window.innerWidth - 96, Math.max(12, rect.left + rect.width / 2 - 42))}px`;
  elements.aiSelectionToolbar.style.top = `${Math.max(12, rect.top - 42)}px`;
  elements.aiSelectionToolbar.hidden = false;
}

function figureContext(figureId, region = null, imageData = "") {
  const figure = article.figures.find((item) => item.id === figureId);
  if (!figure) return null;
  const mentions = (mentionIndex[figureId] || []).slice(0, 5);
  return {
    type: "figure-region",
    title: region ? `${figure.label} region` : figure.label,
    anchorType: "figure",
    figureId,
    anchorLabel: region ? `${figure.label} region` : figure.label,
    figureLabel: figure.label,
    figureTitle: figure.title,
    figureType: figure.type,
    figureCaption: truncateText(figure.caption, 2200),
    mentionTexts: mentions.map((mention) => truncateText(mention.text, 700)),
    region,
    imageData,
    sourceUrl: figure.sourceUrl || article.sourceUrl || "",
  };
}

function renderAiContextPreview(context) {
  if (!context) return "";
  if (context.type === "text") {
    return `
      <div class="ai-context-block">
        <strong>${escapeHtml(context.sectionTitle || "Article text")}</strong>
        <p>${escapeHtml(context.selection)}</p>
      </div>
      <details>
        <summary>Nearby paragraph context</summary>
        ${context.previousParagraph ? `<p>${escapeHtml(context.previousParagraph)}</p>` : ""}
        ${context.paragraphText ? `<p>${escapeHtml(context.paragraphText)}</p>` : ""}
        ${context.nextParagraph ? `<p>${escapeHtml(context.nextParagraph)}</p>` : ""}
      </details>
    `;
  }

  return `
    <div class="ai-context-block">
      <strong>${escapeHtml(context.figureLabel)}: ${escapeHtml(context.figureTitle)}</strong>
      <p>${escapeHtml(context.figureCaption || "No caption available.")}</p>
    </div>
    ${
      context.region
        ? `<p class="ai-context-note">Region: ${Math.round(context.region.width)} x ${Math.round(context.region.height)} px within the displayed figure.</p>`
        : ""
    }
    ${
      context.mentionTexts?.length
        ? `<details open><summary>Text mentions</summary>${context.mentionTexts.map((text) => `<p>${escapeHtml(text)}</p>`).join("")}</details>`
        : ""
    }
  `;
}

function openAiPanel(context) {
  if (!context) return;
  state.aiContext = context;
  elements.aiContextTitle.textContent = context.title || "Selected context";
  elements.aiContextPreview.innerHTML = renderAiContextPreview(context);
  elements.aiAnswer.textContent = "Choose a prompt chip or type your own question.";
  elements.aiAnswerStatus.textContent = "Ready";
  elements.aiQuestion.value = "";
  elements.aiQuestion.placeholder = "Ask about this selection...";
  elements.aiScope.value = "selection";
  state.aiConversation = [];
  state.lastAiQuestion = "";
  state.lastAiAnswer = "";
  if (context.imageData) {
    elements.aiRegionPreview.src = context.imageData;
    elements.aiRegionPreview.hidden = false;
  } else {
    elements.aiRegionPreview.hidden = true;
    elements.aiRegionPreview.removeAttribute("src");
  }
  elements.aiPanel.classList.toggle("is-figure-context", context.anchorType === "figure");
  elements.aiPanel.classList.toggle("is-text-context", context.anchorType !== "figure");
  elements.aiPanel.hidden = false;
  elements.aiQuestion.focus();
}

function closeAiPanel() {
  elements.aiPanel.hidden = true;
  elements.aiPanel.classList.remove("is-figure-context", "is-text-context");
  state.aiContext = null;
  state.aiConversation = [];
  state.lastAiQuestion = "";
  state.lastAiAnswer = "";
}

function paperPayload() {
  if (!article) return null;
  return {
    title: article.title,
    authors: article.authors,
    journal: article.journal,
    published: article.published,
    doi: article.doi,
    sourceUrl: article.sourceUrl,
  };
}

async function apiJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || "Request failed.");
  return payload;
}

function accountMarkup() {
  if (!state.user) {
    return `
      <form class="account-form">
        <input name="username" autocomplete="username" placeholder="Username" aria-label="Username" />
        <input name="password" type="password" autocomplete="current-password" placeholder="Password" aria-label="Password" />
        <button type="submit">Sign in</button>
        <button type="button" data-create-account>Create</button>
      </form>
    `;
  }
  return `
    <div class="account-actions">
      <span class="account-name">${escapeHtml(state.user.username)}</span>
      <button type="button" data-save-paper ${article ? "" : "disabled"}>Save paper</button>
      <button type="button" data-open-library>Library</button>
      <button type="button" data-open-notes ${article ? "" : "disabled"}>Notes</button>
      <button type="button" data-sign-out>Sign out</button>
    </div>
  `;
}

function renderAccountBar() {
  const markup = accountMarkup();
  if (elements.accountBar) elements.accountBar.innerHTML = markup;
  const startAccount = document.querySelector("#start-account");
  if (startAccount) startAccount.innerHTML = markup;
}

async function refreshAccount() {
  try {
    const payload = await apiJson("/api/auth/me");
    state.user = payload.user || null;
  } catch (error) {
    state.user = null;
  }
  renderAccountBar();
}

async function authenticateAccount(mode, form) {
  const username = form.elements.username.value.trim();
  const password = form.elements.password.value;
  const payload = await apiJson(`/api/auth/${mode}`, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  state.user = payload.user;
  renderAccountBar();
}

async function signOut() {
  await apiJson("/api/auth/logout", { method: "POST", body: "{}" });
  state.user = null;
  state.savedPapers = [];
  state.currentPaperId = null;
  state.currentNotes = [];
  elements.libraryPanel.hidden = true;
  elements.notesPanel.hidden = true;
  renderAccountBar();
}

async function saveCurrentPaper() {
  if (!state.user) throw new Error("Please sign in first.");
  const metadata = paperPayload();
  if (!metadata) throw new Error("Load a paper before saving.");
  const payload = await apiJson("/api/library", {
    method: "POST",
    body: JSON.stringify(metadata),
  });
  state.currentPaperId = payload.paper.id;
  state.savedPapers = payload.papers || [];
  renderAccountBar();
  return payload.paper;
}

async function openLibraryPanel() {
  if (!state.user) throw new Error("Please sign in first.");
  const payload = await apiJson("/api/library");
  state.savedPapers = payload.papers || [];
  elements.libraryList.innerHTML = state.savedPapers.length
    ? state.savedPapers
        .map(
          (paper) => `
            <article class="library-item">
              <h3>${escapeHtml(paper.title)}</h3>
              <p>${escapeHtml([paper.journal, paper.published, paper.doi].filter(Boolean).join(" | "))}</p>
              <button type="button" data-load-saved-paper="${paper.id}">Open paper</button>
            </article>
          `,
        )
        .join("")
    : `<p class="empty-state">No saved papers yet.</p>`;
  elements.libraryPanel.hidden = false;
}

function renderNotes() {
  elements.notesTitle.textContent = article?.title ? "Notes for this paper" : "Paper notes";
  elements.notesList.innerHTML = state.currentNotes.length
    ? state.currentNotes
        .map((note) => {
          const body = note.kind === "ai-answer"
            ? `${note.question ? `Q: ${note.question}\n\n` : ""}${note.answer}`
            : note.text;
          return `
            <article class="note-card">
              <h3>${escapeHtml(note.kind === "ai-answer" ? "AI answer" : "Note")}</h3>
              ${note.anchorLabel || note.contextTitle ? `<p>${escapeHtml(note.anchorLabel || note.contextTitle)}</p>` : ""}
              <p>${escapeHtml(body)}</p>
              ${note.anchorType ? `<button type="button" data-jump-note-anchor="${note.anchorType}:${note.anchorType === "paragraph" ? note.paragraphId : note.figureId}">Go to anchor</button>` : ""}
              <button type="button" data-delete-note="${note.id}">Delete</button>
            </article>
          `;
        })
        .join("")
    : `<p class="empty-state">No notes for this paper yet.</p>`;
}

function filterNotesToAnchor(anchorType, anchorId) {
  const allNotes = notesForAnchor(anchorType, anchorId);
  elements.notesTitle.textContent = `${allNotes.length} note${allNotes.length === 1 ? "" : "s"} at anchor`;
  elements.notesList.innerHTML = allNotes.length
    ? allNotes
        .map((note) => {
          const body = note.kind === "ai-answer"
            ? `${note.question ? `Q: ${note.question}\n\n` : ""}${note.answer}`
            : note.text;
          return `
            <article class="note-card">
              <h3>${escapeHtml(note.kind === "ai-answer" ? "AI answer" : "Note")}</h3>
              ${note.anchorLabel || note.contextTitle ? `<p>${escapeHtml(note.anchorLabel || note.contextTitle)}</p>` : ""}
              <p>${escapeHtml(body)}</p>
              <button type="button" data-delete-note="${note.id}">Delete</button>
            </article>
          `;
        })
        .join("")
    : `<p class="empty-state">No notes at this anchor.</p>`;
  elements.notesPanel.hidden = false;
}

function jumpToNoteAnchor(anchorType, anchorId) {
  if (anchorType === "paragraph") {
    const paragraph = document.getElementById(anchorId);
    if (paragraph) {
      paragraph.scrollIntoView({ behavior: "smooth", block: "center" });
      updateActiveParagraph(paragraph);
    }
    return;
  }
  if (anchorType === "figure") {
    scrollFigureIntoView(anchorId);
  }
}

async function refreshNotes() {
  if (!state.currentPaperId) await saveCurrentPaper();
  const payload = await apiJson(`/api/notes?paperId=${encodeURIComponent(state.currentPaperId)}`);
  state.currentNotes = payload.notes || [];
  renderNotes();
  renderArticle();
  renderFigures();
}

async function openNotesPanel() {
  if (!state.user) throw new Error("Please sign in first.");
  if (!article) throw new Error("Load a paper first.");
  await refreshNotes();
  elements.notesPanel.hidden = false;
}

async function saveTextNote() {
  if (!state.currentPaperId) await saveCurrentPaper();
  const text = elements.noteText.value.trim();
  if (!text) return;
  const activeParagraph = state.activeParagraphId ? document.getElementById(state.activeParagraphId) : null;
  const payload = await apiJson("/api/notes", {
    method: "POST",
    body: JSON.stringify({
      paperId: state.currentPaperId,
      kind: "note",
      text,
      anchorType: state.activeParagraphId ? "paragraph" : "",
      paragraphId: state.activeParagraphId || "",
      anchorLabel: activeParagraph ? truncateText(activeParagraph.textContent, 120) : "",
    }),
  });
  state.currentNotes = payload.notes || [];
  elements.noteText.value = "";
  renderNotes();
  renderArticle();
  renderFigures();
}

async function saveAiAnswerNote() {
  if (!state.currentPaperId) await saveCurrentPaper();
  const answer = state.lastAiAnswer || elements.aiAnswer.textContent.trim();
  if (!answer || answer === "Choose a prompt chip or type your own question.") {
    throw new Error("No AI answer to save yet.");
  }
  const payload = await apiJson("/api/notes", {
    method: "POST",
    body: JSON.stringify({
      paperId: state.currentPaperId,
      kind: "ai-answer",
      question: state.lastAiQuestion || elements.aiQuestion.value,
      answer,
      contextTitle: state.aiContext?.title || "",
      anchorType: state.aiContext?.anchorType || "",
      paragraphId: state.aiContext?.paragraphId || "",
      figureId: state.aiContext?.figureId || "",
      anchorLabel: state.aiContext?.anchorLabel || state.aiContext?.title || "",
    }),
  });
  state.currentNotes = payload.notes || [];
  renderNotes();
  renderArticle();
  renderFigures();
  elements.aiAnswerStatus.textContent = "Saved";
}

async function deleteNote(noteId) {
  if (!state.currentPaperId) return;
  const payload = await apiJson("/api/notes/delete", {
    method: "POST",
    body: JSON.stringify({ paperId: state.currentPaperId, noteId }),
  });
  state.currentNotes = payload.notes || [];
  renderNotes();
  renderArticle();
  renderFigures();
}

function sectionTextForContext(context) {
  if (context?.paragraphId) {
    const record = findParagraphRecord(context.paragraphId);
    if (record) {
      const text = record.section.paragraphs
        .map((paragraph) => paragraph.text || "")
        .filter(Boolean)
        .join("\n\n");
      return `${record.section.title}\n${truncateText(text, 6500)}`;
    }
  }
  if (context?.figureId) {
    const mentions = mentionIndex[context.figureId] || [];
    const text = mentions
      .map((mention) => `${mention.sectionTitle}: ${mention.text}`)
      .join("\n\n");
    return truncateText(text || "No in-text mentions found for this figure.", 6500);
  }
  return "";
}

function wholePaperText() {
  const text = (article?.sections || [])
    .map((section) => {
      const paragraphs = section.paragraphs
        .map((paragraph) => paragraph.text || "")
        .filter(Boolean)
        .join("\n\n");
      return `${section.title}\n${paragraphs}`;
    })
    .join("\n\n");
  return truncateText(text, 14000);
}

function aiScopeText(context) {
  const scope = elements.aiScope?.value || "selection";
  if (scope === "section") {
    return sectionTextForContext(context);
  }
  if (scope === "paper") {
    return wholePaperText();
  }
  return "";
}

function aiScopeLabel() {
  const scope = elements.aiScope?.value || "selection";
  if (scope === "section") return "current section or all figure mentions";
  if (scope === "paper") return "whole paper text";
  return "selected context only";
}

function renderAiConversation() {
  if (!state.aiConversation.length) {
    elements.aiAnswer.textContent = "Choose a prompt chip or type your own question.";
    return;
  }
  elements.aiAnswer.innerHTML = state.aiConversation
    .map(
      (turn) => `
        <article class="ai-turn">
          <h3>Question</h3>
          <p>${escapeHtml(turn.question)}</p>
          <h3>Answer</h3>
          <p>${escapeHtml(turn.answer)}</p>
        </article>
      `,
    )
    .join("");
  elements.aiAnswer.scrollTop = elements.aiAnswer.scrollHeight;
}

function buildAiPrompt(context, question = "") {
  const parts = [
    "You are helping read a scientific paper. Answer using only the provided context, and say what is uncertain when the context is insufficient.",
    "Do not offer to look elsewhere unless broader context is not included; instead, state which context scope was provided.",
    "",
    `Paper: ${article?.title || "Untitled article"}`,
    `Journal: ${article?.journal || "Unknown journal"}`,
    article?.doi ? `DOI: ${article.doi}` : "",
    `Context scope: ${aiScopeLabel()}`,
    "",
  ].filter(Boolean);

  if (context.type === "text") {
    parts.push(
      `Selected text from ${context.sectionTitle || "the article"}:`,
      context.selection,
      "",
      "Nearby context:",
      [context.previousParagraph, context.paragraphText, context.nextParagraph].filter(Boolean).join("\n\n"),
    );
  } else {
    parts.push(
      `${context.figureLabel}: ${context.figureTitle}`,
      `Figure type: ${context.figureType}`,
      `Caption: ${context.figureCaption || "No caption available."}`,
    );
    if (context.region) {
      parts.push(
        `Selected visual region: x=${Math.round(context.region.x)}, y=${Math.round(context.region.y)}, width=${Math.round(context.region.width)}, height=${Math.round(context.region.height)} in displayed figure pixels.`,
      );
    }
    if (context.mentionTexts?.length) {
      parts.push("", "Relevant text mentions:", context.mentionTexts.join("\n\n"));
    }
  }

  const scopedText = aiScopeText(context);
  if (scopedText) {
    parts.push("", "Additional context from selected scope:", scopedText);
  }

  if (state.aiConversation.length) {
    const history = state.aiConversation
      .slice(-4)
      .map((turn, index) => `Turn ${index + 1} question: ${turn.question}\nTurn ${index + 1} answer: ${truncateText(turn.answer, 1200)}`)
      .join("\n\n");
    parts.push("", "Conversation so far:", history);
  }

  parts.push("", `Question: ${question.trim() || "Explain the selected context and what I should pay attention to."}`);
  return parts.join("\n");
}

async function copyAiPrompt() {
  if (!state.aiContext) return;
  const prompt = buildAiPrompt(state.aiContext, elements.aiQuestion.value);
  await navigator.clipboard.writeText(prompt);
  elements.aiAnswer.textContent = "Prompt copied. You can paste it into ChatGPT or another assistant.";
  elements.aiAnswerStatus.textContent = "Copied";
}

async function askLocalAi() {
  if (!state.aiContext) return;
  const question = elements.aiQuestion.value.trim();
  elements.aiAsk.disabled = true;
  elements.aiAnswer.textContent = "Asking local AI...";
  elements.aiAnswerStatus.textContent = "Thinking";
  try {
    const response = await fetch("/api/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: buildAiPrompt(state.aiContext, question),
        question,
        context: {
          type: state.aiContext.type,
          title: state.aiContext.title,
          imageData: state.aiContext.imageData || "",
        },
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "AI request failed.");
    const answer = payload.answer || "No answer returned.";
    state.lastAiQuestion = question || "Explain the selected context and what I should pay attention to.";
    state.lastAiAnswer = answer;
    state.aiConversation.push({ question: state.lastAiQuestion, answer });
    renderAiConversation();
    elements.aiQuestion.value = "";
    elements.aiQuestion.placeholder = "Ask a follow-up...";
    elements.aiAnswerStatus.textContent = "Done";
  } catch (error) {
    elements.aiAnswer.textContent = `${error.message}\n\nUse Copy prompt for now, or set OPENAI_API_KEY before starting the local server.`;
    elements.aiAnswerStatus.textContent = "Needs setup";
  } finally {
    elements.aiAsk.disabled = false;
  }
}

function startFigureRegionMode(figureId) {
  state.aiRegionModeFigureId = figureId;
  document.querySelectorAll(".figure-card").forEach((card) => {
    card.classList.toggle("is-region-target", card.dataset.figureCard === figureId);
  });
  const card = document.querySelector(`[data-figure-card="${figureId}"]`);
  card?.querySelector(".figure-stage")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

function stopFigureRegionMode() {
  state.aiRegionModeFigureId = null;
  document.querySelectorAll(".figure-card.is-region-target").forEach((card) => {
    card.classList.remove("is-region-target");
  });
}

function cropFigureRegion(stage, region) {
  const image = stage.querySelector("img");
  if (!image || !image.naturalWidth || !image.naturalHeight) return "";
  const imageRect = image.getBoundingClientRect();
  const left = Math.max(region.left, imageRect.left);
  const top = Math.max(region.top, imageRect.top);
  const right = Math.min(region.right, imageRect.right);
  const bottom = Math.min(region.bottom, imageRect.bottom);
  if (right - left < 8 || bottom - top < 8) return "";

  const sx = ((left - imageRect.left) / imageRect.width) * image.naturalWidth;
  const sy = ((top - imageRect.top) / imageRect.height) * image.naturalHeight;
  const sw = ((right - left) / imageRect.width) * image.naturalWidth;
  const sh = ((bottom - top) / imageRect.height) * image.naturalHeight;
  const canvas = document.createElement("canvas");
  canvas.width = Math.min(1200, Math.max(1, Math.round(sw)));
  canvas.height = Math.min(1200, Math.max(1, Math.round(sh)));
  const context = canvas.getContext("2d");
  try {
    context.drawImage(image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/png");
  } catch (error) {
    return "";
  }
}

function handleFigureRegionPointerDown(event, stage, card) {
  event.preventDefault();
  const startX = event.clientX;
  const startY = event.clientY;
  const box = document.createElement("div");
  box.className = "figure-region-box";
  stage.appendChild(box);
  stage.setPointerCapture(event.pointerId);

  const update = (moveEvent) => {
    const stageRect = stage.getBoundingClientRect();
    const left = Math.min(startX, moveEvent.clientX) - stageRect.left;
    const top = Math.min(startY, moveEvent.clientY) - stageRect.top;
    const width = Math.abs(moveEvent.clientX - startX);
    const height = Math.abs(moveEvent.clientY - startY);
    box.style.left = `${left}px`;
    box.style.top = `${top}px`;
    box.style.width = `${width}px`;
    box.style.height = `${height}px`;
  };

  const cancel = () => {
    box.remove();
    stopFigureRegionMode();
    stage.removeEventListener("pointermove", update);
    stage.removeEventListener("pointerup", stop);
    stage.removeEventListener("pointercancel", cancel);
  };

  const stop = () => {
    stage.removeEventListener("pointermove", update);
    stage.removeEventListener("pointerup", stop);
    stage.removeEventListener("pointercancel", cancel);
    const regionRect = box.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    const region = {
      x: regionRect.left - stageRect.left,
      y: regionRect.top - stageRect.top,
      width: regionRect.width,
      height: regionRect.height,
      left: regionRect.left,
      top: regionRect.top,
      right: regionRect.right,
      bottom: regionRect.bottom,
    };
    box.remove();
    stopFigureRegionMode();
    if (region.width < 10 || region.height < 10) return;
    const imageData = cropFigureRegion(stage, region);
    openAiPanel(figureContext(card.dataset.figureCard, region, imageData));
  };

  update(event);
  stage.addEventListener("pointermove", update);
  stage.addEventListener("pointerup", stop);
  stage.addEventListener("pointercancel", cancel);
}

async function importPaperUrl(url, button) {
  const targetUrl = url.trim();
  if (!targetUrl) return;
  const originalLabel = button?.textContent;
  if (button) {
    button.disabled = true;
    button.textContent = "Loading";
  }

  try {
    const response = await fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: targetUrl }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Could not import this paper.");
    }
    loadArticle(payload);
  } catch (error) {
    alert(
      `${error.message}\n\nFor URL imports, open the app from the local importer server at http://127.0.0.1:4174/index.html.`,
    );
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",").pop() : result);
    });
    reader.addEventListener("error", () => reject(reader.error || new Error("Could not read this PDF.")));
    reader.readAsDataURL(file);
  });
}

async function uploadSupplementPdf(file) {
  if (!article?.sourceUrl) {
    alert("Load a paper before uploading a supplementary PDF.");
    return;
  }
  if (!file) return;
  if (!/\.pdf$/i.test(file.name) && file.type !== "application/pdf") {
    alert("Please choose a PDF file.");
    return;
  }

  const originalLabel = elements.uploadSupplement.textContent;
  elements.uploadSupplement.disabled = true;
  elements.uploadSupplement.textContent = "Uploading";
  try {
    const dataBase64 = await fileToBase64(file);
    const response = await fetch("/api/upload-supplement", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: article.sourceUrl,
        cacheKey: article.cacheKey,
        name: file.name,
        contentType: file.type || "application/pdf",
        dataBase64,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not upload this supplementary PDF.");
    loadArticle(payload);
  } catch (error) {
    alert(error.message);
  } finally {
    elements.uploadSupplement.disabled = false;
    elements.uploadSupplement.textContent = originalLabel;
    elements.supplementPdf.value = "";
  }
}

function setupEvents() {
  elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await importPaperUrl(elements.url.value, elements.form.querySelector("button[type='submit']"));
  });

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("#start-form");
    if (!form) return;
    event.preventDefault();
    const input = form.querySelector("#start-paper-url");
    await importPaperUrl(input.value, form.querySelector("button[type='submit']"));
  });

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest(".account-form");
    if (!form) return;
    event.preventDefault();
    try {
      await authenticateAccount("login", form);
    } catch (error) {
      alert(error.message);
    }
  });

  elements.zoom.addEventListener("input", () => {
    state.zoom = Number(elements.zoom.value) / 100;
    updateFigureCards();
  });
  elements.uploadSupplement.addEventListener("click", () => {
    elements.supplementPdf.click();
  });
  elements.supplementPdf.addEventListener("change", async () => {
    await uploadSupplementPdf(elements.supplementPdf.files?.[0]);
  });

  elements.sync.addEventListener("change", () => {
    state.syncFigures = elements.sync.checked;
    if (state.syncFigures) syncFigureRailToActive({ force: true });
  });

  elements.figureList.addEventListener("scroll", () => {
    if (state.programmaticFigureScroll) {
      window.clearTimeout(state.figureRailScrollSettleTimer);
      state.figureRailScrollSettleTimer = window.setTimeout(() => {
        state.programmaticFigureScroll = false;
      }, 160);
    }
  });

  elements.figureRail.addEventListener(
    "wheel",
    (event) => {
      if (event.target.closest(".figure-tools")) return;
      event.preventDefault();
      state.programmaticFigureScroll = false;
      window.clearTimeout(state.figureRailScrollSettleTimer);
      elements.figureList.scrollBy({
        top: event.deltaY,
        left: event.deltaX,
        behavior: "auto",
      });
    },
    { passive: false },
  );

  elements.figureList.addEventListener("pointerdown", (event) => {
    const stage = event.target.closest(".figure-stage");
    if (!stage || !stage.querySelector("img")) return;
    const card = stage.closest("[data-figure-card]");
    if (!card) return;
    if (state.aiRegionModeFigureId === card.dataset.figureCard) {
      handleFigureRegionPointerDown(event, stage, card);
      return;
    }

    event.preventDefault();
    stage.classList.add("is-panning");
    stage.setPointerCapture(event.pointerId);

    const startX = event.clientX;
    const startY = event.clientY;
    const startPan = state.panByFigure[card.dataset.figureCard] || { x: 0, y: 0 };

    const move = (moveEvent) => {
      setFigurePan(card, {
        x: startPan.x + moveEvent.clientX - startX,
        y: startPan.y + moveEvent.clientY - startY,
      });
    };

    const stop = () => {
      stage.classList.remove("is-panning");
      stage.removeEventListener("pointermove", move);
      stage.removeEventListener("pointerup", stop);
      stage.removeEventListener("pointercancel", stop);
    };

    stage.addEventListener("pointermove", move);
    stage.addEventListener("pointerup", stop);
    stage.addEventListener("pointercancel", stop);
  });

  elements.figureList.addEventListener("dblclick", (event) => {
    const card = event.target.closest("[data-figure-card]");
    if (!card) return;
    state.zoom = 1;
    elements.zoom.value = 100;
    state.panByFigure = {};
    updateFigureCards();
  });

  document.addEventListener("click", async (event) => {
    const figureButton = event.target.closest("[data-figure]");
    const citationButton = event.target.closest("[data-citations]");
    const pinButton = event.target.closest("[data-pin]");
    const jumpButton = event.target.closest("[data-jump-figure]");
    const openImageButton = event.target.closest("[data-open-image]");
    const retryImageButton = event.target.closest("[data-retry-image]");
    const legendToggleButton = event.target.closest("[data-toggle-legend]");
    const legendPanelButton = event.target.closest("[data-legend-panel]");
    const mentionTargetButton = event.target.closest("[data-mention-target]");
    const askRegionButton = event.target.closest("[data-ask-region]");
    const createAccountButton = event.target.closest("[data-create-account]");
    const savePaperButton = event.target.closest("[data-save-paper]");
    const openLibraryButton = event.target.closest("[data-open-library]");
    const openNotesButton = event.target.closest("[data-open-notes]");
    const signOutButton = event.target.closest("[data-sign-out]");
    const savedPaperButton = event.target.closest("[data-load-saved-paper]");
    const deleteNoteButton = event.target.closest("[data-delete-note]");
    const anchorNotesButton = event.target.closest("[data-open-anchor-notes]");
    const jumpNoteAnchorButton = event.target.closest("[data-jump-note-anchor]");

    if (!citationButton && !event.target.closest("#reference-popover")) {
      elements.popover.hidden = true;
    }

    if (figureButton) {
      scrollFigureIntoView(figureButton.dataset.figure);
    }

    if (citationButton) {
      showReferencePopover(citationButton);
    }

    if (pinButton) {
      const id = pinButton.dataset.pin;
      if (state.pinnedFigures.has(id)) state.pinnedFigures.delete(id);
      else state.pinnedFigures.add(id);
      updateFigureCards();
    }

    if (jumpButton) {
      scrollFigureIntoView(jumpButton.dataset.jumpFigure);
    }

    if (openImageButton) {
      openImageViewer(openImageButton.dataset.openImage);
    }

    if (retryImageButton) {
      retryFigureImage(retryImageButton.dataset.retryImage);
    }

    if (legendToggleButton) {
      const id = legendToggleButton.dataset.toggleLegend;
      setLegendOpen(id, !state.openLegendFigures.has(id));
    }

    if (legendPanelButton) {
      setLegendOpen(
        legendPanelButton.dataset.legendFigure,
        true,
        legendPanelButton.dataset.legendPanel,
      );
    }

    if (mentionTargetButton) {
      jumpToMention(
        mentionTargetButton.dataset.mentionTarget,
        mentionTargetButton.dataset.mentionFigure,
      );
    }

    if (askRegionButton) {
      startFigureRegionMode(askRegionButton.dataset.askRegion);
    }

    if (createAccountButton) {
      const form = createAccountButton.closest(".account-form");
      try {
        await authenticateAccount("signup", form);
      } catch (error) {
        alert(error.message);
      }
    }

    if (savePaperButton) {
      try {
        await saveCurrentPaper();
      } catch (error) {
        alert(error.message);
      }
    }

    if (openLibraryButton) {
      try {
        await openLibraryPanel();
      } catch (error) {
        alert(error.message);
      }
    }

    if (openNotesButton) {
      try {
        await openNotesPanel();
      } catch (error) {
        alert(error.message);
      }
    }

    if (signOutButton) {
      try {
        await signOut();
      } catch (error) {
        alert(error.message);
      }
    }

    if (savedPaperButton) {
      const paper = state.savedPapers.find((item) => item.id === savedPaperButton.dataset.loadSavedPaper);
      if (paper?.sourceUrl) {
        elements.libraryPanel.hidden = true;
        await importPaperUrl(paper.sourceUrl);
        state.currentPaperId = paper.id;
      }
    }

    if (deleteNoteButton) {
      try {
        await deleteNote(deleteNoteButton.dataset.deleteNote);
      } catch (error) {
        alert(error.message);
      }
    }

    if (anchorNotesButton) {
      const [anchorType, anchorId] = anchorNotesButton.dataset.openAnchorNotes.split(":");
      filterNotesToAnchor(anchorType, anchorId);
    }

    if (jumpNoteAnchorButton) {
      const [anchorType, anchorId] = jumpNoteAnchorButton.dataset.jumpNoteAnchor.split(":");
      jumpToNoteAnchor(anchorType, anchorId);
    }
  });

  elements.imageViewerClose.addEventListener("click", closeImageViewer);
  elements.imageViewer.addEventListener("click", (event) => {
    if (event.target === elements.imageViewer) closeImageViewer();
  });
  elements.aiSelectionAsk.addEventListener("click", () => {
    openAiPanel(contextForTextSelection());
    elements.aiSelectionToolbar.hidden = true;
  });
  elements.aiClose.addEventListener("click", closeAiPanel);
  elements.aiCopy.addEventListener("click", copyAiPrompt);
  elements.aiAsk.addEventListener("click", askLocalAi);
  elements.aiSave.addEventListener("click", async () => {
    try {
      await saveAiAnswerNote();
    } catch (error) {
      alert(error.message);
    }
  });
  elements.libraryClose.addEventListener("click", () => {
    elements.libraryPanel.hidden = true;
  });
  elements.notesClose.addEventListener("click", () => {
    elements.notesPanel.hidden = true;
  });
  elements.saveNote.addEventListener("click", async () => {
    try {
      await saveTextNote();
    } catch (error) {
      alert(error.message);
    }
  });
  document.querySelectorAll("[data-ai-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      elements.aiQuestion.value = button.dataset.aiPrompt;
      elements.aiQuestion.focus();
    });
  });
  document.addEventListener("mouseup", () => window.setTimeout(showSelectionToolbar, 0));
  document.addEventListener("keyup", (event) => {
    if (event.key === "Escape") {
      elements.aiSelectionToolbar.hidden = true;
      stopFigureRegionMode();
      return;
    }
    showSelectionToolbar();
  });
  document.addEventListener("selectionchange", () => {
    window.clearTimeout(state.aiSelectionTimer);
    state.aiSelectionTimer = window.setTimeout(showSelectionToolbar, 80);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.imageViewer.hidden) closeImageViewer();
    if (event.key === "Escape" && !elements.aiPanel.hidden) closeAiPanel();
  });
}

function importInitialUrl() {
  const params = new URLSearchParams(window.location.search);
  const url = params.get("url");
  if (!url) return;
  elements.url.value = url;
  const startInput = document.querySelector("#start-paper-url");
  if (startInput) startInput.value = url;
  importPaperUrl(url);
}

renderStartPage();
setupEvents();
setupObservers();
refreshAccount();
importInitialUrl();
