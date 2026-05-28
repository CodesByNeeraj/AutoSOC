import { jsPDF } from 'jspdf'

const COLORS = {
  black:      [10,  12,  15],
  darkGray:   [30,  34,  40],
  midGray:    [60,  70,  85],
  lightGray:  [120, 135, 150],
  white:      [255, 255, 255],
  blue:       [59,  130, 246],
  red:        [239, 68,  68],
  amber:      [245, 158, 11],
  green:      [34,  197, 94],
  purple:     [168, 85,  247],
  p0:         [239, 68,  68],
  p1:         [249, 115, 22],
  p2:         [234, 179, 8],
  p3:         [59,  130, 246],
  p4:         [107, 114, 128],
}

const PRIORITY_COLOR = { p0: COLORS.p0, p1: COLORS.p1, p2: COLORS.p2, p3: COLORS.p3, p4: COLORS.p4 }
const PAGE_W = 210
const PAGE_H = 297
const MARGIN = 18
const CONTENT_W = PAGE_W - MARGIN * 2

export function exportIncidentPDF({ incidentId, triage, investigation, response, report }) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  let y = 0

  // ── helpers ────────────────────────────────────────────────────────────────

  function rgb(arr) { return { r: arr[0], g: arr[1], b: arr[2] } }

  function checkPage(needed = 10) {
    if (y + needed > PAGE_H - 16) {
      doc.addPage()
      y = MARGIN
    }
  }

  function text(str, x, size = 10, color = COLORS.black, style = 'normal') {
    doc.setFontSize(size)
    doc.setFont('helvetica', style)
    doc.setTextColor(...color)
    doc.text(str, x, y)
  }

  function wrappedText(str, size = 10, color = COLORS.midGray, indent = 0) {
    if (!str) return
    doc.setFontSize(size)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...color)
    const lines = doc.splitTextToSize(str, CONTENT_W - indent)
    lines.forEach(line => {
      checkPage(6)
      doc.text(line, MARGIN + indent, y)
      y += 5.5
    })
  }

  function sectionHeader(title) {
    checkPage(14)
    y += 6
    doc.setFillColor(...COLORS.darkGray)
    doc.rect(MARGIN, y - 5, CONTENT_W, 9, 'F')
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...COLORS.white)
    doc.text(title.toUpperCase(), MARGIN + 4, y)
    y += 7
  }

  function fieldLabel(label) {
    checkPage(8)
    y += 3
    doc.setFontSize(8)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...COLORS.lightGray)
    doc.text(label.toUpperCase(), MARGIN, y)
    y += 4.5
  }

  function bulletList(items, color = COLORS.midGray) {
    if (!items?.length) return
    items.forEach(item => {
      checkPage(7)
      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(...color)
      doc.text('•', MARGIN + 2, y)
      const lines = doc.splitTextToSize(item, CONTENT_W - 10)
      lines.forEach((line, i) => {
        if (i > 0) { checkPage(5); y += 4.5 }
        doc.text(line, MARGIN + 7, y)
      })
      y += 5.5
    })
  }

  function tagRow(items, color = COLORS.blue) {
    if (!items?.length) return
    let x = MARGIN
    const tagH = 5.5
    const padX = 3
    items.forEach(item => {
      doc.setFontSize(8)
      const w = doc.getTextWidth(item) + padX * 2
      if (x + w > PAGE_W - MARGIN) { y += tagH + 2; x = MARGIN }
      checkPage(tagH + 2)
      doc.setDrawColor(...color)
      doc.setFillColor(color[0], color[1], color[2], 0.08)
      doc.roundedRect(x, y - 4, w, tagH, 1, 1, 'FD')
      doc.setTextColor(...color)
      doc.text(item, x + padX, y)
      x += w + 3
    })
    y += tagH + 2
  }

  function divider() {
    checkPage(6)
    y += 4
    doc.setDrawColor(...COLORS.lightGray)
    doc.setLineWidth(0.2)
    doc.line(MARGIN, y, PAGE_W - MARGIN, y)
    y += 4
  }

  function priorityBadge(priority) {
    const p = priority?.toLowerCase() ?? 'p4'
    const color = PRIORITY_COLOR[p] ?? COLORS.p4
    const label = p.toUpperCase()
    doc.setFontSize(8)
    const w = doc.getTextWidth(label) + 6
    doc.setFillColor(...color)
    doc.roundedRect(PAGE_W - MARGIN - w, y - 14, w, 6, 1, 1, 'F')
    doc.setTextColor(...COLORS.white)
    doc.setFont('helvetica', 'bold')
    doc.text(label, PAGE_W - MARGIN - w + 3, y - 10)
  }

  // ── cover page ─────────────────────────────────────────────────────────────

  doc.setFillColor(...COLORS.black)
  doc.rect(0, 0, PAGE_W, PAGE_H, 'F')

  // accent bar
  doc.setFillColor(...COLORS.blue)
  doc.rect(0, 0, 4, PAGE_H, 'F')

  doc.setFontSize(28)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...COLORS.white)
  doc.text('AUTOSOC', MARGIN, 60)

  doc.setFontSize(14)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...COLORS.lightGray)
  doc.text('Incident Report', MARGIN, 70)

  doc.setDrawColor(...COLORS.midGray)
  doc.setLineWidth(0.3)
  doc.line(MARGIN, 78, PAGE_W - MARGIN, 78)

  const title = triage?.title ?? 'Security Incident'
  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...COLORS.white)
  const titleLines = doc.splitTextToSize(title, CONTENT_W)
  let titleY = 92
  titleLines.forEach(l => { doc.text(l, MARGIN, titleY); titleY += 9 })

  const meta = [
    ['Incident ID', incidentId ?? '—'],
    ['Priority',    triage?.priority?.toUpperCase() ?? '—'],
    ['Category',    triage?.category ?? '—'],
    ['Generated',   new Date().toUTCString()],
  ]
  let metaY = titleY + 12
  meta.forEach(([label, val]) => {
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...COLORS.lightGray)
    doc.text(label, MARGIN, metaY)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...COLORS.white)
    doc.text(val, MARGIN + 36, metaY)
    metaY += 8
  })

  // priority chip on cover
  if (triage?.priority) {
    const p = triage.priority.toLowerCase()
    const color = PRIORITY_COLOR[p] ?? COLORS.p4
    doc.setFillColor(...color)
    doc.roundedRect(MARGIN, PAGE_H - 40, 20, 10, 2, 2, 'F')
    doc.setFontSize(11)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...COLORS.white)
    doc.text(p.toUpperCase(), MARGIN + 4, PAGE_H - 33)
  }

  doc.setFontSize(8)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...COLORS.midGray)
  doc.text('Generated by AutoSOC · Powered by Claude', MARGIN, PAGE_H - 14)

  // ── page 2+ content ────────────────────────────────────────────────────────

  doc.addPage()
  y = MARGIN

  // ── triage ────────────────────────────────────────────────────────────────

  if (triage) {
    sectionHeader('Triage')

    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...COLORS.black)
    doc.text(triage.title ?? '', MARGIN, y)
    priorityBadge(triage.priority)
    y += 7

    // key fields row
    const fields = [
      ['Category',    triage.category ?? '—'],
      ['Confidence',  `${triage.confidence ?? 0}%`],
      ['Human Review', triage.human_review ? 'Required' : 'Not required'],
    ]
    const colW = CONTENT_W / fields.length
    fields.forEach(([label, val], i) => {
      const x = MARGIN + i * colW
      doc.setFontSize(7.5)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(...COLORS.lightGray)
      doc.text(label.toUpperCase(), x, y)
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      const valColor = label === 'Human Review' && triage.human_review ? COLORS.amber : COLORS.black
      doc.setTextColor(...valColor)
      doc.text(val, x, y + 5)
    })
    y += 14

    fieldLabel('Summary')
    wrappedText(triage.summary, 9.5, COLORS.midGray)

    fieldLabel('Justification')
    wrappedText(triage.justification, 9.5, COLORS.midGray)

    fieldLabel('Indicators')
    tagRow(triage.indicators ?? [])

    divider()
  }

  // ── investigation ─────────────────────────────────────────────────────────

  if (investigation) {
    sectionHeader('Investigation')

    const blastColor = investigation.blast_radius === 'critical' ? COLORS.red
      : investigation.blast_radius === 'spreading' ? COLORS.amber
      : COLORS.green

    const iFields = [
      ['Attack Pattern',  investigation.attack_pattern ?? '—'],
      ['Blast Radius',    investigation.blast_radius ?? '—'],
      ['Confidence',      `${investigation.confidence ?? 0}%`],
    ]
    const iColW = CONTENT_W / iFields.length
    iFields.forEach(([label, val], i) => {
      const x = MARGIN + i * iColW
      doc.setFontSize(7.5)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(...COLORS.lightGray)
      doc.text(label.toUpperCase(), x, y)
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      const valColor = label === 'Blast Radius' ? blastColor : COLORS.black
      doc.setTextColor(...valColor)
      doc.text(val, x, y + 5)
    })
    y += 14

    fieldLabel('Root Cause')
    wrappedText(investigation.root_cause, 9.5, COLORS.midGray)

    fieldLabel('Summary')
    wrappedText(investigation.summary, 9.5, COLORS.midGray)

    fieldLabel('MITRE ATT&CK Tactics')
    tagRow(investigation.mitre_tactics ?? [], COLORS.purple)

    fieldLabel('Affected Assets')
    tagRow(investigation.affected_assets ?? [])

    fieldLabel('Timeline')
    bulletList(investigation.timeline ?? [])

    fieldLabel('Evidence Gaps')
    bulletList(investigation.evidence_gaps ?? [], COLORS.amber)

    divider()
  }

  // ── response ───────────────────────────────────────────────────────────────

  if (response) {
    sectionHeader('Response Plan')

    const rFields = [
      ['Est. Resolution',   response.estimated_resolution_time ?? '—'],
      ['Confidence',        `${response.confidence ?? 0}%`],
      ['Escalate to Human', response.escalate_to_human ? 'Yes' : 'No'],
    ]
    const rColW = CONTENT_W / rFields.length
    rFields.forEach(([label, val], i) => {
      const x = MARGIN + i * rColW
      doc.setFontSize(7.5)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(...COLORS.lightGray)
      doc.text(label.toUpperCase(), x, y)
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      const valColor = label === 'Escalate to Human' && response.escalate_to_human ? COLORS.red : COLORS.black
      doc.setTextColor(...valColor)
      doc.text(val, x, y + 5)
    })
    y += 14

    fieldLabel('Immediate Actions  (within 15 minutes)')
    bulletList(response.immediate_actions ?? [], COLORS.red)

    fieldLabel('Short-term Actions  (within 2 hours)')
    bulletList(response.short_term_actions ?? [], COLORS.amber)

    fieldLabel('Long-term Actions  (within 24–72 hours)')
    bulletList(response.long_term_actions ?? [], COLORS.blue)

    fieldLabel('Containment Strategy')
    wrappedText(response.containment_strategy, 9.5, COLORS.midGray)

    fieldLabel('Eradication Steps')
    bulletList(response.eradication_steps ?? [])

    fieldLabel('Recovery Steps')
    bulletList(response.recovery_steps ?? [])

    fieldLabel('Notify Teams')
    tagRow(response.notify_teams ?? [])

    divider()
  }

  // ── report ─────────────────────────────────────────────────────────────────

  if (report) {
    sectionHeader('Incident Report')

    fieldLabel('Executive Summary')
    // highlighted box
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    const execLines = doc.splitTextToSize(report.executive_summary ?? '', CONTENT_W - 8)
    const boxH = execLines.length * 5.5 + 8
    checkPage(boxH + 4)
    doc.setFillColor(240, 245, 255)
    doc.setDrawColor(...COLORS.blue)
    doc.setLineWidth(0.3)
    doc.rect(MARGIN, y, CONTENT_W, boxH, 'FD')
    doc.setTextColor(...COLORS.black)
    execLines.forEach((line, i) => {
      doc.text(line, MARGIN + 4, y + 6 + i * 5.5)
    })
    y += boxH + 5

    fieldLabel('Technical Summary')
    wrappedText(report.technical_summary, 9.5, COLORS.midGray)

    fieldLabel('Attack Narrative')
    wrappedText(report.attack_narrative, 9.5, COLORS.midGray)

    fieldLabel('Timeline')
    bulletList(report.timeline ?? [])

    fieldLabel('Affected Assets')
    tagRow(report.affected_assets ?? [])

    fieldLabel('Response Actions Taken')
    bulletList(report.response_actions_taken ?? [])

    fieldLabel('Lessons Learned')
    bulletList(report.lessons_learned ?? [])

    fieldLabel('Recommendations')
    bulletList(report.recommendations ?? [], COLORS.blue)

    if (report.open_items?.length) {
      fieldLabel('Open Items')
      bulletList(report.open_items, COLORS.amber)
    }

    fieldLabel('Severity Justification')
    wrappedText(report.severity_justification, 9.5, COLORS.midGray)

    divider()

    // footer meta
    checkPage(16)
    doc.setFontSize(8)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...COLORS.lightGray)
    doc.text(`Authored by: ${report.authored_by ?? 'autosoc report agent'}`, MARGIN, y)
    y += 5
    doc.text(`Report confidence: ${report.report_confidence ?? 0}%`, MARGIN, y)
  }

  // ── page numbers ───────────────────────────────────────────────────────────

  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    if (i === 1) continue  // cover has no page number
    doc.setFontSize(8)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...COLORS.lightGray)
    doc.text(`${i} / ${totalPages}`, PAGE_W - MARGIN, PAGE_H - 8, { align: 'right' })
    doc.text('AutoSOC · Incident Report', MARGIN, PAGE_H - 8)
  }

  // ── save ───────────────────────────────────────────────────────────────────

  const slug = (triage?.title ?? 'incident').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40)
  doc.save(`autosoc-${slug}.pdf`)
}
