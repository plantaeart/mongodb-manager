/**
 * Terminal output line patterns
 * Regex patterns for syntax highlighting and line classification
 */
export enum OutputLinePattern {
  SUCCESS = '^(✓|✔|SUCCESS|Created|Added|Completed|Connected)',
  ERROR = '^(✗|✘|ERROR|Failed|Error:|Exception)',
  WARNING = '^(⚠|WARNING|Warning:|Note:)',
  INFO = '^(ℹ|INFO|→|•)'
}
