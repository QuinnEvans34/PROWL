const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  ImageRun,
  LevelFormat,
  PageNumber,
  Packer,
  Paragraph,
  SectionType,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} = require("docx");

const OUTPUT = path.resolve("Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx");
if (fs.existsSync(OUTPUT)) {
  throw new Error(`Refusing to overwrite existing file: ${OUTPUT}`);
}

const NAVY = "153A5B";
const TEAL = "147D73";
const DARK = "263442";
const MID = "5D6A74";
const LIGHT_TEAL = "E8F3F1";
const LIGHT_BLUE = "EDF3F8";
const LIGHT_GRAY = "F4F6F8";
const WHITE = "FFFFFF";
const GRID = "AAB5BD";
const CONTENT_WIDTH = 10080;

const logoPath = path.resolve("assets/branding/PROWL_CT_wordmark_concept_v2.png");
const systemFlowPath = path.resolve("assets/branding/PROWL_system_flow_v3.png");
const schemaPath = path.resolve("assets/branding/PROWL_file_schema_v3.png");
for (const requiredPath of [logoPath, systemFlowPath, schemaPath]) {
  if (!fs.existsSync(requiredPath)) throw new Error(`Missing required asset: ${requiredPath}`);
}

function textRun(text, options = {}) {
  return new TextRun({
    text,
    font: options.font || "Georgia",
    size: options.size || 21,
    color: options.color || DARK,
    bold: options.bold || false,
    italics: options.italics || false,
    allCaps: options.allCaps || false,
  });
}

function body(text, options = {}) {
  return new Paragraph({
    style: options.style || "BodyText",
    alignment: options.alignment,
    keepNext: options.keepNext,
    pageBreakBefore: options.pageBreakBefore,
    spacing: options.spacing,
    children: [textRun(text, options.run || {})],
  });
}

function rich(parts, options = {}) {
  return new Paragraph({
    style: options.style || "BodyText",
    alignment: options.alignment,
    keepNext: options.keepNext,
    pageBreakBefore: options.pageBreakBefore,
    spacing: options.spacing,
    children: parts.map((part) => textRun(part.text, part)),
  });
}

function heading1(text, pageBreakBefore = false) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore,
    keepNext: true,
    border: {
      bottom: { color: TEAL, style: BorderStyle.SINGLE, size: 8, space: 5 },
    },
    children: [textRun(text, { size: 31, bold: true, color: NAVY })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    keepNext: true,
    children: [textRun(text, { size: 25, bold: true, color: TEAL })],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 150 },
    children: [textRun(text, { size: 17, color: MID, italics: true })],
  });
}

function bullet(text) {
  return new Paragraph({
    style: "BodyText",
    numbering: { reference: "appendix-bullets", level: 0 },
    children: [textRun(text)],
  });
}

function callout(label, text) {
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    margins: { top: 120, bottom: 120, left: 180, right: 180 },
    borders: {
      top: { style: BorderStyle.NONE, size: 0, color: WHITE },
      bottom: { style: BorderStyle.NONE, size: 0, color: WHITE },
      left: { style: BorderStyle.SINGLE, size: 18, color: TEAL },
      right: { style: BorderStyle.NONE, size: 0, color: WHITE },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: WHITE },
      insideVertical: { style: BorderStyle.NONE, size: 0, color: WHITE },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            shading: { fill: LIGHT_TEAL, type: ShadingType.CLEAR },
            children: [
              rich([
                { text: `${label} `, bold: true, color: TEAL },
                { text },
              ], { spacing: { after: 0 } }),
            ],
          }),
        ],
      }),
    ],
  });
}

function tableCell(content, width, options = {}) {
  const paragraphs = Array.isArray(content)
    ? content.map((item) => typeof item === "string" ? body(item, { spacing: { after: 0 }, run: { size: 18 } }) : item)
    : [body(content, { spacing: { after: 0 }, run: { size: 18, bold: options.bold, color: options.color } })];
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    shading: options.fill ? { fill: options.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 95, bottom: 95, left: 110, right: 110 },
    children: paragraphs,
  });
}

