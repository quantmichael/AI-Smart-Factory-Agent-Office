/**
 * AI Smart Factory Agent Office
 * 설문 + 응답 시트 + 분석 대시보드 + 개인별 빌드업 리포트(PDF)
 *
 * [사용 방법]
 * 1. Apps Script의 기존 코드를 전부 지우고 이 파일 전체를 붙여넣습니다.
 * 2. 저장 후 setupSurveySystem()을 1회 실행합니다.
 * 3. 권한 승인 후 실행 로그에서 설문/시트/리포트 폴더 링크를 확인합니다.
 * 4. 설문이 제출되면 자동으로:
 *    - 분석 탭 갱신
 *    - 개인별 Google Docs 리포트 생성
 *    - PDF 생성
 *    - 관리자 이메일 알림(선택)
 *
 * 기존 프로젝트의 Script Properties에 FORM_ID / SPREADSHEET_ID가 남아 있다면
 * 기존 설문과 응답 시트를 그대로 재사용합니다.
 */

// ======================================================
// 0. 설정
// ======================================================

const FORM_TITLE = 'AI Smart Factory Agent Office — 사용자 테스트 설문';
const SPREADSHEET_TITLE = 'AI Smart Factory Agent Office — 설문 응답 및 분석';
const REPORT_FOLDER_NAME = 'AI Smart Factory Agent Office — 빌드업 리포트';

// 6명 통합 리포트에서 읽을 최대 응답자 수
const COMBINED_REPORT_MAX_PEOPLE = 6;

const SEND_EMAIL_NOTIFICATIONS = true;
const NOTIFY_EMAIL = Session.getActiveUser().getEmail();

const INTRO_TEXT =
  '안녕하세요. AI Smart Factory Agent Office를 사용해 주셔서 감사합니다.\n' +
  '이 설문은 서비스를 개선하기 위한 목적으로만 사용됩니다.\n' +
  '소요 시간은 약 10분이며, 느끼신 그대로 편하게 답변해 주세요.';

const CONFIRMATION_TEXT =
  '응답해 주셔서 감사합니다. 제출과 동시에 빌드업 리포트가 자동 생성됩니다.';

// ======================================================
// 1. 설문 문항
// ======================================================

const TASKS = [
  '측정 샘플(정상/손상) 선택 후 진단 시작',
  '진단이 진행되는 동안 Agent Office 화면(5개 담당자 아이콘)에서 진행 상태 확인',
  '정상/이상 판정 결과 확인',
  '판정 근거(어떤 자료를 참고했는지) 확인',
  '다음에 점검해야 할 내용(점검 계획) 확인',
  '설비 이력(과거 진단 기록) 확인',
  '최종 보고서 확인',
];

const TASK_STATUS = ['완료', '부분완료', '미완료'];

const LIKERT_ITEMS = [
  '진단이 진행되는 과정을 이해하기 쉬웠다',
  '판정 근거를 확인하기 쉬웠다',
  '다음에 점검할 내용을 이해하기 쉬웠다',
  '최종 보고서 내용을 신뢰할 수 있었다',
  '화면(모바일·PC)이 보기 편했다',
  '실제 업무에 도움이 될 것 같다',
];

const LIKERT_COLUMNS = [
  '1 (전혀 아니다)',
  '2 (아니다)',
  '3 (보통이다)',
  '4 (그렇다)',
  '5 (매우 그렇다)',
];

const OPEN_QUESTIONS = [
  '가장 도움이 되었던 점은 무엇인가요?',
  '가장 불편했거나 개선이 필요한 점은 무엇인가요?',
  '기타 의견이나 제안이 있다면 자유롭게 적어 주세요.',
];

const JOB_CHOICES = ['설비 운영·정비', '생산·공정', '기획·관리', '연구개발'];
const CAREER_CHOICES = ['3년 미만', '3~10년', '10년 이상'];
const DEVICE_SKILL_CHOICES = ['익숙함', '보통', '어려움'];
const REUSE_CHOICES = ['예', '아니오', '잘 모르겠음'];

const GRID_TITLE_MOBILE = '[모바일] 각 단계의 테스트 결과를 표시해 주세요';
const GRID_TITLE_PC = '[PC·노트북] 각 단계의 테스트 결과를 표시해 주세요';
const GRID_TITLE_LIKERT = '아래 항목에 대해 동의하는 정도를 선택해 주세요';
const SCALE_TITLE = '전체 만족도';
const REUSE_TITLE = '다시 사용·추천 의향';

// ======================================================
// 2. 최초 설치 / 재연결
// ======================================================

function setupSurveySystem() {
  const props = PropertiesService.getScriptProperties();
  const oldFormId = props.getProperty('FORM_ID');
  const oldSsId = props.getProperty('SPREADSHEET_ID');

  // 기존 설문/시트가 있으면 그대로 사용
  if (oldFormId && oldSsId) {
    try {
      const form = FormApp.openById(oldFormId);
      const ss = SpreadsheetApp.openById(oldSsId);

      ensureReportFolder_();
      installOrRepairSubmitTrigger_(form);
      buildAnalysisDashboard();

      Logger.log('기존 설문 시스템을 재사용합니다.');
      logUrls_(form, ss);
      return;
    } catch (err) {
      Logger.log('기존 설문 정보를 열지 못해 새로 만듭니다: ' + err.message);
    }
  }

  // 새 설문과 새 응답 시트 생성
  const form = buildForm_();
  const ss = SpreadsheetApp.create(SPREADSHEET_TITLE);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  props.setProperty('FORM_ID', form.getId());
  props.setProperty('SPREADSHEET_ID', ss.getId());

  const folder = ensureReportFolder_();
  props.setProperty('REPORT_FOLDER_ID', folder.getId());

  Utilities.sleep(2500);

  installOrRepairSubmitTrigger_(form);

  try {
    buildAnalysisDashboard();
  } catch (err) {
    Logger.log('분석 탭 초기 생성 보류: ' + err.message);
  }

  Logger.log('설문 시스템 생성 완료');
  logUrls_(form, ss);
}

