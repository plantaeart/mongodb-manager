/**
 * downloadFile — trigger a browser file download from a Blob.
 *
 * Creates a temporary object URL, clicks a hidden anchor element, then
 * immediately revokes the URL to free memory.
 *
 * @param blob     - The file content as a Blob
 * @param filename - The suggested filename for the download dialog
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
