// Nexar Aquatic Academy — Google Apps Script
// Paste this ENTIRE file into script.google.com to replace the existing code.
// After saving, click "Deploy" → "Manage deployments" → update the existing deployment.

var ADMIN_EMAIL = 'swimnexar@gmail.com';

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);

    // ── 1. Save to Google Sheets ──────────────────────────────────────
    var ss   = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName('Registrations');
    if (!sheet) {
      sheet = ss.insertSheet('Registrations');
      sheet.appendRow([
        'Timestamp', 'Program', 'Location', 'Parent Name', 'Child Name',
        'Email', 'Phone', 'Child Age', 'Swim Level', 'Pricing Plan', 'Message', 'Waiver'
      ]);
    }
    sheet.appendRow([
      new Date(),
      data.program      || '',
      data.location     || '',
      data.parentName   || '',
      data.childName    || '',
      data.email        || '',
      data.phone        || '',
      data.childAge     || '',
      data.experience   || data.swimLevel || '',
      data.pricingPlan  || '',
      data.message      || '',
      data.waiver ? 'Yes' : 'No'
    ]);

    // ── 2. Human-readable program label ──────────────────────────────
    var prog = data.program || '';
    var loc  = data.location || '';
    var programLabel =
      prog === 'swimteam'         ? 'Swim Team — Wesley Chapel' :
      prog === 'waterpolo-temple' ? 'Water Polo — Temple Terrace (Tue/Thu 7–8 PM)' :
      loc  === 'temple-terrace'   ? 'Water Polo — Temple Terrace (Tue/Thu 7–8 PM)' :
                                    'Water Polo — Land O\'Lakes (Mon/Wed/Fri 8–9:45 PM)';

    // ── 3. Notification email → Alex ─────────────────────────────────
    var adminSubject = '🆕 New registration: ' + (data.childName || '?') + ' — ' + programLabel;
    var adminBody =
      '🆕 NEW REGISTRATION\n'
      + '─────────────────────────────\n'
      + 'Program:    ' + programLabel + '\n'
      + 'Parent:     ' + (data.parentName || '') + '\n'
      + 'Child:      ' + (data.childName  || '') + ' · Age ' + (data.childAge || '?') + '\n'
      + 'Email:      ' + (data.email      || '') + '\n'
      + 'Phone:      ' + (data.phone      || '') + '\n'
      + 'Swim level: ' + (data.experience || data.swimLevel || 'not specified') + '\n'
      + (data.pricingPlan ? 'Pricing:    ' + data.pricingPlan + '\n' : '')
      + (data.message     ? 'Message:    ' + data.message     + '\n' : '')
      + '─────────────────────────────\n'
      + 'Reply directly to this email to contact the parent.';

    MailApp.sendEmail({
      to:          ADMIN_EMAIL,
      subject:     adminSubject,
      body:        adminBody,
      replyTo:     data.email || ADMIN_EMAIL
    });

    // ── 4. Confirmation email → parent ────────────────────────────────
    if (data.email) {
      var confirmSubject = '✅ Registration received — Nexar Aquatic Academy';
      var confirmBody =
        'Hi ' + (data.parentName || 'there') + ',\n\n'
        + 'We received your registration for ' + (data.childName || 'your child') + '!\n\n'
        + 'Program: ' + programLabel + '\n'
        + 'First practice is FREE — no commitment required.\n\n'
        + 'We\'ll reach out within 24 hours to confirm the details and welcome you to the team.\n\n'
        + 'Questions? We\'re always available:\n'
        + '  WhatsApp: +1 (838) 333-0666\n'
        + '  Email:    swimnexar@gmail.com\n\n'
        + 'See you on the water! 🤽\n\n'
        + '— Coach Alex\n'
        + 'Nexar Aquatic Academy\n'
        + 'swimnexar.com';

      MailApp.sendEmail({
        to:      data.email,
        subject: confirmSubject,
        body:    confirmBody,
        name:    'Nexar Aquatic Academy',
        replyTo: ADMIN_EMAIL
      });
    }

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