function resetSurveySystem() {
  const props = PropertiesService.getScriptProperties();

  props.deleteProperty('FORM_ID');
  props.deleteProperty('SPREADSHEET_ID');
  props.deleteProperty('REPORT_FOLDER_ID');

  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === 'onSurveySubmit_') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  Logger.log('저장 정보와 제출 트리거를 초기화했습니다.');
  Logger.log('기존 Form/Sheet/리포트 파일 자체는 삭제되지 않습니다.');
}

function logUrls_(form, ss) {
  const folder = ensureReportFolder_();

  Logger.log('====================================================');
  Logger.log('설문 응답 링크: ' + form.getPublishedUrl());
  Logger.log('설문 편집 링크: ' + form.getEditUrl());
  Logger.log('응답 스프레드시트: ' + ss.getUrl());
  Logger.log('빌드업 리포트 폴더: ' + folder.getUrl());
  Logger.log('====================================================');
}

// ======================================================
// 3. 설문 생성
// ======================================================

function buildForm_() {
  const form = FormApp.create(FORM_TITLE);

  form.setDescription(INTRO_TEXT);
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setShowLinkToRespondAgain(false);
  form.setConfirmationMessage(CONFIRMATION_TEXT);
  form.setProgressBar(true);

  form.addPageBreakItem()
    .setTitle('0. 응답자 정보')
    .setHelpText('개인 이름·연락처는 받지 않습니다.');

  form.addMultipleChoiceItem()
    .setTitle('담당 업무')
    .setChoiceValues(JOB_CHOICES)
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('경력')
    .setChoiceValues(CAREER_CHOICES)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('스마트기기 사용')
    .setChoiceValues(DEVICE_SKILL_CHOICES)
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('1. 테스트 진행')
    .setHelpText('모바일과 PC·노트북에서 각 단계를 확인해 주세요.');

  form.addGridItem()
    .setTitle(GRID_TITLE_MOBILE)
    .setRows(TASKS)
    .setColumns(TASK_STATUS)
    .setRequireOneResponsePerRow(false)
    .setRequired(false);

  form.addGridItem()
    .setTitle(GRID_TITLE_PC)
    .setRows(TASKS)
    .setColumns(TASK_STATUS)
    .setRequireOneResponsePerRow(false)
    .setRequired(false);

  form.addPageBreakItem().setTitle('2. 항목별 평가');

  form.addGridItem()
    .setTitle(GRID_TITLE_LIKERT)
    .setRows(LIKERT_ITEMS)
    .setColumns(LIKERT_COLUMNS)
    .setRequireOneResponsePerRow(true)
    .setRequired(true);

  form.addPageBreakItem().setTitle('3. 자유 의견');

  OPEN_QUESTIONS.forEach(function (q) {
    form.addParagraphTextItem()
      .setTitle(q)
      .setRequired(false);
  });

  form.addPageBreakItem().setTitle('4. 종합');

  form.addScaleItem()
    .setTitle(SCALE_TITLE)
    .setBounds(1, 5)
    .setLabels('전혀 만족하지 않음', '매우 만족')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle(REUSE_TITLE)
    .setChoiceValues(REUSE_CHOICES)
    .setRequired(true);

  return form;
}

// ======================================================
// 4. 제출 트리거
// ======================================================

function installOrRepairSubmitTrigger_(form) {
  // 중복 트리거 방지
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === 'onSurveySubmit_') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // 이메일 알림 여부와 관계없이 리포트 생성을 위해 항상 설치
  ScriptApp.newTrigger('onSurveySubmit_')
    .forForm(form)
    .onFormSubmit()
    .create();
}

// ======================================================
// 5. 설문 제출 시 자동 실행
// ======================================================

function onSurveySubmit_(e) {
  try {
    const answers = extractAnswers_(e);

    // 개인별 리포트 생성
    const report = createBuildUpReport_(answers);

    // 시트 반영 대기 후 분석 탭 갱신
    Utilities.sleep(1200);

    try {
      buildAnalysisDashboard();
    } catch (dashboardErr) {
      Logger.log('분석 대시보드 갱신 실패: ' + dashboardErr.message);
    }

    // 관리자 이메일
    if (SEND_EMAIL_NOTIFICATIONS && NOTIFY_EMAIL) {
      const summary = analyzeAnswers_(answers);

      const subject =
        '[설문 응답 + 빌드업 리포트 생성 완료] AI Smart Factory Agent Office';

      const body =
        '새로운 설문 응답이 도착했습니다.\n\n' +
        '담당 업무: ' + text_(answers['담당 업무']) + '\n' +
        '경력: ' + text_(answers['경력']) + '\n' +
        '전체 만족도: ' + text_(answers[SCALE_TITLE]) + '/5\n' +
        '항목별 평균: ' + summary.likertAverage.toFixed(2) + '/5\n' +
        '과업 완료율: ' + summary.taskCompletionRate.toFixed(1) + '%\n' +
        '종합 점수: ' + summary.totalScore.toFixed(1) + '/100\n' +
        '등급: ' + summary.grade + '\n\n' +
        'Google Docs 리포트:\n' + report.docUrl + '\n\n' +
        'PDF 파일:\n' + report.pdfUrl;

      MailApp.sendEmail(NOTIFY_EMAIL, subject, body);
    }

  } catch (err) {
    Logger.log('응답 처리 중 오류: ' + err.stack);
  }
}

