/**
 * Fidelity sanity check — single-form builder (one-pass design)
 * --------------------------------------------------------------
 * Builds one Google Form from a Drive folder of screenshots.
 * Per stimulus the rater sees: image + Visual Believability + Copy Quality +
 * Would Fool a User (1–5 each) + Source (Ours / Real / Not sure) + Confidence.
 *
 * Stim numbering and the ours/real ground truth come from the embedded
 * MANIFEST array below, which mirrors
 * scripts/fidelity_check/screenshots/rating_manifest.json exactly. Keep
 * the two in sync if either changes.
 *
 * SETUP — what to do in Drive before running this script
 * --------------------------------------------------------------
 *   1. Make a Drive folder called something like "fidelity_check".
 *   2. Inside it, create two sub-folders named exactly:
 *          ours        (drop your 20 synthetic-site screenshots here,
 *                       keeping their ORIGINAL filenames)
 *          real        (drop your 20 real-phishing screenshots here,
 *                       keeping their ORIGINAL filenames)
 *      The script looks up each file by its original_name from the
 *      manifest, so don't rename them.
 *   3. Open the parent "fidelity_check" folder in Drive. Copy the long
 *      ID from the URL. Paste it into PARENT_FOLDER_ID below (full URL
 *      also accepted).
 *   4. Go to https://script.google.com → New project → paste this file
 *      in as Code.gs → Save.
 *   5. Click "Run" with build_form selected. First run will prompt for
 *      permissions (Drive read + Forms create).
 *   6. After it finishes, open View → Logs. Copy the form URL and
 *      share with raters.
 *   7. In Drive, open the form, go to the "Responses" tab, click the
 *      Sheets icon to create a linked response sheet for analysis.
 *
 * Traceability
 * --------------------------------------------------------------
 *   Each form question is titled like "stim_07 — Visual Believability".
 *   That becomes the response-sheet column header. Join "stim_NN" to the
 *   manifest's "number" field to recover source ("ours"/"real") and
 *   original_name for every rating.
 *
 * Notes
 * --------------------------------------------------------------
 *   - Images are embedded as blobs at build time. Raters do NOT need
 *     access to your Drive folder.
 *   - Apps Script has a 6-minute execution limit; this form has ~280
 *     items, which usually completes in ~4–5 minutes. If it times out,
 *     just re-run (a partial form will appear in Drive — delete it).
 *   - Re-running build_form creates a NEW form each time. Delete old
 *     ones from Drive if you iterate.
 */

// === CONFIG ===================================================
const PARENT_FOLDER_ID = '__PASTE_DRIVE_FOLDER_ID_OR_URL_HERE__';
const OURS_SUBFOLDER = 'ours';
const REAL_SUBFOLDER = 'real';

// Only needed for link_response_sheet(). Paste the form URL or ID after build_form() finishes.
const EXISTING_FORM_URL = '__PASTE_FORM_URL_OR_ID_HERE__';
// ==============================================================


