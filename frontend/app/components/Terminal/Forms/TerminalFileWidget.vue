<template>
  <!-- Readonly / done state -->
  <div v-if="isReadonly" class="widget-done-state">
    <span v-if="doneMessage" class="status-submitted">✓ {{ doneMessage }}</span>
    <span v-else class="status-cancelled">✗ Cancelled</span>
  </div>

  <!-- Active widget -->
  <div v-else class="terminal-file-widget">
    <!-- Header -->
    <div class="widget-header">
      <h3>{{ title }}</h3>
      <p v-if="description" class="widget-description">{{ description }}</p>
    </div>

    <!-- Body -->
    <div class="widget-body">

      <!-- ── backup export ─────────────────────────────────── -->
      <template v-if="widgetData.mode === 'backup-export'">
        <div class="field-group">
          <label class="field-label">Select Backup to Export</label>
          <select v-model="backupSelector" class="field-select" :disabled="isBusy">
            <option value="" disabled>— choose a backup —</option>
            <option
              v-for="opt in widgetData.backupOptions"
              :key="opt.value"
              :value="opt.value"
            >{{ opt.label }}</option>
          </select>
          <p v-if="widgetData.backupOptions?.length === 0" class="field-hint warn">
            No backups found. Create one first with <code>backup create</code>.
          </p>
          <p v-else class="field-hint">Choose the backup to download as a ZIP file.</p>
        </div>
      </template>

      <!-- ── backup import ─────────────────────────────────── -->
      <template v-else-if="widgetData.mode === 'backup-import'">
        <div class="field-group">
          <label class="field-label">Destination Folder</label>
          <select v-model="folderPath" class="field-select" :disabled="isBusy">
            <option value="" disabled>— choose a backup folder —</option>
            <option
              v-for="opt in widgetData.folderOptions"
              :key="opt.value"
              :value="opt.value"
            >{{ opt.label }}</option>
          </select>
          <p v-if="widgetData.folderOptions?.length === 0" class="field-hint warn">
            No backup folders registered. Add one first with <code>backup folder add</code>.
          </p>
          <p v-else class="field-hint">Select the registered folder where the backup will be imported.</p>
        </div>

        <div class="field-group">
          <label class="field-label">ZIP File</label>
          <div class="file-input-wrapper">
            <input
              ref="fileInputRef"
              type="file"
              accept=".zip"
              class="file-input-hidden"
              :disabled="isBusy"
              @change="onFileSelected"
            />
            <button class="file-pick-btn" :disabled="isBusy" @click="fileInputRef?.click()">
              📁 Choose ZIP file
            </button>
            <span class="file-name">{{ selectedFileName || 'No file chosen' }}</span>
          </div>
          <p class="field-hint">Select the <code>.zip</code> file previously exported from this app.</p>
        </div>

        <div class="field-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="overwrite" type="checkbox" :disabled="isBusy" />
            <span>Overwrite existing backup if name conflicts</span>
          </label>
        </div>
      </template>

      <!-- ── connect export ────────────────────────────────── -->
      <template v-else-if="widgetData.mode === 'connect-export'">
        <div class="info-box">
          <p>📋 Downloads a <strong>connections.json</strong> file with all your connections.</p>
          <p class="warn-text">⚠️ Passwords are <strong>not included</strong> in the export.</p>
        </div>
      </template>

      <!-- ── connect import ────────────────────────────────── -->
      <template v-else-if="widgetData.mode === 'connect-import'">
        <div class="field-group">
          <label class="field-label">JSON File</label>
          <div class="file-input-wrapper">
            <input
              ref="fileInputRef"
              type="file"
              accept=".json,application/json"
              class="file-input-hidden"
              :disabled="isBusy"
              @change="onFileSelected"
            />
            <button class="file-pick-btn" :disabled="isBusy" @click="fileInputRef?.click()">
              📁 Choose JSON file
            </button>
            <span class="file-name">{{ selectedFileName || 'No file chosen' }}</span>
          </div>
          <p class="field-hint">Select the <code>connections.json</code> file exported from this app.</p>
        </div>

        <div class="field-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="overwrite" type="checkbox" :disabled="isBusy" />
            <span>Overwrite existing connections with the same name</span>
          </label>
        </div>

        <div class="field-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="importBackupPaths" type="checkbox" :disabled="isBusy" />
            <span>Import backup folder paths from file</span>
          </label>
          <p class="field-hint">Only enable if the backup folders exist at the same paths on this machine.</p>
        </div>
      </template>

      <!-- Error message -->
      <div v-if="errorMessage" class="error-msg">✗ {{ errorMessage }}</div>

    </div>

    <!-- Actions -->
    <div class="widget-actions">
      <button
        class="action-btn action-primary"
        :disabled="!canSubmit || isBusy"
        @click="handleSubmit"
      >
        <span v-if="isBusy" class="spinner"></span>
        {{ isBusy ? 'Processing…' : submitLabel }}
      </button>
      <button class="action-btn action-secondary" :disabled="isBusy" @click="emit('cancel')">
        Cancel
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FileWidgetData } from '~/types/terminal'
import { downloadBlob } from '~/utils/downloadFile'