// ======================================================
// 6. 이벤트에서 응답 추출
// ======================================================

function extractAnswers_(e) {
  const out = {};

  // 폼에 연결된 onFormSubmit 트리거
  if (e && e.response) {
    const items = e.response.getItemResponses();

    items.forEach(function (ir) {
      out[ir.getItem().getTitle()] = ir.getResponse();
    });

    out.__timestamp = e.response.getTimestamp();
    return out;
  }

  // 혹시 나중에 시트 트리거로 바꿨을 때 대비
  if (e && e.namedValues) {
    Object.keys(e.namedValues).forEach(function (key) {
      const v = e.namedValues[key];
      out[key] = Array.isArray(v) ? v[0] : v;
    });

    out.__timestamp = new Date();
  }

  return out;
}

// ======================================================
// 7. 점수 분석
// ======================================================

function analyzeAnswers_(answers) {
  const likertRaw = toArray_(answers[GRID_TITLE_LIKERT]);
  const mobile = toArray_(answers[GRID_TITLE_MOBILE]);
  const pc = toArray_(answers[GRID_TITLE_PC]);

  const likertScores = LIKERT_ITEMS
    .map(function (_, i) {
      return parseLeadingNumber_(likertRaw[i]);
    })
    .filter(function (v) {
      return !isNaN(v);
    });

  const likertAverage = likertScores.length
    ? likertScores.reduce(function (a, b) { return a + b; }, 0) / likertScores.length
    : 0;

  const mobileScore = taskScore_(mobile);
  const pcScore = taskScore_(pc);

  // 완료=1, 부분완료=0.5, 미완료/공란=0
  const taskMax = TASKS.length * 2;
  const taskEarned = mobileScore + pcScore;
  const taskCompletionRate = taskMax
    ? (taskEarned / taskMax) * 100
    : 0;

  const satisfaction = Number(answers[SCALE_TITLE]) || 0;

  // 종합 점수:
  // 항목별 평가 50 + 과업 완료 30 + 만족도 20
  const totalScore =
    (likertAverage / 5) * 50 +
    (taskCompletionRate / 100) * 30 +
    (satisfaction / 5) * 20;

  let grade = 'D';
  let diagnosis = '기초 사용 단계';
  let recommendation =
    '핵심 사용 흐름을 다시 확인하고 미완료 단계부터 반복 테스트하는 것을 권장합니다.';

  if (totalScore >= 90) {
    grade = 'A+';
    diagnosis = '매우 높은 활용 준비도';
    recommendation =
      '현재 사용 경험을 표준 업무 프로세스에 연결하고, 반복 업무 자동화와 보고서 활용까지 확장해 보세요.';
  } else if (totalScore >= 80) {
    grade = 'A';
    diagnosis = '높은 활용 준비도';
    recommendation =
      '판정 근거와 점검 계획을 실제 업무 의사결정 과정에 연결하는 단계로 확장해 보세요.';
  } else if (totalScore >= 70) {
    grade = 'B';
    diagnosis = '양호한 활용 준비도';
    recommendation =
      '부분완료 또는 이해도가 낮았던 항목을 중심으로 반복 사용하면 활용도가 빠르게 올라갈 수 있습니다.';
  } else if (totalScore >= 60) {
    grade = 'C';
    diagnosis = '보완이 필요한 활용 단계';
    recommendation =
      '화면 흐름과 판정 근거 확인 절차를 중심으로 짧은 재교육 또는 가이드 제공을 권장합니다.';
  }

  const strengths = [];
  const improvements = [];

  LIKERT_ITEMS.forEach(function (item, i) {
    const score = parseLeadingNumber_(likertRaw[i]);

    if (!isNaN(score)) {
      if (score >= 4) strengths.push(item);
      if (score <= 2) improvements.push(item);
    }
  });

  TASKS.forEach(function (task, i) {
    if (mobile[i] === '미완료' || pc[i] === '미완료') {
      improvements.push(task + ' 단계');
    }
  });

  return {
    likertAverage: likertAverage,
    taskCompletionRate: taskCompletionRate,
    satisfaction: satisfaction,
    totalScore: totalScore,
    grade: grade,
    diagnosis: diagnosis,
    recommendation: recommendation,
    strengths: strengths,
    improvements: improvements,
    mobile: mobile,
    pc: pc,
    likertRaw: likertRaw,
  };
}

function taskScore_(arr) {
  return TASKS.reduce(function (sum, _, i) {
    const v = arr[i];

    if (v === '완료') return sum + 1;
    if (v === '부분완료') return sum + 0.5;

    return sum;
  }, 0);
}

function parseLeadingNumber_(value) {
  if (value === null || value === undefined) return NaN;

  const m = String(value).match(/^\s*([1-5])/);
  return m ? Number(m[1]) : NaN;
}

// ======================================================
// 8. 개인별 빌드업 리포트 생성
// ======================================================