// === MANIFEST (mirror of rating_manifest.json) ================
// Order here = display order in the form. stim_NN ID = number.
const MANIFEST = [
  { number:  1, source: 'ours', original_name: 'gov_portal' },
  { number:  2, source: 'ours', original_name: 'e7_ninite' },
  { number:  3, source: 'ours', original_name: 'news' },
  { number:  4, source: 'ours', original_name: 'e10_mychart' },
  { number:  5, source: 'real', original_name: 'Screenshot 2026-05-24 121110' },
  { number:  6, source: 'ours', original_name: 'support_chat' },
  { number:  7, source: 'real', original_name: 'at&t_eb3b9414c9d4' },
  { number:  8, source: 'ours', original_name: 'e8_chase' },
  { number:  9, source: 'real', original_name: 'Screenshot 2026-05-24 121223' },
  { number: 10, source: 'real', original_name: 'netflix_019c900f' },
  { number: 11, source: 'real', original_name: 'insta' },
  { number: 12, source: 'ours', original_name: 'freelance' },
  { number: 13, source: 'real', original_name: 'paypalscam' },
  { number: 14, source: 'ours', original_name: 'quiz_scam' },
  { number: 15, source: 'real', original_name: 'Screenshot 2026-05-24 121326' },
  { number: 16, source: 'ours', original_name: 'e18_linkedin' },
  { number: 17, source: 'real', original_name: 'blogspot' },
  { number: 18, source: 'real', original_name: 'Screenshot 2026-05-24 121306' },
  { number: 19, source: 'real', original_name: 'Screenshot 2026-05-24 121903' },
  { number: 20, source: 'real', original_name: 'at&t_ec96e404f777' },
  { number: 21, source: 'ours', original_name: 'adp' },
  { number: 22, source: 'real', original_name: 'Screenshot 2026-05-24 121344' },
  { number: 23, source: 'real', original_name: 'other_bc510e932e42' },
  { number: 24, source: 'ours', original_name: 'ecommerce' },
  { number: 25, source: 'ours', original_name: 'e14_oracle_no_timer' },
  { number: 26, source: 'ours', original_name: 'e17_amazon' },
  { number: 27, source: 'ours', original_name: 'virus_scanner' },
  { number: 28, source: 'real', original_name: 'sumitomo mit_dd0589f7294b' },
  { number: 29, source: 'real', original_name: 'trezor_t' },
  { number: 30, source: 'ours', original_name: 'saas_onboard' },
  { number: 31, source: 'ours', original_name: 'marketplace' },
  { number: 32, source: 'ours', original_name: 'dating_verify' },
  { number: 33, source: 'real', original_name: 'other_ab563686d333' },
  { number: 34, source: 'ours', original_name: 'crypto_platform' },
  { number: 35, source: 'real', original_name: 'usps_fccbf67c72e2' },
  { number: 36, source: 'real', original_name: 'other_1076bb6838fb' },
  { number: 37, source: 'ours', original_name: 'e23_netflix' },
  { number: 38, source: 'ours', original_name: 'e13_irs_no_timer' },
  { number: 39, source: 'real', original_name: 'facebook' },
  { number: 40, source: 'real', original_name: 'other_546d1e57efc1' },
];
// ==============================================================


function build_form() {
  const parent = DriveApp.getFolderById(extractFolderId_(PARENT_FOLDER_ID));
  const oursFiles = indexFolder_(getSubfolder_(parent, OURS_SUBFOLDER));
  const realFiles = indexFolder_(getSubfolder_(parent, REAL_SUBFOLDER));

  // Resolve each manifest entry to a Drive file. Hard-fail if anything
  // is missing — silent mismatches would corrupt the join.
  const stimuli = MANIFEST.map(function(m) {
    const lookup = (m.source === 'ours' ? oursFiles : realFiles);
    const file = lookup[m.original_name.toLowerCase() + '.png'];
    if (!file) {
      throw new Error(
        'Missing file in Drive: ' + m.source + '/' + m.original_name + '.png ' +
        '(stim #' + m.number + '). Upload it before running.'
      );
    }
    return {
      stim_id: 'stim_' + ('0' + m.number).slice(-2),
      number: m.number,
      source: m.source,
      original_name: m.original_name,
      file: file,
    };
  });

  Logger.log('Building form with ' + stimuli.length + ' stimuli...');
  const url = buildForm_(stimuli);
  Logger.log('');
  Logger.log('=== FORM DONE ===');
  Logger.log('Form URL (share with raters): ' + url);
  Logger.log('');
  Logger.log('Next step: open the form in Drive → Responses tab → click the');
  Logger.log('Sheets icon to create a linked response sheet. Then share the');
  Logger.log('URL above with your raters.');
}


// Link an already-built form to a fresh Google Sheet for response collection.
// Run this if the form's Responses tab is too laggy to use (common with image-
// heavy forms). Sheet appears in your Drive root. Paste EXISTING_FORM_URL above
// before running.
function link_response_sheet() {
  const formId = extractFormId_(EXISTING_FORM_URL);
  const form = FormApp.openById(formId);

  const sheetName = form.getTitle() + ' — Responses';
  const sheet = SpreadsheetApp.create(sheetName);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('=== RESPONSE SHEET LINKED ===');
  Logger.log('Form:  ' + form.getEditUrl());
  Logger.log('Sheet: ' + sheet.getUrl());
  Logger.log('');
  Logger.log('Any responses raters have already submitted are NOT retroactively');
  Logger.log('copied — only new submissions will land in the sheet. If you have');
  Logger.log('responses already, export them from the form first.');
}


// ---- Drive helpers ----

function extractFolderId_(s) {
  const m = String(s).match(/\/folders\/([a-zA-Z0-9_-]+)/);
  if (m) return m[1];
  return String(s).trim();
}