interface Props {
  widgetData: FileWidgetData
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  done: [message: string]
  cancel: []
}>()

// ── State ────────────────────────────────────────────────────────────────────

const backupSelector = ref('')
const folderPath = ref('')
const selectedFile = ref<File | null>(null)
const selectedFileName = ref('')
const overwrite = ref(false)
const importBackupPaths = ref(false)
const isBusy = ref(false)
const errorMessage = ref('')
const doneMessage = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

const isReadonly = computed(() => props.readonly)

// ── Metadata ─────────────────────────────────────────────────────────────────

const modeConfig: Record<FileWidgetData['mode'], { title: string; description: string; submitLabel: string }> = {
  'backup-export': {
    title: 'Export Backup',
    description: 'Download a backup as a ZIP file to your computer',
    submitLabel: '⬇ Export & Download',
  },
  'backup-import': {
    title: 'Import Backup',
    description: 'Upload a ZIP file and import it into a backup folder',
    submitLabel: '⬆ Import Backup',
  },
  'connect-export': {
    title: 'Export Connections',
    description: 'Download all connections as a JSON file (passwords excluded)',
    submitLabel: '⬇ Export & Download',
  },
  'connect-import': {
    title: 'Import Connections',
    description: 'Upload a connections JSON file to import saved connections',
    submitLabel: '⬆ Import Connections',
  },
}

const title = computed(() => modeConfig[props.widgetData.mode].title)
const description = computed(() => modeConfig[props.widgetData.mode].description)
const submitLabel = computed(() => modeConfig[props.widgetData.mode].submitLabel)

// ── Validation ───────────────────────────────────────────────────────────────

const canSubmit = computed(() => {
  const mode = props.widgetData.mode
  if (mode === 'backup-export') return !!backupSelector.value
  if (mode === 'backup-import') return !!folderPath.value && !!selectedFile.value
  if (mode === 'connect-export') return true
  if (mode === 'connect-import') return !!selectedFile.value
  return false
})

// ── File picker handler ───────────────────────────────────────────────────────

const onFileSelected = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  selectedFile.value = file
  selectedFileName.value = file?.name ?? ''
  errorMessage.value = ''
}

// ── API base URL ──────────────────────────────────────────────────────────────

const config = useRuntimeConfig()
const baseUrl = config.public.apiUrl as string

const authStore = useAuthStore()

// ── Submit ───────────────────────────────────────────────────────────────────

const handleSubmit = async () => {
  errorMessage.value = ''
  isBusy.value = true

  try {
    const mode = props.widgetData.mode

    if (mode === 'backup-export') {
      await doBackupExport()
    } else if (mode === 'backup-import') {
      await doBackupImport()
    } else if (mode === 'connect-export') {
      await doConnectExport()
    } else if (mode === 'connect-import') {
      await doConnectImport()
    }
  } catch (err: any) {
    errorMessage.value = err?.message ?? 'Unexpected error'
  } finally {
    isBusy.value = false
  }
}

// ── backup export ─────────────────────────────────────────────────────────────

const doBackupExport = async () => {
  const response = await fetch(
    `${baseUrl}/api/transfer/backup/export?backup_selector=${encodeURIComponent(backupSelector.value)}`,
    { headers: { Authorization: `Bearer ${authStore.token}` } }
  )

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: 'Export failed' }))
    throw new Error(detail.detail ?? 'Export failed')
  }

  const blob = await response.blob()
  // Derive filename from Content-Disposition or fallback
  const cd = response.headers.get('Content-Disposition') ?? ''
  const match = cd.match(/filename="?([^"]+)"?/)
  const filename = match?.[1] ?? `${backupSelector.value.split('|')[1] ?? 'backup'}.zip`

  downloadBlob(blob, filename)

  doneMessage.value = `Downloaded ${filename}`
  emit('done', `✓ Backup exported as "${filename}"`)
}

// ── backup import ─────────────────────────────────────────────────────────────