function createBuildUpReport_(answers) {
  const folder = ensureReportFolder_();
  const summary = analyzeAnswers_(answers);

  const job = text_(answers['담당 업무']) || '미기재';
  const timestamp = answers.__timestamp || new Date();

  const stamp = Utilities.formatDate(
    new Date(timestamp),
    Session.getScriptTimeZone(),
    'yyyyMMdd_HHmmss'
  );

  const baseName =
    '빌드업 리포트_' + sanitizeFileName_(job) + '_' + stamp;

  const doc = DocumentApp.create(baseName);
  const body = doc.getBody();

  // 제목
  body.appendParagraph('AI Smart Factory Agent Office')
    .setHeading(DocumentApp.ParagraphHeading.TITLE);

  body.appendParagraph('개인별 빌드업 리포트')
    .setHeading(DocumentApp.ParagraphHeading.HEADING1);

  body.appendParagraph(
    '생성일: ' +
    Utilities.formatDate(
      new Date(timestamp),
      Session.getScriptTimeZone(),
      'yyyy-MM-dd HH:mm:ss'
    )
  );

  body.appendHorizontalRule();

  // 1. 응답자 정보
  body.appendParagraph('1. 응답자 정보')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  appendKeyValueTable_(body, [
    ['담당 업무', job],
    ['경력', text_(answers['경력']) || '-'],
    ['스마트기기 사용', text_(answers['스마트기기 사용']) || '-'],
    ['다시 사용·추천 의향', text_(answers[REUSE_TITLE]) || '-'],
  ]);

  // 2. 종합 진단
  body.appendParagraph('2. 종합 진단')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  appendKeyValueTable_(body, [
    ['종합 점수', summary.totalScore.toFixed(1) + ' / 100'],
    ['빌드업 등급', summary.grade],
    ['진단', summary.diagnosis],
    ['항목별 평가 평균', summary.likertAverage.toFixed(2) + ' / 5'],
    ['테스트 과업 완료율', summary.taskCompletionRate.toFixed(1) + '%'],
    ['전체 만족도', summary.satisfaction + ' / 5'],
  ]);

  body.appendParagraph('추천 방향')
    .setHeading(DocumentApp.ParagraphHeading.HEADING3);

  body.appendParagraph(summary.recommendation);

  // 3. 강점
  body.appendParagraph('3. 강점')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  if (summary.strengths.length) {
    summary.strengths.forEach(function (item) {
      body.appendListItem(item);
    });
  } else {
    body.appendParagraph('현재 응답에서 뚜렷한 고득점 강점 항목은 확인되지 않았습니다.');
  }

  // 4. 개선 포인트
  body.appendParagraph('4. 우선 개선 포인트')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  if (summary.improvements.length) {
    summary.improvements.forEach(function (item) {
      body.appendListItem(item);
    });
  } else {
    body.appendParagraph('우선 보완이 필요한 저점 항목은 확인되지 않았습니다.');
  }

  // 5. 기기별 테스트
  body.appendParagraph('5. 기기별 테스트 결과')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  const taskRows = [['테스트 단계', '모바일', 'PC·노트북']];

  TASKS.forEach(function (task, i) {
    taskRows.push([
      task,
      summary.mobile[i] || '-',
      summary.pc[i] || '-',
    ]);
  });

  body.appendTable(taskRows);

  // 6. 항목별 평가
  body.appendParagraph('6. 항목별 평가')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  const likertRows = [['평가 항목', '점수']];

  LIKERT_ITEMS.forEach(function (item, i) {
    const score = parseLeadingNumber_(summary.likertRaw[i]);

    likertRows.push([
      item,
      isNaN(score) ? '-' : String(score) + ' / 5',
    ]);
  });

  body.appendTable(likertRows);

  // 7. 자유 의견
  body.appendParagraph('7. 자유 의견')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  OPEN_QUESTIONS.forEach(function (q) {
    body.appendParagraph(q)
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    body.appendParagraph(text_(answers[q]) || '(응답 없음)');
  });

  body.appendHorizontalRule();

  body.appendParagraph(
    '※ 본 리포트는 설문 응답을 기반으로 자동 생성된 참고용 리포트입니다.'
  );

  doc.saveAndClose();

  // Docs 파일을 리포트 폴더로 이동
  const docFile = DriveApp.getFileById(doc.getId());
  docFile.moveTo(folder);

  // PDF 생성
  const pdfBlob = docFile
    .getAs(MimeType.PDF)
    .setName(baseName + '.pdf');

  const pdfFile = folder.createFile(pdfBlob);

  Logger.log('빌드업 리포트 생성 완료: ' + doc.getUrl());
  Logger.log('PDF 생성 완료: ' + pdfFile.getUrl());

  return {
    docUrl: doc.getUrl(),
    pdfUrl: pdfFile.getUrl(),
    docId: doc.getId(),
    pdfId: pdfFile.getId(),
  };
}

function appendKeyValueTable_(body, rows) {
  const table = body.appendTable(rows);

  for (let r = 0; r < table.getNumRows(); r++) {
    const row = table.getRow(r);

    row.getCell(0).setBackgroundColor('#EEF3FF');
    row.getCell(0).editAsText().setBold(true);
  }
}

// ======================================================
// 9. 리포트 폴더
// ======================================================

function ensureReportFolder_() {
  const props = PropertiesService.getScriptProperties();
  const savedId = props.getProperty('REPORT_FOLDER_ID');

  if (savedId) {
    try {
      return DriveApp.getFolderById(savedId);
    } catch (err) {
      Logger.log('기존 리포트 폴더를 찾지 못해 다시 만듭니다.');
    }
  }

  const folders = DriveApp.getFoldersByName(REPORT_FOLDER_NAME);

  const folder = folders.hasNext()
    ? folders.next()
    : DriveApp.createFolder(REPORT_FOLDER_NAME);

  props.setProperty('REPORT_FOLDER_ID', folder.getId());

  return folder;
}

// ======================================================
// 10. 분석 대시보드
// ======================================================