function extractFormId_(s) {
  // Accept the long form ID, /d/<id>/edit URLs, /e/<id>/viewform URLs, or bare ID.
  const m = String(s).match(/\/(?:d|e)\/([a-zA-Z0-9_-]+)/);
  if (m) return m[1];
  return String(s).trim();
}

function getSubfolder_(parent, name) {
  const it = parent.getFoldersByName(name);
  if (!it.hasNext()) {
    throw new Error('Missing subfolder "' + name + '" inside "' + parent.getName() + '". ' +
                    'Create it and put screenshots in it before running.');
  }
  return it.next();
}

function indexFolder_(folder) {
  // Returns { lowercase_filename: File } so manifest lookups are case-insensitive.
  const out = {};
  const iter = folder.getFiles();
  while (iter.hasNext()) {
    const f = iter.next();
    out[f.getName().toLowerCase()] = f;
  }
  return out;
}


// ---- Form construction ----

function addScale_(form, title, lowDesc, midDesc, highDesc) {
  const item = form.addScaleItem();
  item.setTitle(title);
  // Anchors live in help text above the scale (where the rater is already
  // looking). Endpoint labels under the scale are skipped because the
  // Forms UI truncates them at ~25 chars.
  item.setHelpText('1 = ' + lowDesc + '   ·   3 = ' + midDesc + '   ·   5 = ' + highDesc);
  item.setBounds(1, 5);
  item.setRequired(true);
}

function buildForm_(stimuli) {
  const form = FormApp.create('Website screenshot ratings');
  form.setDescription(
    "You'll see 40 website screenshots. For each one:\n" +
    "  • Rate it on 3 dimensions (visual believability, copy quality, " +
    "would-fool-a-user) on a 1–5 scale\n" +
    "  • Guess whether it's a real captured phishing site or a synthetic " +
    "site we built (Ours / Real / Not sure)\n" +
    "  • Mark your confidence in that guess\n\n" +
    "All questions are required. Allow about 15–20 minutes. Please do this " +
    "in one sitting."
  );
  form.setShowLinkToRespondAgain(false);
  form.setCollectEmail(false);
  form.setProgressBar(true);

  // Rater username — anonymized, chosen by the rater. Used to group their
  // responses for inter-rater agreement analysis.
  const rid = form.addTextItem();
  rid.setTitle('Username');
  rid.setHelpText('Pick any anonymized username you like (initials, nickname, ' +
                  'a made-up word — anything except your real name). Used only ' +
                  'to group your responses for analysis.');
  rid.setRequired(true);

  // Demographic — single, optional secondary finding.
  const demo = form.addMultipleChoiceItem();
  demo.setTitle('How would you describe your familiarity with phishing / web security?');
  demo.setChoiceValues(['Low', 'Medium', 'High']);
  demo.setRequired(true);

  for (let pos = 0; pos < stimuli.length; pos++) {
    const s = stimuli[pos];

    const pb = form.addPageBreakItem();
    pb.setTitle(s.stim_id + '   (' + (pos + 1) + ' of ' + stimuli.length + ')');

    form.addImageItem()
        .setImage(s.file.getBlob())
        .setTitle(s.stim_id);

    addScale_(form, s.stim_id + ' — Visual Believability',
      'obviously fake / amateur',
      'mixed cues',
      'indistinguishable from a real site');

    addScale_(form, s.stim_id + ' — Copy Quality',
      'awkward, errors, off-brand',
      'passable but uneven',
      'reads like genuine corporate copy');

    addScale_(form, s.stim_id + ' — Would Fool a User',
      'most users would spot it immediately',
      'some would fall, some would not',
      'a careful user would likely fall for it');

    const src = form.addMultipleChoiceItem();
    src.setTitle(s.stim_id + ' — Source');
    src.setHelpText('Is this a real captured phishing site, or a synthetic site we built?');
    src.setChoiceValues(['Ours (synthetic)', 'Real (captured phishing)', 'Not sure']);
    src.setRequired(true);

    const conf = form.addMultipleChoiceItem();
    conf.setTitle(s.stim_id + ' — Confidence');
    conf.setHelpText('How confident are you in your source guess above?');
    conf.setChoiceValues(['Low', 'Medium', 'High']);
    conf.setRequired(true);

    if ((pos + 1) % 5 === 0) {
      Logger.log('  ' + (pos + 1) + ' / ' + stimuli.length + ' stimuli added');
    }
  }

  return form.getPublishedUrl();
}