const doBackupImport = async () => {
  if (!selectedFile.value) return

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('folder_path', folderPath.value)
  formData.append('overwrite', String(overwrite.value))

  const response = await fetch(`${baseUrl}/api/transfer/backup/import`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${authStore.token}` },
    body: formData,
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail ?? 'Import failed')
  }

  doneMessage.value = data.message
  emit('done', `✓ ${data.message}`)
}

// ── connect export ────────────────────────────────────────────────────────────

const doConnectExport = async () => {
  const response = await fetch(`${baseUrl}/api/transfer/connect/export`, {
    headers: { Authorization: `Bearer ${authStore.token}` },
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: 'Export failed' }))
    throw new Error(detail.detail ?? 'Export failed')
  }

  const blob = await response.blob()
  downloadBlob(blob, 'connections.json')

  doneMessage.value = 'Downloaded connections.json'
  emit('done', '✓ Connections exported as "connections.json"')
}

// ── connect import ────────────────────────────────────────────────────────────

const doConnectImport = async () => {
  if (!selectedFile.value) return

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('overwrite', String(overwrite.value))
  formData.append('import_backup_paths', String(importBackupPaths.value))

  const response = await fetch(`${baseUrl}/api/transfer/connect/import`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${authStore.token}` },
    body: formData,
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail ?? 'Import failed')
  }

  const { imported = 0, overwritten = 0, skipped = 0, errors = [] } = data
  const parts = []
  if (imported) parts.push(`${imported} imported`)
  if (overwritten) parts.push(`${overwritten} overwritten`)
  if (skipped) parts.push(`${skipped} skipped`)
  const summary = parts.length ? parts.join(', ') : 'no changes'

  doneMessage.value = `${summary}`
  const errNote = errors.length ? ` (${errors.length} error(s): ${errors.slice(0, 2).join('; ')})` : ''
  emit('done', `✓ Connections imported: ${summary}${errNote}`)
}
</script>

<style scoped>
/* ── Container ── */
.terminal-file-widget {
  background: var(--color-bg-primary, #1d2021);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  padding: 16px;
  margin: 12px 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

/* ── Header ── */
.widget-header {
  border-bottom: 1px solid var(--color-border-secondary, #504945);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.widget-header h3 {
  color: var(--color-primary, #83a598);
  font-size: 16px;
  margin: 0 0 4px 0;
  font-weight: 600;
}

.widget-description {
  color: var(--color-text-tertiary, #928374);
  font-size: 13px;
  margin: 0;
}

/* ── Body ── */
.widget-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Field groups ── */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  color: var(--color-text-secondary, #d5c4a1);
  font-size: 13px;
  font-weight: 500;
}

.field-select {
  background: var(--color-bg-secondary, #3c3836);
  border: 1px solid var(--color-border-secondary, #504945);
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 8px 10px;
  border-radius: 3px;
  width: 100%;
  cursor: pointer;
}

.field-select:focus {
  outline: none;
  border-color: var(--color-primary, #83a598);
}

.field-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-hint {
  color: var(--color-text-tertiary, #928374);
  font-size: 12px;
  margin: 0;
}

.field-hint.warn {
  color: var(--color-warning, #fe8019);
}

/* ── File input ── */
.file-input-hidden {
  display: none;
}

.file-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-pick-btn {
  background: var(--color-bg-secondary, #3c3836);
  border: 1px solid var(--color-border-secondary, #504945);
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 7px 12px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.file-pick-btn:hover:not(:disabled) {
  background: var(--color-bg-tertiary, #504945);
}

.file-pick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-name {
  color: var(--color-text-tertiary, #928374);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

/* ── Checkboxes ── */
.checkbox-group {
  gap: 4px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  color: var(--color-text-primary, #ebdbb2);
  font-size: 13px;
  line-height: 1.4;
}

.checkbox-label input[type='checkbox'] {
  margin-top: 2px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--color-primary, #83a598);
}

/* ── Info box (connect export) ── */
.info-box {
  background: var(--color-bg-secondary, #3c3836);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 3px;
  padding: 12px 14px;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-box p {
  margin: 0;
  color: var(--color-text-primary, #ebdbb2);
}

.warn-text {
  color: var(--color-warning, #fe8019) !important;
}

/* ── Error ── */
.error-msg {
  color: var(--color-danger, #fb4934);
  font-size: 13px;
  padding: 8px 10px;
  background: rgba(204, 36, 29, 0.1);
  border: 1px solid rgba(204, 36, 29, 0.3);
  border-radius: 3px;
}

/* ── Actions ── */
.widget-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary, #504945);
  margin-top: 4px;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
  border: none;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-primary {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.action-primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #8ec07c);
}

.action-secondary {
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945) !important;
}

.action-secondary:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

/* ── Spinner ── */
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Done state ── */
.widget-done-state {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 4px 0;
}

.status-submitted {
  color: var(--color-success, #b8bb26);
}

.status-cancelled {
  color: var(--color-warning, #fe8019);
}

/* ── code ── */
code {
  background: var(--color-bg-tertiary, #504945);
  padding: 1px 5px;
  border-radius: 2px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .widget-actions {
    flex-direction: column;
  }
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  .file-input-wrapper {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
