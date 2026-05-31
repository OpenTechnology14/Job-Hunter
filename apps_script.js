/**
 * Google Apps Script — Add a "Scrape Jobs" button to your Google Sheet.
 *
 * SETUP:
 * 1. Open your Google Sheet
 * 2. Go to Extensions → Apps Script
 * 3. Delete the default code, paste this entire file
 * 4. Click Save
 * 5. Go back to the sheet — you'll see a new "Job Hunter" menu
 *
 * HOW IT WORKS:
 * The "Run Scrape" button calls a webhook URL on your local machine.
 * You need to run a tiny local server that listens for the webhook
 * and kicks off the scraper. See webhook_server.py.
 *
 * ALTERNATIVE (simpler):
 * If you don't want to run a webhook server, just use the
 * "Add Timestamp" button to mark when you last scraped,
 * and run `python run_scrape.py` manually from your terminal.
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Job Hunter')
    .addItem('🔍 Run Scrape (manual reminder)', 'addScrapeTimestamp')
    .addItem('📊 Summary', 'showSummary')
    .addItem('✅ Mark Selected as Ready', 'markReady')
    .addItem('⏭️ Mark Selected as Skip', 'markSkip')
    .addToUi();
}

/**
 * Adds a timestamp note reminding you to run the scraper locally.
 */
function addScrapeTimestamp() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var now = new Date().toLocaleString();
  SpreadsheetApp.getUi().alert(
    'Run Scraper',
    'Open your terminal and run:\n\n' +
    'python run_scrape.py --profile <name>\n\n' +
    'Last reminder: ' + now,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Shows a summary of job counts by status and category.
 */
function showSummary() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet()
    .getSheetByName('Job Tracker');
  if (!sheet) {
    SpreadsheetApp.getUi().alert('No "Job Tracker" sheet found.');
    return;
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var statusCol = headers.indexOf('Status');
  var catCol = headers.indexOf('Role Category');
  var methodCol = headers.indexOf('Apply Method');

  if (statusCol === -1) {
    SpreadsheetApp.getUi().alert('Status column not found.');
    return;
  }

  var statusCounts = {};
  var catCounts = {};
  var methodCounts = {};

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (!row[0]) continue; // skip empty rows

    var status = row[statusCol] || 'Unknown';
    var cat = row[catCol] || 'Unknown';
    var method = row[methodCol] || 'Unknown';

    statusCounts[status] = (statusCounts[status] || 0) + 1;
    catCounts[cat] = (catCounts[cat] || 0) + 1;
    methodCounts[method] = (methodCounts[method] || 0) + 1;
  }

  var msg = 'TOTAL: ' + (data.length - 1) + ' jobs\n\n';

  msg += 'BY STATUS:\n';
  for (var s in statusCounts) msg += '  ' + s + ': ' + statusCounts[s] + '\n';

  msg += '\nBY CATEGORY:\n';
  for (var c in catCounts) msg += '  ' + c + ': ' + catCounts[c] + '\n';

  msg += '\nBY APPLY METHOD:\n';
  for (var m in methodCounts) msg += '  ' + m + ': ' + methodCounts[m] + '\n';

  SpreadsheetApp.getUi().alert('Job Hunter Summary', msg, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Mark selected rows as "Ready to Apply"
 */
function markReady() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getActiveRange();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var statusCol = headers.indexOf('Status') + 1;

  if (statusCol === 0) {
    SpreadsheetApp.getUi().alert('Status column not found.');
    return;
  }

  var startRow = range.getRow();
  var numRows = range.getNumRows();
  var count = 0;

  for (var i = 0; i < numRows; i++) {
    var row = startRow + i;
    if (row <= 1) continue; // skip header
    sheet.getRange(row, statusCol).setValue('✅ Ready to Apply');
    count++;
  }

  SpreadsheetApp.getUi().alert(count + ' jobs marked as Ready to Apply.\n\nRun: python run_apply.py --profile <name>');
}

/**
 * Mark selected rows as "Skip"
 */
function markSkip() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getActiveRange();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var statusCol = headers.indexOf('Status') + 1;

  if (statusCol === 0) {
    SpreadsheetApp.getUi().alert('Status column not found.');
    return;
  }

  var startRow = range.getRow();
  var numRows = range.getNumRows();
  var count = 0;

  for (var i = 0; i < numRows; i++) {
    var row = startRow + i;
    if (row <= 1) continue;
    sheet.getRange(row, statusCol).setValue('⏭️ Skipped');
    count++;
  }

  SpreadsheetApp.getUi().alert(count + ' jobs marked as Skipped.');
}