function buildAnalysisDashboard() {
  const ss = getResponseSpreadsheet_();
  const respSheet = findResponseSheet_(ss);

  if (!respSheet) {
    throw new Error('Google Forms 응답 시트를 찾지 못했습니다.');
  }

  const values = respSheet.getDataRange().getDisplayValues();

  if (!values.length) {
    throw new Error('응답 시트가 비어 있습니다.');
  }

  const headers = values[0];

  const rows = values.slice(1).filter(function (r) {
    return r[0] !== '';
  });

  let sheet = ss.getSheetByName('분석');

  if (sheet) {
    ss.deleteSheet(sheet);
  }

  sheet = ss.insertSheet('분석', 0);

  sheet.setFrozenRows(2);
  sheet.setColumnWidth(1, 360);
  sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 120);

  sheet.getRange('A1:C1')
    .merge()
    .setValue('AI Smart Factory Agent Office — 설문 결과 분석')
    .setFontWeight('bold')
    .setFontSize(14)
    .setBackground('#14213D')
    .setFontColor('#FFFFFF');

  sheet.getRange('A2').setValue('총 응답 수');
  sheet.getRange('B2').setValue(rows.length);

  let row = 4;

  // 항목별 평균
  sheet.getRange(row, 1, 1, 3)
    .merge()
    .setValue('1. 항목별 평가 평균')
    .setFontWeight('bold')
    .setBackground('#EEF3FF');

  row++;

  sheet.getRange(row, 1, 1, 3)
    .setValues([['문항', '평균', '응답 수']])
    .setFontWeight('bold');

  row++;

  LIKERT_ITEMS.forEach(function (item) {
    const idx = findHeaderIndex_(headers, item);

    const scores = idx >= 0
      ? rows
          .map(function (r) {
            return parseLeadingNumber_(r[idx]);
          })
          .filter(function (v) {
            return !isNaN(v);
          })
      : [];

    const avg = scores.length
      ? scores.reduce(function (a, b) { return a + b; }, 0) / scores.length
      : '';

    sheet.getRange(row, 1).setValue(item);
    sheet.getRange(row, 2).setValue(
      avg === '' ? '' : Number(avg.toFixed(2))
    );
    sheet.getRange(row, 3).setValue(scores.length);

    row++;
  });

  row += 2;

  // 종합
  sheet.getRange(row, 1, 1, 3)
    .merge()
    .setValue('2. 종합')
    .setFontWeight('bold')
    .setBackground('#EEF3FF');

  row++;

  const satIdx = findHeaderIndex_(headers, SCALE_TITLE);

  const satScores = satIdx >= 0
    ? rows
        .map(function (r) {
          return Number(r[satIdx]);
        })
        .filter(function (v) {
          return !isNaN(v) && v > 0;
        })
    : [];

  const satAvg = satScores.length
    ? satScores.reduce(function (a, b) { return a + b; }, 0) / satScores.length
    : '';

  sheet.getRange(row, 1).setValue('전체 만족도 평균');
  sheet.getRange(row, 2).setValue(
    satAvg === '' ? '' : Number(satAvg.toFixed(2))
  );

  row += 2;

  const reuseIdx = findHeaderIndex_(headers, REUSE_TITLE);

  const reuseCounts = {
    '예': 0,
    '아니오': 0,
    '잘 모르겠음': 0,
  };

  if (reuseIdx >= 0) {
    rows.forEach(function (r) {
      const v = String(r[reuseIdx]).trim();

      if (Object.prototype.hasOwnProperty.call(reuseCounts, v)) {
        reuseCounts[v]++;
      }
    });
  }

  sheet.getRange(row, 1, 1, 2)
    .setValues([['재사용·추천 의향', '응답 수']])
    .setFontWeight('bold');

  row++;

  Object.keys(reuseCounts).forEach(function (k) {
    sheet.getRange(row, 1).setValue(k);
    sheet.getRange(row, 2).setValue(reuseCounts[k]);
    row++;
  });

  // 간단한 차트
  try {
    const chart = sheet.newChart()
      .setChartType(Charts.ChartType.BAR)
      .addRange(sheet.getRange(6, 1, LIKERT_ITEMS.length, 2))
      .setPosition(4, 5, 0, 0)
      .setOption('title', '항목별 평가 평균')
      .setOption('legend', { position: 'none' })
      .build();

    sheet.insertChart(chart);
  } catch (err) {
    Logger.log('차트 생성 실패: ' + err.message);
  }

  Logger.log('분석 탭 갱신 완료: ' + ss.getUrl());
}

// ======================================================
// 11. 응답 시트 찾기
// ======================================================

function getResponseSpreadsheet_() {
  const id =
    PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');

  if (!id) {
    throw new Error(
      'SPREADSHEET_ID가 없습니다. setupSurveySystem()을 먼저 실행하세요.'
    );
  }

  return SpreadsheetApp.openById(id);
}

function findResponseSheet_(ss) {
  const known = ['Form Responses 1', 'Form Responses 2'];

  for (let i = 0; i < known.length; i++) {
    const s = ss.getSheetByName(known[i]);

    if (s && s.getLastColumn() > 0) {
      return s;
    }
  }

  const sheets = ss.getSheets();

  for (let i = 0; i < sheets.length; i++) {
    const s = sheets[i];

    if (s.getName() === '분석') continue;
    if (s.getLastColumn() < 1) continue;

    const first =
      String(s.getRange(1, 1).getDisplayValue()).toLowerCase();

    if (
      first.indexOf('timestamp') !== -1 ||
      first.indexOf('타임스탬프') !== -1
    ) {
      return s;
    }
  }

  return null;
}

function findHeaderIndex_(headers, text) {
  for (let i = 0; i < headers.length; i++) {
    if (String(headers[i]).indexOf(text) !== -1) {
      return i;
    }
  }

  return -1;
}

// ======================================================
// 12. 공통 유틸
// ======================================================

function toArray_(value) {
  if (Array.isArray(value)) return value;
  if (value === null || value === undefined || value === '') return [];

  return [value];
}

function text_(value) {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.join(', ');

  return String(value);
}

