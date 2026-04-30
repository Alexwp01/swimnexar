/**
 * SWIMNEXAR — Google Apps Script
 * Receives form submissions → writes to Google Sheets + sends email notification
 *
 * SETUP INSTRUCTIONS (5 minutes):
 * 1. Go to https://script.google.com → New project
 * 2. Paste this entire file
 * 3. Edit NOTIFICATION_EMAIL below (your email)
 * 4. Click Deploy → New deployment → Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5. Click Deploy → copy the Web App URL
 * 6. Open js/main.js → paste the URL into APPS_SCRIPT_URL at the top
 * 7. Done! Every form submission goes to Sheets + your email.
 */

const NOTIFICATION_EMAIL = 'swimnexar@gmail.com';
const SHEET_NAME = 'Registrations';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    const sheet = getOrCreateSheet();

    // Add header row on first run
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        'Date / Time',
        'Parent Name',
        "Child's Name",
        'Email',
        'Phone',
        'Program',
        "Child's Age",
        'Experience',
        'Message'
      ]);
      // Style header row
      const headerRange = sheet.getRange(1, 1, 1, 9);
      headerRange.setFontWeight('bold');
      headerRange.setBackground('#0a1628');
      headerRange.setFontColor('#ffffff');
    }

    // Append the submission
    sheet.appendRow([
      data.submittedAt || new Date().toLocaleString(),
      data.parentName  || '',
      data.childName   || '',
      data.email       || '',
      data.phone       || '',
      data.program     || '',
      data.childAge    || '',
      data.experience  || '',
      data.message     || ''
    ]);

    // Auto-resize columns for readability
    sheet.autoResizeColumns(1, 9);

    // Send email notification
    sendNotificationEmail(data);

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'success' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log('Error: ' + err.toString());
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  return ContentService.createTextOutput('Swimnexar Form API is running ✅');
}

function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  return sheet;
}

function sendNotificationEmail(data) {
  const subject = `🏊 New Registration: ${data.parentName} — ${data.program}`;
  const htmlBody = `
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#0a1628;padding:24px;border-radius:12px 12px 0 0;">
        <h2 style="color:#00c6ff;margin:0;">New Registration — Swimnexar</h2>
      </div>
      <div style="background:#f0f7ff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e2eaf4;">
        <table style="width:100%;border-collapse:collapse;">
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;width:140px;">Parent Name</td>
            <td style="padding:10px 0;color:#1e293b;">${data.parentName || '—'}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Child's Name</td>
            <td style="padding:10px 0;color:#1e293b;">${data.childName || '—'}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Email</td>
            <td style="padding:10px 0;"><a href="mailto:${data.email}" style="color:#0072ff;">${data.email || '—'}</a></td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Phone</td>
            <td style="padding:10px 0;"><a href="tel:${data.phone}" style="color:#0072ff;">${data.phone || '—'}</a></td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Program</td>
            <td style="padding:10px 0;color:#1e293b;"><strong>${data.program || '—'}</strong></td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Child's Age</td>
            <td style="padding:10px 0;color:#1e293b;">${data.childAge || '—'}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2eaf4;">
            <td style="padding:10px 0;font-weight:bold;color:#475569;">Experience</td>
            <td style="padding:10px 0;color:#1e293b;">${data.experience || '—'}</td>
          </tr>
          <tr>
            <td style="padding:10px 0;font-weight:bold;color:#475569;vertical-align:top;">Message</td>
            <td style="padding:10px 0;color:#1e293b;">${data.message || '—'}</td>
          </tr>
        </table>
        <div style="margin-top:24px;padding:16px;background:#ffffff;border-radius:8px;border-left:4px solid #00c6ff;">
          <p style="margin:0;font-size:14px;color:#475569;">Submitted: ${data.submittedAt || new Date().toLocaleString()}</p>
        </div>
        <div style="margin-top:24px;text-align:center;">
          <a href="mailto:${data.email}?subject=Re: Your Swimnexar Registration"
             style="display:inline-block;background:#00c6ff;color:#ffffff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;">
            Reply to ${data.parentName}
          </a>
        </div>
      </div>
      <p style="text-align:center;font-size:12px;color:#94a3b8;margin-top:16px;">
        swimnexar.com · Wesley Chapel, FL
      </p>
    </div>
  `;

  MailApp.sendEmail({
    to: NOTIFICATION_EMAIL,
    subject: subject,
    htmlBody: htmlBody,
  });
}
