/** @OnlyCurrentDoc */
/**
 * HK Commercial Intelligence - shared priority / PIC / status / comments store.
 *
 * Paste this whole file into Extensions > Apps Script of the team Google Sheet,
 * set PASSCODE below, then Deploy > Manage deployments > Edit > Version: New version > Deploy.
 * Run testEmail() once from the editor to allow assignment emails.
 *
 * Team tab: put each salesperson's email next to their name. Those addresses stay
 * in this sheet; they are never sent to the website.
 */
const PASSCODE = 'CHANGE-ME';   // <-- set your team passcode here

const PICS = ['Magnum', 'Hin', 'Alan', 'Joyce', 'Ken', 'Peter', 'Jonathan'];
const LEVELS = ['HIGH', 'MEDIUM', 'LOW'];
const NOTIFY_KINDS = ['event'];          // send an email when someone is assigned to these item types
const DASHBOARD_URL = 'https://xl888163.github.io/hk-commercial-intelligence/';
// New columns are only ever added at the end, so existing sheets keep working.
const TRACKER_HEAD = ['id', 'pic', 'status', 'title', 'kind', 'url', 'itemDate', 'createdAt', 'updatedAt', 'updatedBy', 'priority', 'systemLevel', 'features'];
const LOG_HEAD = ['at', 'itemId', 'title', 'kind', 'field', 'from', 'to', 'by'];
const COMMENT_HEAD = ['at', 'itemId', 'title', 'kind', 'by', 'text'];
const TEAM_HEAD = ['Name', 'Email'];

function doGet() {
  return out_({ ok: true, service: 'hk-commercial-intelligence' });
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_request' }); }
  if (!req || PASSCODE === 'CHANGE-ME' || req.passcode !== PASSCODE) return out_({ ok: false, error: 'bad_passcode' });
  if (req.action === 'read') return state_({});
  if (!/^[A-Za-z0-9_-]{6,40}$/.test(String(req.id || ''))) return out_({ ok: false, error: 'bad_id' });

  if (req.action === 'comment') {
    const text = String(req.text || '').trim();
    if (!text || text.length > 2000) return out_({ ok: false, error: 'bad_value' });
    const now = new Date().toISOString();
    sheet_('Comments', COMMENT_HEAD).appendRow([now, req.id, clean_(req.title, 300), clean_(req.kind, 20), clean_(req.by, 60), clean_(text, 2000)]);
    sheet_('Log', LOG_HEAD).appendRow([now, req.id, clean_(req.title, 300), clean_(req.kind, 20), 'comment', '', clean_(text.slice(0, 120), 120), clean_(req.by, 60)]);
    return state_({});
  }

  if (req.action === 'set') {
    const field = req.field, value = String(req.value || '');
    if (['pic', 'status', 'priority'].indexOf(field) < 0) return out_({ ok: false, error: 'bad_field' });
    if (value && field === 'priority' && LEVELS.indexOf(value) < 0) return out_({ ok: false, error: 'bad_value' });
    if (value && field === 'pic' && PICS.indexOf(value) < 0) return out_({ ok: false, error: 'bad_value' });
    if (value && field === 'status' && !/^[A-Za-z][A-Za-z /&\-]{1,39}$/.test(value)) return out_({ ok: false, error: 'bad_value' });

    let prev = {}, rec = {};
    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      const sh = sheet_('Tracker', TRACKER_HEAD);
      const data = sh.getDataRange().getValues();
      let row = -1;
      for (let i = 1; i < data.length; i++) if (String(data[i][0]) === req.id) { row = i; break; }
      const now = new Date().toISOString();
      prev = row > 0 ? rowObj_(TRACKER_HEAD, data[row]) : {};
      rec = {
        id: req.id,
        pic: prev.pic || '', status: prev.status || '', priority: prev.priority || '',
        systemLevel: field === 'priority' ? clean_(req.systemLevel, 10) : (prev.systemLevel || ''),
        features: field === 'priority' ? clean_(req.features, 2000) : (prev.features || ''),
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
    let email = null;
    if (field === 'pic' && value && value !== prev.pic && NOTIFY_KINDS.indexOf(rec.kind) >= 0) {
      email = notify_(value, rec, req.notify || {}, req.by);
    }
    return state_({ email: email });
  }
  return out_({ ok: false, error: 'bad_action' });
}

// ---------- email on assignment ----------
function notify_(pic, rec, n, by) {
  const to = teamEmail_(pic);
  if (!to) return { sent: false, to: pic, reason: 'no_email' };
  const esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  const steps = (n.actions || []).slice(0, 8).map(function (a) { return '<li>' + esc(a) + '</li>'; }).join('');
  const html =
    '<p>Hi ' + esc(pic) + ',</p>' +
    '<p>' + esc(by || 'A teammate') + ' assigned you to an industry event on HK Commercial Intelligence.</p>' +
    '<table cellpadding="4" style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px">' +
    '<tr><td><b>Event</b></td><td>' + esc(rec.title) + '</td></tr>' +
    '<tr><td><b>Date</b></td><td>' + esc(n.when) + '</td></tr>' +
    '<tr><td><b>Venue</b></td><td>' + esc(n.venue) + '</td></tr>' +
    '<tr><td><b>Access</b></td><td>' + esc(n.access) + '</td></tr>' +
    (n.organiser ? '<tr><td><b>Organiser</b></td><td>' + esc(n.organiser) + '</td></tr>' : '') +
    '</table>' +
    (steps ? '<p><b>Action plan</b></p><ol>' + steps + '</ol>' : '') +
    '<p><a href="' + esc(rec.url) + '">Event listing</a> &middot; <a href="' + DASHBOARD_URL + '">Open the dashboard</a></p>';
  try {
    MailApp.sendEmail({ to: to, subject: 'Assigned: ' + rec.title + (n.when ? ' (' + n.when + ')' : ''), htmlBody: html, name: 'HK Commercial Intelligence' });
    return { sent: true, to: pic };
  } catch (err) {
    return { sent: false, to: pic, reason: 'send_failed' };
  }
}

function teamEmail_(name) {
  const data = sheet_('Team', TEAM_HEAD).getDataRange().getValues();
  if (data.length < 2) PICS.forEach(function (p) { sheet_('Team', TEAM_HEAD).appendRow([p, '']); });
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]).trim().toLowerCase() === name.toLowerCase()) {
      const e = String(data[i][1]).trim();
      return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e) ? e : '';
    }
  }
  return '';
}

