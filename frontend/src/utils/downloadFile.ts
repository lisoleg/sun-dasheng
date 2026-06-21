/**
 * 浏览器下载工具
 * 支持 CSV、JSON、PDF 等格式下载
 */

/**
 * 下载 CSV 文件
 */
export function downloadCSV(data: unknown[], filename: string): void {
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map((row) =>
      headers
        .map((header) => {
          const val = (row as Record<string, unknown>)[header];
          // 处理包含逗号或引号的值
          if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
            return `"${val.replace(/"/g, '""')}"`;
          }
          return String(val);
        })
        .join(',')
    ),
  ];

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, `${filename}.csv`);
}

/**
 * 下载 JSON 文件
 */
export function downloadJSON(data: unknown, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
  downloadBlob(blob, `${filename}.json`);
}

/**
 * 下载 PDF 文件（从 blob）
 */
export function downloadPDF(blob: Blob, filename: string): void {
  downloadBlob(blob, `${filename}.pdf`);
}

/**
 * 下载文本文件
 */
export function downloadText(text: string, filename: string, mimeType = 'text/plain'): void {
  const blob = new Blob([text], { type: `${mimeType};charset=utf-8;` });
  downloadBlob(blob, filename);
}

/**
 * 通用 blob 下载
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 从 URL 下载文件（用于后端生成的文件）
 */
export async function downloadFromUrl(url: string, filename?: string): Promise<void> {
  const response = await fetch(url);
  const blob = await response.blob();
  const finalFilename = filename || response.headers.get('Content-Disposition')?.split('filename=')[1] || 'download';
  downloadBlob(blob, finalFilename);
}