function sanitizeFileName_(name) {
  return String(name || '응답자')
    .replace(/[\\/:*?"<>|#%]/g, '_')
    .substring(0, 50);
}

// ======================================================
// 13. 리포트 수동 테스트
// ======================================================

function testBuildUpReport() {
  const sample = {};

  sample['담당 업무'] = '설비 운영·정비';
  sample['경력'] = '3~10년';
  sample['스마트기기 사용'] = '보통';

  sample[GRID_TITLE_MOBILE] = [
    '완료',
    '완료',
    '완료',
    '부분완료',
    '완료',
    '부분완료',
    '완료',
  ];

  sample[GRID_TITLE_PC] = [
    '완료',
    '완료',
    '완료',
    '완료',
    '완료',
    '완료',
    '완료',
  ];

  sample[GRID_TITLE_LIKERT] = [
    '4 (그렇다)',
    '4 (그렇다)',
    '3 (보통이다)',
    '5 (매우 그렇다)',
    '4 (그렇다)',
    '5 (매우 그렇다)',
  ];

  sample['가장 도움이 되었던 점은 무엇인가요?'] =
    '판정 근거와 최종 보고서가 한 화면에서 연결되는 점이 좋았습니다.';

  sample['가장 불편했거나 개선이 필요한 점은 무엇인가요?'] =
    '모바일 화면에서 일부 정보가 조금 작게 보였습니다.';

  sample['기타 의견이나 제안이 있다면 자유롭게 적어 주세요.'] =
    '설비별 비교 기능이 추가되면 좋겠습니다.';

  sample[SCALE_TITLE] = '4';
  sample[REUSE_TITLE] = '예';
  sample.__timestamp = new Date();

  const report = createBuildUpReport_(sample);

  Logger.log('테스트 리포트 생성 완료');
  Logger.log(report.docUrl);
  Logger.log(report.pdfUrl);
}


// ======================================================
// 14. 6명 통합 빌드업 리포트
// ======================================================

/**
 * 현재 응답 스프레드시트에서 최대 6명의 응답을 읽어
 * 하나의 Google Docs + PDF 통합 리포트를 만듭니다.
 *
 * 실행 방법:
 * Apps Script 상단 함수 선택 → buildSixPersonCombinedReport → 실행
 */
function buildSixPersonCombinedReport() {
  // setupSurveySystem()에서 Script Properties에 저장한 실제 응답 스프레드시트를 사용
  const ss = getResponseSpreadsheet_();
  const respSheet = findResponseSheet_(ss);

  if (!respSheet) {
    throw new Error('응답 시트를 찾지 못했습니다.');
  }

  const data = respSheet.getDataRange().getDisplayValues();

  if (data.length < 2) {
    throw new Error('아직 설문 응답이 없습니다.');
  }

  const headers = data[0];
  const rawRows = data.slice(1).filter(function(row) {
    return row.some(function(v) { return String(v).trim() !== ''; });
  });

  if (!rawRows.length) {
    throw new Error('분석할 응답이 없습니다.');
  }

  // 현재 응답 중 앞에서 최대 6명
  const rows = rawRows.slice(0, COMBINED_REPORT_MAX_PEOPLE);

  const participants = rows.map(function(row, index) {
    const answers = sheetRowToAnswers_(headers, row);
    return {
      no: index + 1,
      answers: answers,
      summary: analyzeAnswers_(answers)
    };
  });

  const group = summarizeParticipants_(participants);
  const report = createCombinedReportDocument_(participants, group, ss);

  Logger.log('====================================================');
  Logger.log('6명 통합 리포트 생성 완료');
  Logger.log('대상 응답 수: ' + participants.length);
  Logger.log('Google Docs: ' + report.docUrl);
  Logger.log('PDF: ' + report.pdfUrl);
  Logger.log('====================================================');

  return report;
}


/**
 * 응답 시트의 한 행을 기존 analyzeAnswers_()가 읽을 수 있는 형태로 변환합니다.
 */
function sheetRowToAnswers_(headers, row) {
  const out = {};

  function exactValue(title) {
    const idx = headers.findIndex(function(h) {
      return String(h).trim() === title;
    });
    return idx >= 0 ? row[idx] : '';
  }

  function containsValue(text) {
    const idx = headers.findIndex(function(h) {
      return String(h).indexOf(text) !== -1;
    });
    return idx >= 0 ? row[idx] : '';
  }

  out['담당 업무'] = exactValue('담당 업무') || containsValue('담당 업무');
  out['경력'] = exactValue('경력') || containsValue('경력');
  out['스마트기기 사용'] = exactValue('스마트기기 사용') || containsValue('스마트기기 사용');
  out[SCALE_TITLE] = exactValue(SCALE_TITLE) || containsValue(SCALE_TITLE);
  out[REUSE_TITLE] = exactValue(REUSE_TITLE) || containsValue(REUSE_TITLE);

  OPEN_QUESTIONS.forEach(function(q) {
    out[q] = exactValue(q) || containsValue(q);
  });

  // 항목별 평가 그리드
  out[GRID_TITLE_LIKERT] = LIKERT_ITEMS.map(function(item) {
    const idx = headers.findIndex(function(h) {
      return String(h).indexOf(item) !== -1;
    });
    return idx >= 0 ? row[idx] : '';
  });

  // 모바일/PC 과업 그리드
  // 같은 과업명이 두 번 등장하므로 첫 번째는 모바일, 두 번째는 PC로 읽습니다.
  const mobile = [];
  const pc = [];

  TASKS.forEach(function(task) {
    const matches = [];

    headers.forEach(function(h, idx) {
      if (String(h).indexOf(task) !== -1) {
        matches.push(idx);
      }
    });

    mobile.push(matches.length >= 1 ? row[matches[0]] : '');
    pc.push(matches.length >= 2 ? row[matches[1]] : '');
  });

  out[GRID_TITLE_MOBILE] = mobile;
  out[GRID_TITLE_PC] = pc;

  // A열은 보통 타임스탬프
  out.__timestamp = row[0] || new Date();

  return out;
}


/**
 * 여러 사람의 결과를 전체 평균/공통 강점/공통 개선점으로 요약합니다.
 */
function summarizeParticipants_(participants) {
  const count = participants.length;

  const avg = function(values) {
    if (!values.length) return 0;
    return values.reduce(function(a, b) { return a + b; }, 0) / values.length;
  };

  const gradeCounts = {};
  const reuseCounts = {
    '예': 0,
    '아니오': 0,
    '잘 모르겠음': 0
  };

  const strengthCounts = {};
  const improvementCounts = {};

  participants.forEach(function(p) {
    const s = p.summary;

    gradeCounts[s.grade] = (gradeCounts[s.grade] || 0) + 1;

    const reuse = text_(p.answers[REUSE_TITLE]).trim();
    if (Object.prototype.hasOwnProperty.call(reuseCounts, reuse)) {
      reuseCounts[reuse]++;
    }

    s.strengths.forEach(function(item) {
      strengthCounts[item] = (strengthCounts[item] || 0) + 1;
    });

    s.improvements.forEach(function(item) {
      improvementCounts[item] = (improvementCounts[item] || 0) + 1;
    });
  });

  function topItems(obj, limit) {
    return Object.keys(obj)
      .map(function(key) {
        return { item: key, count: obj[key] };
      })
      .sort(function(a, b) {
        if (b.count !== a.count) return b.count - a.count;
        return a.item.localeCompare(b.item, 'ko');
      })
      .slice(0, limit);
  }

  return {
    count: count,
    avgTotalScore: avg(participants.map(function(p) {
      return p.summary.totalScore;
    })),
    avgLikert: avg(participants.map(function(p) {
      return p.summary.likertAverage;
    })),
    avgTaskCompletion: avg(participants.map(function(p) {
      return p.summary.taskCompletionRate;
    })),
    avgSatisfaction: avg(participants.map(function(p) {
      return p.summary.satisfaction;
    })),
    gradeCounts: gradeCounts,
    reuseCounts: reuseCounts,
    topStrengths: topItems(strengthCounts, 5),
    topImprovements: topItems(improvementCounts, 5)
  };
}


/**
 * 하나의 Google Docs 안에
 *  - 6명 전체 요약
 *  - 6명 비교표
 *  - 공통 강점/개선점
 *  - 응답자 1~6 상세 결과
 * 를 모두 넣고 PDF도 생성합니다.
 */
function createCombinedReportDocument_(participants, group, ss) {
  const folder = ensureReportFolder_();

  const stamp = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    'yyyyMMdd_HHmmss'
  );

  const baseName = '6명_통합_빌드업_리포트_' + stamp;

  const doc = DocumentApp.create(baseName);
  const body = doc.getBody();

  body.appendParagraph('AI Smart Factory Agent Office')
    .setHeading(DocumentApp.ParagraphHeading.TITLE);

  body.appendParagraph('사용자 6명 통합 빌드업 리포트')
    .setHeading(DocumentApp.ParagraphHeading.HEADING1);

  body.appendParagraph(
    '분석 대상: ' + group.count + '명\n' +
    '생성일: ' +
    Utilities.formatDate(
      new Date(),
      Session.getScriptTimeZone(),
      'yyyy-MM-dd HH:mm:ss'
    )
  );

  body.appendHorizontalRule();

  // --------------------------------------------------
  // 1. 전체 요약
  // --------------------------------------------------
  body.appendParagraph('1. 전체 요약')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  appendKeyValueTable_(body, [
    ['응답 인원', group.count + '명'],
    ['평균 종합 점수', group.avgTotalScore.toFixed(1) + ' / 100'],
    ['평균 항목별 평가', group.avgLikert.toFixed(2) + ' / 5'],
    ['평균 과업 완료율', group.avgTaskCompletion.toFixed(1) + '%'],
    ['평균 전체 만족도', group.avgSatisfaction.toFixed(2) + ' / 5'],
    [
      '재사용·추천 의향',
      '예 ' + group.reuseCounts['예'] + '명 / ' +
      '아니오 ' + group.reuseCounts['아니오'] + '명 / ' +
      '잘 모르겠음 ' + group.reuseCounts['잘 모르겠음'] + '명'
    ]
  ]);

  // 등급 분포
  body.appendParagraph('등급 분포')
    .setHeading(DocumentApp.ParagraphHeading.HEADING3);

  const gradeOrder = ['A+', 'A', 'B', 'C', 'D'];
  const gradeRows = [['등급', '인원']];

  gradeOrder.forEach(function(grade) {
    gradeRows.push([
      grade,
      String(group.gradeCounts[grade] || 0)
    ]);
  });

  body.appendTable(gradeRows);

  // --------------------------------------------------
  // 2. 6명 비교표
  // --------------------------------------------------
  body.appendParagraph('2. 응답자별 비교')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  const compareRows = [[
    '응답자',
    '담당 업무',
    '경력',
    '종합점수',
    '등급',
    '평가평균',
    '완료율',
    '만족도',
    '재사용'
  ]];

  participants.forEach(function(p) {
    compareRows.push([
      '응답자 ' + p.no,
      text_(p.answers['담당 업무']) || '-',
      text_(p.answers['경력']) || '-',
      p.summary.totalScore.toFixed(1),
      p.summary.grade,
      p.summary.likertAverage.toFixed(2),
      p.summary.taskCompletionRate.toFixed(1) + '%',
      String(p.summary.satisfaction),
      text_(p.answers[REUSE_TITLE]) || '-'
    ]);
  });

  body.appendTable(compareRows);

  // --------------------------------------------------
  // 3. 공통 강점
  // --------------------------------------------------
  body.appendParagraph('3. 공통 강점')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  if (group.topStrengths.length) {
    group.topStrengths.forEach(function(x) {
      body.appendListItem(
        x.item + ' — ' + x.count + '명에서 강점으로 확인'
      );
    });
  } else {
    body.appendParagraph('공통 강점으로 분류된 항목이 없습니다.');
  }

  // --------------------------------------------------
  // 4. 공통 개선 포인트
  // --------------------------------------------------
  body.appendParagraph('4. 공통 개선 포인트')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  if (group.topImprovements.length) {
    group.topImprovements.forEach(function(x) {
      body.appendListItem(
        x.item + ' — ' + x.count + '명에서 개선 필요'
      );
    });
  } else {
    body.appendParagraph('공통 개선 필요 항목이 없습니다.');
  }

  // --------------------------------------------------
  // 5. 자유 의견 전체 모음
  // --------------------------------------------------
  body.appendParagraph('5. 사용자 의견 모음')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);

  OPEN_QUESTIONS.forEach(function(q) {
    body.appendParagraph(q)
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    participants.forEach(function(p) {
      const answer = text_(p.answers[q]).trim();

      if (answer) {
        body.appendListItem(
          '응답자 ' + p.no + ': ' + answer
        );
      }
    });
  });

  // --------------------------------------------------
  // 6. 개인별 상세
  // --------------------------------------------------
  body.appendPageBreak();

  body.appendParagraph('6. 응답자별 상세 분석')
    .setHeading(DocumentApp.ParagraphHeading.HEADING1);

  participants.forEach(function(p, index) {
    const s = p.summary;
    const a = p.answers;

    if (index > 0) {
      body.appendPageBreak();
    }

    body.appendParagraph('응답자 ' + p.no)
      .setHeading(DocumentApp.ParagraphHeading.HEADING2);

    appendKeyValueTable_(body, [
      ['담당 업무', text_(a['담당 업무']) || '-'],
      ['경력', text_(a['경력']) || '-'],
      ['스마트기기 사용', text_(a['스마트기기 사용']) || '-'],
      ['종합 점수', s.totalScore.toFixed(1) + ' / 100'],
      ['등급', s.grade],
      ['진단', s.diagnosis],
      ['항목별 평가 평균', s.likertAverage.toFixed(2) + ' / 5'],
      ['과업 완료율', s.taskCompletionRate.toFixed(1) + '%'],
      ['전체 만족도', s.satisfaction + ' / 5'],
      ['재사용·추천 의향', text_(a[REUSE_TITLE]) || '-']
    ]);

    body.appendParagraph('강점')
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    if (s.strengths.length) {
      s.strengths.forEach(function(item) {
        body.appendListItem(item);
      });
    } else {
      body.appendParagraph('고득점 강점 항목 없음');
    }

    body.appendParagraph('개선 포인트')
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    if (s.improvements.length) {
      s.improvements.forEach(function(item) {
        body.appendListItem(item);
      });
    } else {
      body.appendParagraph('우선 개선 항목 없음');
    }

    body.appendParagraph('추천 방향')
      .setHeading(DocumentApp.ParagraphHeading.HEADING3);

    body.appendParagraph(s.recommendation);
  });

  body.appendHorizontalRule();

  body.appendParagraph(
    '원본 응답 스프레드시트: ' + ss.getName() + '\n' +
    '※ 본 문서는 설문 응답을 기반으로 자동 생성된 통합 분석 리포트입니다.'
  );

  doc.saveAndClose();

  const docFile = DriveApp.getFileById(doc.getId());
  docFile.moveTo(folder);

  const pdfBlob = docFile
    .getAs(MimeType.PDF)
    .setName(baseName + '.pdf');

  const pdfFile = folder.createFile(pdfBlob);

  return {
    docUrl: doc.getUrl(),
    pdfUrl: pdfFile.getUrl(),
    docId: doc.getId(),
    pdfId: pdfFile.getId()
  };
}


