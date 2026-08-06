const OWNER_EMAIL = 'swimnexar@gmail.com';

const EXP_LABELS = {
  none:        "Beginner (Can't swim independently)",
  strokes:     'Can swim freestyle & breaststroke',
  competitive: 'Competitive swimmer',
  waterpolo:   'Has played water polo before',
};

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    try { saveToSheet(data); } catch (sheetErr) { console.error('Sheet error:', sheetErr); }
    sendNotification(data);
  } catch (err) {
    console.error('doPost error:', err);
  }
  return ContentService.createTextOutput('ok').setMimeType(ContentService.MimeType.TEXT);
}

function doGet() {
  return ContentService.createTextOutput('ok').setMimeType(ContentService.MimeType.TEXT);
}

function getSheet() {
  const props = PropertiesService.getScriptProperties();
  let ssId = props.getProperty('SS_ID');
  let ss;
  if (ssId) {
    try { ss = SpreadsheetApp.openById(ssId); } catch (_) { ssId = null; }
  }
  if (!ssId) {
    ss = SpreadsheetApp.create('Swimnexar Registrations');
    props.setProperty('SS_ID', ss.getId());
  }

  // New sheet tab each month: "August 2026", "September 2026", etc.
  const now = new Date();
  const monthLabel = now.toLocaleString('en-US', { month: 'long', year: 'numeric', timeZone: 'America/New_York' });

  let sheet = ss.getSheetByName(monthLabel);
  if (!sheet) {
    sheet = ss.insertSheet(monthLabel);

    const headers = ['Timestamp', 'Program', 'Parent Name', 'Email', 'Phone', 'Child Name', 'Age', 'Experience', 'Waiver'];
    sheet.appendRow(headers);

    // Column header colors
    const colors = ['#4a86e8', '#6aa84f', '#e69138', '#cc4125', '#674ea7', '#45818e', '#bf9000', '#741b47', '#38761d'];
    headers.forEach(function(_, i) {
      const cell = sheet.getRange(1, i + 1);
      cell.setBackground(colors[i]);
      cell.setFontColor('#ffffff');
      cell.setFontWeight('bold');
      cell.setHorizontalAlignment('center');
    });

    // Freeze header row and resize columns
    sheet.setFrozenRows(1);
    sheet.setRowHeight(1, 32);
    sheet.autoResizeColumns(1, headers.length);
  }

  return sheet;
}

function saveToSheet(data) {
  const sheet = getSheet();
  sheet.appendRow([
    new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }),
    data.program    || '',
    data.parentName || '',
    data.email      || '',
    data.phone      || '',
    data.childName  || '',
    data.childAge   || '',
    EXP_LABELS[data.experience] || data.experience || '',
    data.waiver ? 'Yes' : 'No',
  ]);
}

function sendNotification(data) {
  const prog = data.program === 'swimteam' ? 'Swim Team' : 'Water Polo';

  // Notification to owner
  const ownerSubject = `New ${prog} Registration — ${data.childName || '?'}`;
  const ownerBody = [
    `Program:    ${prog}`,
    `Child:      ${data.childName  || ''}`,
    `Age:        ${data.childAge   || ''}`,
    `Parent:     ${data.parentName || ''}`,
    `Email:      ${data.email      || ''}`,
    `Phone:      ${data.phone      || ''}`,
    `Experience: ${EXP_LABELS[data.experience] || data.experience || ''}`,
    `Waiver:     ${data.waiver ? 'Accepted' : 'Not accepted'}`,
    '',
    `Time: ${new Date().toLocaleString('en-US', { timeZone: 'America/New_York' })} ET`,
  ].join('\n');
  MailApp.sendEmail(OWNER_EMAIL, ownerSubject, ownerBody);

  // Confirmation to registrant
  if (!data.email) return;

  const childName  = data.childName  || 'your child';
  const parentName = data.parentName || '';

  let clientSubject, clientBody;

  if (data.program === 'swimteam') {
    clientSubject = 'Your Swim Team Registration — Nexar Swim Team';
    clientBody = [
      `Hi ${parentName},`,
      '',
      `Thank you for registering ${childName} for our Nexar Swim Team program!`,
      '',
      `We have successfully received your registration. Our practices take place:`,
      '',
      `Tuesday & Thursday`,
      `📍 2910 Sports Core Cir, Wesley Chapel, FL 33544`,
      '',
      `Practice Schedule:`,
      `5:00 PM – Beginner Group`,
      `6:00 PM – Youth Group`,
      '',
      `${childName} is welcome to attend a trial session on either practice day. Please reply and let me know which day works best for you so I can be ready to welcome you at the pool.`,
      '',
      `What to bring:`,
      `- Swimsuit`,
      `- Towel`,
      `- Goggles`,
      `- Water bottle`,
      '',
      `If you have any questions, feel free to reach out.`,
      `Looking forward to seeing you at practice!`,
      '',
      `Warm regards,`,
      `Coach Alex`,
      `Nexar Swim Team`,
      `📧 swimnexar@gmail.com`,
      `🌐 www.swimnexar.com`,
    ].join('\n');
  } else {
    clientSubject = 'Your Water Polo Registration — Nexar Water Polo Club';
    clientBody = [
      `Hi ${parentName},`,
      '',
      `Thank you for submitting your form for a Nexar Water Polo free trial practice.`,
      '',
      `We have successfully received your registration. ${childName} is welcome to attend one free trial practice at either of our locations:`,
      '',
      `Land O' Lakes Recreation Center`,
      `Monday, Wednesday, and Friday`,
      `8:00 PM – 9:45 PM`,
      '',
      `Temple Terrace Aquatic Center`,
      `Tuesday and Thursday`,
      `6:45 PM – 8:30 PM`,
      '',
      `Please reply to this email and let me know which location and practice day work best for you, so I can be prepared to welcome you at the pool.`,
      '',
      `What to bring:`,
      `- Swimsuit`,
      `- Towel`,
      `- Goggles`,
      `- Water bottle`,
      '',
      `All water polo equipment will be provided.`,
      '',
      `If you have any questions, please don't hesitate to reply to this email. I'll be happy to help.`,
      '',
      `Looking forward to seeing ${childName} at practice!`,
      '',
      `Warm regards,`,
      `Coach Alex`,
      `Nexar Water Polo Club`,
      `swimnexar@gmail.com`,
    ].join('\n');
  }

  MailApp.sendEmail(data.email, clientSubject, clientBody);
}

function testSwimTeam() {
  sendNotification({
    program: 'swimteam',
    childName: 'Max',
    childAge: '10',
    parentName: 'Alex',
    email: 'alexmpwr@gmail.com',
    phone: '555-0000',
    experience: 'strokes',
    waiver: true,
  });
}

function testWaterPolo() {
  sendNotification({
    program: 'waterpolo',
    childName: 'Test Child',
    childAge: '12',
    parentName: 'Test Parent',
    email: 'alexmpwr@gmail.com',
    phone: '555-0000',
    experience: 'none',
    waiver: true,
  });
}

function setupSheet() {
  const props = PropertiesService.getScriptProperties();
  props.deleteProperty('SS_ID');
  getSheet();
  const ssId = props.getProperty('SS_ID');
  const url = SpreadsheetApp.openById(ssId).getUrl();
  Logger.log('Sheet URL: ' + url);
}

function testSheet() {
  const data = {
    program: 'swimteam', childName: 'Max', childAge: '10',
    parentName: 'Alex', email: 'alexmpwr@gmail.com',
    phone: '555-0000', experience: 'strokes', waiver: true,
  };
  saveToSheet(data);
}