function dataTable(headers, rows, widths) {
  const tableRows = [
    new TableRow({
      tableHeader: true,
      children: headers.map((header, index) => tableCell(header, widths[index], { fill: NAVY, bold: true, color: WHITE })),
    }),
  ];
  rows.forEach((row, rowIndex) => {
    tableRows.push(new TableRow({
      children: row.map((cell, index) => tableCell(cell, widths[index], { fill: rowIndex % 2 ? LIGHT_GRAY : WHITE })),
    }));
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    layout: "fixed",
    borders: {
      top: { style: BorderStyle.SINGLE, size: 5, color: GRID },
      bottom: { style: BorderStyle.SINGLE, size: 5, color: GRID },
      left: { style: BorderStyle.SINGLE, size: 5, color: GRID },
      right: { style: BorderStyle.SINGLE, size: 5, color: GRID },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: GRID },
      insideVertical: { style: BorderStyle.SINGLE, size: 4, color: GRID },
    },
    rows: tableRows,
  });
}

function spacer(after = 120) {
  return new Paragraph({ spacing: { after }, children: [] });
}

function figure(imagePath, width, height, altText) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    keepNext: true,
    spacing: { before: 100, after: 40 },
    children: [
      new ImageRun({
        data: fs.readFileSync(imagePath),
        type: "png",
        transformation: { width, height },
        altText: { title: altText, description: altText, name: altText },
      }),
    ],
  });
}

const footer = new Footer({
  children: [
    new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [
        textRun("Quinton Evans  |  PROWL Technical Appendix  |  ", { size: 17, color: MID }),
        new TextRun({ children: [PageNumber.CURRENT], font: "Georgia", size: 17, color: MID }),
      ],
    }),
  ],
});

const cover = [
  spacer(1500),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [textRun("BSAAI CAPSTONE TECHNICAL APPENDIX", { size: 19, bold: true, color: TEAL, allCaps: true })],
  }),
  figure(logoPath, 500, 167, "PROWL wordmark with axial CT and pancreas contour"),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 110 },
    children: [textRun("Pancreatic Review and Outlining", { size: 21, bold: true, color: TEAL })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 430 },
    children: [textRun("Workflow for Lesions", { size: 21, bold: true, color: TEAL })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 420 },
    border: { bottom: { color: "B7C8D5", style: BorderStyle.SINGLE, size: 5, space: 16 } },
    children: [textRun("Technical Design Supplement for an Autonomous Pancreatic Lesion Annotation and Radiologist Review System", { size: 25, bold: true, color: DARK })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 150 },
    children: [textRun("Quinton Evans", { size: 25, bold: true, color: DARK })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 90 },
    children: [textRun("Bachelor of Science in Applied Artificial Intelligence and Data Engineering", { size: 19, color: MID })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [textRun("August 25, 2026", { size: 19, color: MID })],
  }),
];

