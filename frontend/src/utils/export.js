/** Escape sesuai RFC 4180: bungkus dengan tanda kutip, gandakan kutip di dalam. */
function escapeCell(value) {
  if (value === null || value === undefined) return ''
  const text = String(value)
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

/**
 * Unduh array of object sebagai file .csv.
 * Kolom diambil dari key baris pertama.
 */
export function exportToCsv(data, filename = 'export.csv') {
  if (!data?.length) return

  const headers = Object.keys(data[0])
  const rows = data.map((row) => headers.map((h) => escapeCell(row[h])).join(','))
  const csv = [headers.join(','), ...rows].join('\n')

  // BOM agar Excel membaca UTF-8 dengan benar.
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
