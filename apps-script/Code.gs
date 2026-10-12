/** @OnlyCurrentDoc */
/**
 * HK Commercial Intelligence - shared PIC / status store.
 *
 * Paste this whole file into Extensions > Apps Script of a new Google Sheet,
 * change PASSCODE below, then Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone). Copy the web app URL into
 * config.json in the GitHub repository.
 *
 * The passcode is required to read or change assignments, so people without
 * it can still browse the events and office moves but cannot see or edit the
 * sales pipeline.
 */
const PASSCODE = 'CHANGE-ME';   // <-- set your team passcode here

const PICS = ['Magnum', 'Hin', 'Alan', 'Joyce', 'Ken', 'Peter', 'Jonathan'];
const STATUSES = ['Not started', 'Researching', 'Contacted', 'Meeting set', 'Proposal sent', 'Won', 'Lost', 'Not pursuing'];
const TRACKER_HEAD = ['id', 'pic', 'status', 'title', 'kind', 'url', 'itemDate', 'createdAt', 'updatedAt', 'updatedBy'];
const LOG_HEAD = ['at', 'itemId', 'title', 'kind', 'field', 'from', 'to', 'by'];

function doGet() {
  return out_({ ok: true, service: 'hk-commercial-intelligence' });
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_request' }); }
  if (!req || PASSCODE === 'CHANGE-ME' || req.passcode !== PASSCODE) return out_({ ok: false, error: 'bad_passcode' });

  if (req.action === 'read') return out_({ ok: true, tracker: readTracker_(), log: readLog_(300) });

  if (req.action === 'set') {
    const field = req.field, value = String(req.value || '');
    if (!/^[A-Za-z0-9_-]{6,40}$/.test(String(req.id || ''))) return out_({ ok: false, error: 'bad_id' });
    if (field !== 'pic' && field !== 'status') return out_({ ok: false, error: 'bad_field' });
    if (value && field === 'pic' && PICS.indexOf(value) < 0) return out_({ ok: false, error: 'bad_value' });
    if (value && field === 'status' && STATUSES.indexOf(value) < 0) return out_({ ok: false, error: 'bad_value' });

    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      const sh = sheet_('Tracker', TRACKER_HEAD);
      const data = sh.getDataRange().getValues();
      let row = -1;
      for (let i = 1; i < data.length; i++) if (String(data[i][0]) === req.id) { row = i; break; }
      const now = new Date().toISOString();
      const prev = row > 0 ? rowObj_(TRACKER_HEAD, data[row]) : {};
      const rec = {
        id: req.id,
        pic: prev.pic || '', status: prev.status || '',
        title: clean_(req.title || prev.title, 300), kind: clean_(req.kind || prev.kind, 20),
        url: clean_(req.url || prev.url, 1000), itemDate: clean_(req.itemDate || prev.itemDate, 20),
        createdAt: prev.createdAt || now, updatedAt: now, updatedBy: clean_(req.by, 60),
      };
      rec[field] = value;
      const vals = TRACKER_HEAD.map(function (k) { return rec[k]; });
      if (row > 0) sh.getRange(row + 1, 1, 1, vals.length).setValues([vals]);
      else sh.appendRow(vals);
      sheet_('Log', LOG_HEAD).appendRow([now, req.id, rec.title, rec.kind, field, prev[field] || '', value, rec.updatedBy]);
    } finally {
      lock.releaseLock();
    }
    return out_({ ok: true, tracker: readTracker_(), log: readLog_(300) });
  }
  return out_({ ok: false, error: 'bad_action' });
}

function readTracker_() {
  const data = sheet_('Tracker', TRACKER_HEAD).getDataRange().getValues();
  const out = {};
  for (let i = 1; i < data.length; i++) {
    const o = rowObj_(TRACKER_HEAD, data[i]);
    if (o.id) out[o.id] = o;
  }
  return out;
}

function readLog_(n) {
  const sh = sheet_('Log', LOG_HEAD);
  const last = sh.getLastRow();
  if (last < 2) return [];
  const start = Math.max(2, last - n + 1);
  const rows = sh.getRange(start, 1, last - start + 1, LOG_HEAD.length).getValues();
  return rows.map(function (r) { return rowObj_(LOG_HEAD, r); }).reverse();
}

function sheet_(name, head) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(head);
    sh.setFrozenRows(1);
  }
  return sh;
}

function rowObj_(head, row) {
  const o = {};
  head.forEach(function (k, i) { o[k] = row[i] instanceof Date ? row[i].toISOString() : String(row[i] == null ? '' : row[i]); });
  return o;
}

// Stops text from being treated as a spreadsheet formula.
function clean_(v, max) {
  let s = String(v == null ? '' : v).slice(0, max);
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