const content = [
  heading1("A1. Purpose and Design Boundaries"),
  body("This appendix provides the technical evidence behind the PROWL proposal. It documents the planned system boundaries, measured data facts, evaluation controls, and fallback paths without treating implementation choices as fixed before experimentation begins."),
  callout("Implementation boundary.", "The committed design is file-based and reproducible. A relational database, managed vector service, or particular model architecture may be evaluated later, but none is required by this proposal and none will be implemented before the simpler design demonstrates a measured need."),
  heading2("Three-source design"),
  body("PROWL combines two imaging datasets and one supporting text corpus. The first two drive model development; the third supports evidence retrieval for the review workflow. PanTS narrative-text incorporation is a stretch opportunity rather than a committed dependency."),
  dataTable(
    ["source", "role in PROWL", "core boundary"],
    [
      ["PanTS imaging", "Primary CT and annotation source; establishes the autonomous baseline and held-out evaluation path.", "No raw data stored in the repository; patient-group protection remains mandatory."],
      ["PANORAMA imaging", "Additional CT and label source; expands tumor examples and tests cross-source integration.", "Declared imports are excluded before any combined cohort is created."],
      ["PubMed/PMC literature", "Supporting evidence corpus used to retrieve cited passages beside structured imaging findings.", "Contains published literature, not patient records; unsupported questions must be refused."],
    ],
    [1900, 4190, 3990]
  ),

  heading1("A2. System Architecture", true),
  body("The imaging and literature workstreams remain separate until the reviewer interface. Imaging produces masks, measurements, and scores. Retrieval produces cited passages or a refusal. Both write versioned artifacts so that every displayed result can be traced to its source, configuration, and model version."),
  figure(systemFlowPath, 650, 282, "PROWL system architecture diagram"),
  caption("Figure A1. High-level architecture. File-based artifacts connect the workstreams without requiring a database implementation."),
  heading2("End-to-end imaging path"),
  dataTable(
    ["stage", "system action", "verification evidence"],
    [
      ["1. Ingest", "Validate the scan, source identity, label mapping, and required metadata.", "Manifest checks and reconciliation counts."],
      ["2. Localize", "Identify the pancreatic region without a human-supplied box.", "Coverage of the target region and localization failures."],
      ["3. Segment", "Produce pancreas and suspected-lesion contours using the selected experimental model.", "Pancreas and lesion metrics reported separately."],
      ["4. Evaluate", "Calculate measurements and a review-ordering score.", "Patient-level sensitivity, specificity, and operating-point curves."],
      ["5. Review", "Display the scan and proposed contours for accept, edit, or reject review.", "Recorded reviewer decision and limitation history."],
    ],
    [1300, 4700, 4080]
  ),
  rich([
    { text: "Measured scale. ", bold: true, color: NAVY },
    { text: "Across 9,901 PanTS scans, a CT resampled to 1.5 mm isotropic contains a median of approximately 6.9 million voxels. Whole-volume localization therefore requires sliding-window or equivalent full-volume processing; patch-only evaluation is not sufficient." },
  ]),

  heading1("A3. Data Sources and Reconciliation", true),
  heading2("PANORAMA evidence measured from the delivered files"),
  body("The PANORAMA spreadsheet contains 2,238 rows and its label archive contains one file per study. The declared NIH and Medical Segmentation Decathlon imports are removed before integration because related scans are already represented in the PanTS evaluation design."),
  dataTable(
    ["observed fact", "count", "design consequence"],
    [
      ["PANORAMA spreadsheet rows and label files", "2,238", "Identifiers reconcile directly; missing and duplicate file checks remain automated."],
      ["Declared NIH and Decathlon imports", "274", "Excluded before cohort construction to protect evaluation independence."],
      ["Usable PANORAMA cases after exclusion", "1,964", "Available for source-aware integration experiments."],
      ["Usable tumor cases", "578", "Additional tumor examples are the principal data-scale opportunity."],
      ["Expert / machine-generated tumor masks", "382 / 196", "Annotation provenance is retained and results are reported by source quality."],
    ],
    [3900, 1400, 4780]
  ),
  heading2("Integration controls"),
  dataTable(
    ["difference or risk", "control"],
    [
      ["Label values and structure definitions differ between sources.", "A configuration-driven remap is tested against representative real masks before training."],
      ["PANORAMA pancreas masks are machine-generated, while PanTS masks are expert-validated.", "Provenance is stored per structure; pancreas and lesion performance are reported separately by source."],
      ["Negative-case definitions and reference standards differ.", "Reference standard remains visible in the manifest and is included in subgroup analysis."],
      ["A scan may appear in more than one public collection.", "Declared imports are excluded, duplicate detection runs before splitting, and every patient group belongs to one frozen cohort only."],
      ["Contrast phase changes model behavior.", "Contrast phase is tracked and analyzed rather than treated as interchangeable acquisition metadata."],
    ],
    [4900, 5180]
  ),
  callout("Cohort in plain language.", "A cohort is simply a frozen list of cases used for one purpose—training, validation, or testing. PROWL creates these lists only after overlap and duplicate checks, records a checksum, and prevents the same patient group from crossing purposes."),

  heading1("A4. File-Based Data Design", true),
  body("The capstone will begin with versioned manifests and artifact folders on local or attached storage. This keeps the data path inspectable, matches the scale of a solo academic project, and avoids committing time to database infrastructure before it is justified."),
  figure(schemaPath, 650, 325, "Design-level file schema for PROWL"),
  caption("Figure A2. Design-level schema requested for planning. It describes relationships among artifacts, not database tables to be implemented."),
  heading2("Minimum records"),
  dataTable(
    ["record", "minimum fields", "control provided"],
    [
      ["Unified manifest", "source, case identifier, patient-group key, file paths, label provenance, validation status", "Single auditable inventory across imaging sources."],
      ["Frozen cohort", "purpose, member identifiers, checksum, timestamp", "Reproducible and leakage-resistant train/validation/test membership."],
      ["Run record", "configuration, seed, code version, cohort checksum, model artifact, metrics, decision", "A result can be reproduced and compared fairly."],
      ["Prediction and review", "scan/model identifiers, mask path, measurements, score, accept/edit/reject decision", "Every displayed contour and reviewer action remains traceable."],
      ["Evidence record", "source citation, passage identifiers, summary or refusal, grounding scores", "The literature assistant cannot hide its evidence path."],
    ],
    [1850, 5000, 3230]
  ),
  heading2("Storage tiers"),
  rich([
    { text: "Original files: ", bold: true, color: NAVY },
    { text: "compressed source volumes, labels, and checksums remain read-only on the external drive. " },
    { text: "Working files: ", bold: true, color: NAVY },
    { text: "preprocessed arrays and frozen manifests use the internal SSD or a mirrored rented-compute volume. " },
    { text: "Artifacts: ", bold: true, color: NAVY },
    { text: "configurations, checkpoints, predictions, metrics, reviews, and retrieval-index files are versioned in project output directories, with keeper artifacts backed up." },
  ]),

  heading1("A5. Model Experimentation and Evaluation", true),
  body("The prior project contributes a validated pipeline, error analysis, and experience with transfer learning. Its trained model will not be reused as the capstone model. PROWL will establish a new autonomous baseline and use measured errors to choose the next experiment."),
  heading2("Experiment categories—not fixed commitments"),
  dataTable(
    ["question", "illustrative options", "decision evidence"],
    [
      ["What model family or initialization is most useful?", "From-scratch and pretrained baselines; architecture comparisons where compute permits.", "Held-out lesion and pancreas accuracy, stability, and resource cost."],
      ["How should localization and segmentation interact?", "Single-stage processing, cascaded regions, or other anatomy-aware approaches.", "Autonomous-versus-provided-region accuracy loss and failure analysis."],
      ["How should false alarms be controlled?", "Training, calibration, post-processing, or context experiments selected from the baseline errors.", "Patient-level sensitivity/specificity curve and lesion-size analysis."],
      ["Would a larger or compressed model help?", "Ensembling, distillation, or another scaling strategy only if core results justify the effort.", "Incremental accuracy, inference cost, and implementation complexity."],
    ],
    [3000, 3860, 3220]
  ),
  body("Each comparison begins with a written hypothesis. Training and evaluation data, preprocessing, and metrics remain fixed unless one is the variable under study. A modeling strategy is adopted only when the full result—including errors and resource cost—supports it."),
  heading2("Evaluation contract"),
  dataTable(
    ["metric or analysis", "purpose"],
    [
      ["Pancreas Dice and lesion Dice, reported separately", "Prevents strong organ segmentation from hiding weak lesion performance."],
      ["Patient-level sensitivity and specificity", "Measures the review-worklist tradeoff, including healthy cases left unflagged."],
      ["Full-volume autonomous inference", "Tests the system that will actually be demonstrated rather than isolated training patches."],
      ["Provided-region reference versus autonomous system", "Quantifies the accuracy cost of removing the human-supplied region."],
      ["Per-case error analysis and subgroup results", "Identifies failure patterns by lesion size, source, annotation quality, and acquisition factors."],
      ["Runtime, storage, and experiment cost", "Keeps model improvements proportional to practical resource requirements."],
    ],
    [3800, 6280]
  ),
  rich([
    { text: "Starting reference. ", bold: true, color: NAVY },
    { text: "The preceding provided-region model detected tumors in 96% of positive patients but correctly left only 17% of healthy patients unflagged. That result motivates the capstone’s autonomous localization and false-alarm experiments; it is not presented as the capstone result." },
  ]),

  heading1("A6. Evidence-Support Workflow", true),
  body("The literature assistant retrieves peer-reviewed passages related to structured imaging findings. It does not retrieve from patient data, classify a tumor type, recommend treatment, or replace the reviewer’s judgment."),
  heading2("Example source record"),
  dataTable(
    ["field", "example"],
    [
      ["Identifier", "PMID 39865461"],
      ["Title", "Artificial Intelligence in Pancreatic Imaging: A Systematic Review"],
      ["Journal / year", "United European Gastroenterology Journal / 2025"],
      ["Indexed descriptors", "Artificial intelligence; deep learning; pancreatic neoplasms; pancreas; imaging"],
      ["Retrievable text", "Abstract or licensed full-text passage; records without usable text are excluded and counted."],
    ],
    [2200, 7880]
  ),
  heading2("Query and generation boundary"),
  dataTable(
    ["step", "example", "system responsibility"],
    [
      ["Structured finding", "Pancreatic head; suspected lesion; 24 mm maximum diameter; portal-venous CT.", "Produced by the imaging workflow and available for review."],
      ["Reviewer question", "What literature discusses CT evaluation of pancreatic lesions?", "Supplied by the reviewer; not interpreted as a diagnostic request."],
      ["Retrieval query", "Terms are constructed from the finding fields and question, then used to retrieve top passages.", "Software constructs the evidence query; retrieval returns source passages and citation identifiers."],
      ["Generated response", "A short summary limited to the retrieved passages, with citations beside supported statements.", "The LLM generates the response—not the evidence. If the passages are insufficient, it refuses."],
    ],
    [1800, 4250, 4030]
  ),
  callout("Direct answer to the professor’s question.", "The query is constructed from structured finding fields and the reviewer’s question. Retrieval pulls the text evidence. The language model then summarizes only that retrieved evidence or returns an insufficient-evidence refusal."),
  heading2("Evaluation and stretch boundary"),
  bullet("Retrieval quality: recall at k and mean reciprocal rank on a held-out question-and-source set."),
  bullet("Response quality: groundedness rate and refusal accuracy on deliberately unsupported questions."),
  bullet("PanTS narrative-text incorporation: stretch work only, estimated at three to five working days after the core corpus and imaging system are functioning."),

  heading1("A7. Existing Foundation and New Capstone Work", true),
  dataTable(
    ["foundation from the preceding project", "new PROWL work", "completion evidence"],
    [
      ["Experience preparing and evaluating 3D medical images", "Validate and reconcile the three-source design across PanTS, PANORAMA, and the literature corpus.", "Manifest, overlap report, source-quality checks, and frozen cohorts."],
      ["Reusable training, evaluation, and experiment-tracking structure", "Model experimentation for a newly trained autonomous localization-and-segmentation system.", "Controlled comparisons with recorded adopt/reject decisions."],
      ["Prior provided-region results and error analysis", "Measure autonomous performance and the sensitivity/specificity tradeoff.", "Side-by-side autonomous and provided-region reference results."],
      ["Experience with an imaging service and review interface", "Integrate new predictions, measurements, evidence retrieval, and persisted reviewer decisions.", "End-to-end demonstration from scan arrival to recorded review."],
    ],
    [3300, 4200, 2580]
  ),
  body("The prior pipeline is scaffolding and knowledge, not a completed capstone model. The central capstone evidence is a newly evaluated autonomous workflow operating on a broader, controlled data design."),

  heading1("A8. Risks, Fallbacks, and Scope Control", true),
  dataTable(
    ["risk", "response"],
    [
      ["The first model experiment returns a null result.", "Report it honestly, retain the baseline, and choose the next experiment from the measured failure mode."],
      ["Autonomous localization loses accuracy.", "Report autonomous and provided-region reference results side by side; the comparison remains a valid capstone result."],
      ["Cross-source integration introduces label or provenance noise.", "Train and report by source quality, preserve provenance, and use a source-specific ablation before broad inclusion."],
      ["Specificity cannot improve without losing too much sensitivity.", "Report the full operating-point curve and lesion-size errors rather than selecting one favorable threshold."],
      ["Local training throughput is insufficient.", "Profile first, mirror only the working data to rented compute, and re-establish the baseline before new comparisons."],
      ["The literature assistant produces unsupported language.", "Treat it as a defect, enforce cite-or-refuse behavior, and disable the supporting feature if groundedness gates are not met."],
      ["Scope expands across two workstreams.", "Core imaging milestones take priority; PanTS text, richer reporting, external evaluation, and additional experiments remain optional."],
    ],
    [4100, 5980]
  ),

  heading1("A9. Data Use, Attribution, and Reproducibility", true),
  body("PanTS and PANORAMA are available for non-commercial research use. PROWL is an academic capstone and is not presented as a commercial or clinical diagnostic product. Source licenses, dataset versions, and repository commit identifiers will be recorded with every reproducible run."),
  dataTable(
    ["source", "use and attribution boundary"],
    [
      ["PanTS", "Non-commercial research use; cite the PanTS dataset publication and preserve its dataset split and provenance requirements."],
      ["PANORAMA", "CC BY-NC 4.0; cite the study protocol and record the labels-repository commit used for reconciliation."],
      ["PubMed/PMC literature", "Store bibliographic metadata and only text that may be retrieved under the applicable access terms; display citations beside supported statements."],
    ],
    [2400, 7680]
  ),
  heading2("Key references"),
  new Paragraph({
    style: "Reference",
    children: [textRun("Alves, N., Schuurmans, M., Rutkowski, D., et al. (2024). The PANORAMA Study Protocol: Pancreatic Cancer Diagnosis—Radiologists Meet AI. Zenodo. https://doi.org/10.5281/zenodo.10599559", { size: 19 })],
  }),
  new Paragraph({
    style: "Reference",
    children: [textRun("Li, W., Zhou, X., Chen, Q., Lin, T., Bassi, P. R. A. S., et al. (2025). PanTS: The Pancreatic Tumor Segmentation Dataset. NeurIPS 2025 Datasets and Benchmarks Track. arXiv:2507.01291.", { size: 19 })],
  }),
  new Paragraph({
    style: "Reference",
    children: [textRun("Antonelli, M., Reinke, A., Bakas, S., et al. (2022). The Medical Segmentation Decathlon. Nature Communications, 13, 4128. https://doi.org/10.1038/s41467-022-30695-9", { size: 19 })],
  }),
  new Paragraph({
    style: "Reference",
    children: [textRun("Suman, G., Patra, A., Korfiatis, P., et al. (2021). Assessment of pancreatic ductal adenocarcinoma using CT imaging. PMID 33840636.", { size: 19 })],
  }),
  callout("Reproducibility rule.", "A result is reportable only when its source files, manifest checksum, cohort membership, configuration, code version, model artifact, and evaluation output can be traced together."),
];