// Run once from the editor (select testEmail, click Run) to allow sending email; it sends a test to you.
function testEmail() {
  const team = sheet_('Team', TEAM_HEAD);
  if (team.getLastRow() < 2) PICS.forEach(function (p) { team.appendRow([p, '']); });
  const me = Session.getEffectiveUser().getEmail();
  MailApp.sendEmail(me, 'HK Commercial Intelligence: assignment emails are on', 'This confirms the dashboard can send assignment emails. Fill in the Team tab with each salesperson\'s email.');
}

// ---------- reads ----------
function state_(extra) {
  return out_(Object.assign({ ok: true, tracker: readTracker_(), log: readLog_(300), comments: readComments_(1500), team: teamNames_() }, extra));
}

function teamNames_() {
  // only which names have an email set (never the addresses themselves)
  const data = sheet_('Team', TEAM_HEAD).getDataRange().getValues();
  const out = {};
  for (let i = 1; i < data.length; i++) out[String(data[i][0]).trim()] = /@/.test(String(data[i][1]));
  return out;
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

function readComments_(n) {
  const sh = sheet_('Comments', COMMENT_HEAD);
  const last = sh.getLastRow();
  if (last < 2) return {};
  const start = Math.max(2, last - n + 1);
  const rows = sh.getRange(start, 1, last - start + 1, COMMENT_HEAD.length).getValues();
  const out = {};
  rows.reverse().forEach(function (r) {
    const o = rowObj_(COMMENT_HEAD, r);
    (out[o.itemId] = out[o.itemId] || []).push({ at: o.at, by: o.by, text: o.text });
  });
  return out;
}

// ---------- helpers ----------
function sheet_(name, head) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(head);
    sh.setFrozenRows(1);
    return sh;
  }
  const have = sh.getLastColumn();
  if (have < head.length) sh.getRange(1, have + 1, 1, head.length - have).setValues([head.slice(have)]);
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
