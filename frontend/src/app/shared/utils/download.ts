/** Saves a Blob or a CSV string as a file in the browser. */
export function saveFile(content: Blob | string, filename: string, type = 'text/csv;charset=utf-8'): void {
  const blob = typeof content === 'string' ? new Blob(['\ufeff' + content], { type }) : content;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Rows -> CSV (comma separated, quoted when needed). */
export function toCsv(rows: Record<string, unknown>[], columns: { key: string; label: string }[]): string {
  const cell = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = columns.map(c => cell(c.label)).join(',');
  const body = rows.map(r => columns.map(c => cell(r[c.key])).join(',')).join('\n');
  return header + '\n' + body;
}