const document = new Document({
  title: "PROWL — BSAAI Capstone Technical Appendix",
  subject: "Pancreatic Review and Outlining Workflow for Lesions",
  creator: "Quinton Evans",
  description: "Technical design supplement for the PROWL BSAAI capstone proposal.",
  styles: {
    default: {
      document: { run: { font: "Georgia", size: 21, color: DARK } },
    },
    paragraphStyles: [
      {
        id: "BodyText",
        name: "Body Text",
        basedOn: "Normal",
        next: "BodyText",
        quickFormat: true,
        run: { font: "Georgia", size: 21, color: DARK },
        paragraph: { spacing: { after: 150, line: 280 } },
      },
      {
        id: "Reference",
        name: "Reference",
        basedOn: "BodyText",
        next: "Reference",
        quickFormat: true,
        run: { font: "Georgia", size: 19, color: DARK },
        paragraph: { indent: { left: 360, hanging: 360 }, spacing: { after: 120, line: 250 } },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "appendix-bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 420, hanging: 220 }, spacing: { after: 100, line: 270 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 900, right: 1080, bottom: 900, left: 1080 },
        },
      },
      children: cover,
    },
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 850, right: 1080, bottom: 850, left: 1080, footer: 450 },
          pageNumbers: { start: 1 },
        },
      },
      footers: { default: footer },
      children: content,
    },
  ],
});

Packer.toBuffer(document).then((buffer) => {
  fs.writeFileSync(OUTPUT, buffer);
  console.log(OUTPUT);
});
