/**
 * Backup helper utilities
 *
 * Provides display-layer helpers for backup folder paths.
 * The backend appends `_mongodb_manager` to every backup folder name for
 * namespacing purposes. These helpers strip that suffix so users see clean
 * folder names in the UI without the internal implementation detail.
 */

const BACKUP_FOLDER_SUFFIX = '_mongodb_manager'

/**
 * Strip the internal `_mongodb_manager` suffix from a backup folder path.
 *
 * Only the **last path segment** is cleaned — the rest of the path is kept
 * intact so the full value can still be sent back to the backend as-is.
 *
 * @example
 * stripBackupSuffix('/backups/test1_mongodb_manager') // → '/backups/test1'
 * stripBackupSuffix('test1_mongodb_manager')          // → 'test1'
 * stripBackupSuffix('/backups/test1')                 // → '/backups/test1' (no-op)
 */
export const stripBackupSuffix = (path: string): string => {
  if (!path) return path
  const lastSlash = path.lastIndexOf('/')
  const segment = lastSlash >= 0 ? path.slice(lastSlash + 1) : path
  const prefix = lastSlash >= 0 ? path.slice(0, lastSlash + 1) : ''

  const cleanSegment = segment.endsWith(BACKUP_FOLDER_SUFFIX)
    ? segment.slice(0, -BACKUP_FOLDER_SUFFIX.length)
    : segment

  return prefix + cleanSegment
}

/**
 * Strip the internal `_mongodb_manager` suffix from the **last path segment**
 * of every path found in a free-text line (e.g. terminal output like
 * "Location: /backups_mongodb_manager/test1_mongodb_manager").
 *
 * Only removes the suffix when it appears at a path-segment boundary — i.e.
 * followed by `/`, whitespace, or end-of-string — so parent directory names
 * that also carry the suffix (e.g. `/backups_mongodb_manager/`) are preserved.
 *
 * @example
 * stripBackupSuffixFromLine('Location: /backups_mongodb_manager/test1_mongodb_manager')
 * // → 'Location: /backups_mongodb_manager/test1'
 *
 * stripBackupSuffixFromLine('Location: /backups_mongodb_manager/test1_mongodb_manager ')
 * // → 'Location: /backups_mongodb_manager/test1 '
 */
export const stripBackupSuffixFromLine = (line: string): string => {
  if (!line) return line
  // Match the suffix only when followed by '/', whitespace, or end-of-string
  return line.replace(
    new RegExp(`${BACKUP_FOLDER_SUFFIX}(?=/|\\s|$)`, 'g'),
    ''
  )
}