// ======================================================
// 15. 현재 연결 상태 확인
// ======================================================

function showCurrentSurveySystemLinks() {
  const props = PropertiesService.getScriptProperties();
  const formId = props.getProperty('FORM_ID');
  const ssId = props.getProperty('SPREADSHEET_ID');
  const folderId = props.getProperty('REPORT_FOLDER_ID');

  Logger.log('================ 현재 연결 정보 ================');

  if (formId) {
    try {
      const form = FormApp.openById(formId);
      Logger.log('설문 응답 링크: ' + form.getPublishedUrl());
      Logger.log('설문 편집 링크: ' + form.getEditUrl());
    } catch (e) {
      Logger.log('설문지 열기 실패: ' + e.message);
    }
  } else {
    Logger.log('FORM_ID 없음');
  }

  if (ssId) {
    try {
      const ss = SpreadsheetApp.openById(ssId);
      Logger.log('응답 스프레드시트: ' + ss.getUrl());
    } catch (e) {
      Logger.log('응답 스프레드시트 열기 실패: ' + e.message);
    }
  } else {
    Logger.log('SPREADSHEET_ID 없음');
  }

  if (folderId) {
    try {
      const folder = DriveApp.getFolderById(folderId);
      Logger.log('리포트 폴더: ' + folder.getUrl());
    } catch (e) {
      Logger.log('리포트 폴더 열기 실패: ' + e.message);
    }
  }

  Logger.log('================================================');
}
