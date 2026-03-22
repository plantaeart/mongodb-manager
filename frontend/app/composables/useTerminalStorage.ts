/**
 * useTerminalStorage
 * 
 * Handles all localStorage persistence for the terminal:
 * favorites and command history.
 * Extracted from TerminalService to satisfy SRP.
 */

import { StorageKey, CommandStatus } from '~/enums'
import type { TerminalEntry } from '~/types/terminal'
import { TerminalConfig } from '~/enums'

export const useTerminalStorage = () => {
  /**
   * Load favorites from localStorage
   */
  function loadFavoritesFromStorage(): string[] {
    if (typeof window === 'undefined') return []

    const saved = localStorage.getItem(StorageKey.FAVORITE_COMMANDS)
    if (!saved) return []

    try {
      return JSON.parse(saved) as string[]
    } catch {
      return []
    }
  }

  /**
   * Persist favorites to localStorage
   */
  function saveFavoritesToStorage(favorites: string[]): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(StorageKey.FAVORITE_COMMANDS, JSON.stringify(favorites))
  }

  /**
   * Load command history from localStorage.
   * Only restores completed entries — active forms are marked as interrupted.
   */
  function loadHistoryFromStorage(): TerminalEntry[] {
    if (typeof window === 'undefined') return []

    const saved = localStorage.getItem(StorageKey.TERMINAL_HISTORY)
    if (!saved) return []

    try {
      const parsed: TerminalEntry[] = JSON.parse(saved)
      return parsed.map(e => {
        const entry = { ...e, timestamp: new Date(e.timestamp), form: undefined }
        if (entry.status === CommandStatus.RUNNING) {
          entry.status = CommandStatus.ERROR
          entry.output = ['Session interrupted — please re-run the command']
        }
        return entry
      })
    } catch {
      localStorage.removeItem(StorageKey.TERMINAL_HISTORY)
      return []
    }
  }

  /**
   * Persist command history to localStorage.
   * Strips live form objects and caps at PERSIST_HISTORY entries.
   */
  function saveHistoryToStorage(history: TerminalEntry[]): void {
    if (typeof window === 'undefined') return

    const toSave = history
      .slice(-TerminalConfig.PERSIST_HISTORY)
      .map(e => ({ ...e, form: undefined }))

    localStorage.setItem(StorageKey.TERMINAL_HISTORY, JSON.stringify(toSave))
  }

  /**
   * Remove the persisted history key (used by clearHistory)
   */
  function clearHistoryStorage(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(StorageKey.TERMINAL_HISTORY)
  }

  return {
    loadFavoritesFromStorage,
    saveFavoritesToStorage,
    loadHistoryFromStorage,
    saveHistoryToStorage,
    clearHistoryStorage
  }
}
