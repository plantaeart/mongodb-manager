/**
 * Stepper Workflow Tests
 *
 * These tests simulate the multi-step UI flow end-to-end at the pure-function
 * level — no Nuxt runtime, no $fetch calls.
 *
 * For each stepper command we:
 *   1. Construct the config via the factory (same as the real UI does)
 *   2. Populate step 1 data (as if the user filled out the form)
 *   3. Assert step 1 validates correctly (canProceedFromStep + isStepValid)
 *   4. Assert step 2 reads step 1 data correctly via getAllStepData
 *   5. Populate step 2 data and assert step 2 validates correctly
 *   6. Assert getAllStepData returns the merged payload
 *
 * Covered commands:
 *   - connect update     (select_connection → update_details)
 *   - backup folder add  (configure_folder → select_connection)
 *   - backup folder delete (select_connection → confirm_delete)
 *   - backup create      (select_connection → configure_backup)
 *   - backup restore     (select_backup → configure_restore)
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { getStepperConfig } from '~/config/stepperRegistry'
import {
  createStep,
  getAllStepData,
  isStepValid,
  canProceedFromStep,
} from '~/utils/stepperHelpers'
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Deep-clone config so mutations in one test don't bleed into the next */
function freshConfig(command: string): StepperFormConfig {
  const config = getStepperConfig(command, `form-${command.replace(/\s+/g, '-')}`)!
  // Re-create each step from scratch to avoid shared object refs
  const steps: StepDefinition[] = config.steps.map(step => ({
    ...createStep(step.id, step.config.title, step.config.description, step.config.icon),
    validate: step.validate,
    loadData: step.loadData,
    component: step.component,
  }))
  return { ...config, steps }
}

// ── createStep helper ─────────────────────────────────────────────────────────

describe('createStep — factory defaults', () => {
  it('returns a step with empty data, errors, and isLoading=false', () => {
    const step = createStep('my-step', 'My Title', 'My Description', 'i-lucide-star')
    expect(step.id).toBe('my-step')
    expect(step.config.title).toBe('My Title')
    expect(step.config.description).toBe('My Description')
    expect(step.config.icon).toBe('i-lucide-star')
    expect(step.data).toEqual({})
    expect(step.errors).toEqual({})
    expect(step.isLoading).toBe(false)
    expect(step.config.disabled).toBe(false)
  })

  it('icon is optional — step is created without it', () => {
    const step = createStep('no-icon', 'Title', 'Desc')
    expect(step.config.icon).toBeUndefined()
  })
})

// ── getAllStepData ─────────────────────────────────────────────────────────────

describe('getAllStepData — data merging', () => {
  it('returns empty object when all steps have empty data', () => {
    const steps = [
      createStep('s1', 'Step 1', 'First'),
      createStep('s2', 'Step 2', 'Second'),
    ]
    expect(getAllStepData(steps)).toEqual({})
  })

  it('merges data from a single step', () => {
    const steps = [createStep('s1', 'Step 1', 'First')]
    steps[0]!.data = { name: 'foo', host: 'localhost' }
    expect(getAllStepData(steps)).toEqual({ name: 'foo', host: 'localhost' })
  })

  it('merges data from two steps into one flat object', () => {
    const steps = [
      createStep('s1', 'Step 1', 'First'),
      createStep('s2', 'Step 2', 'Second'),
    ]
    steps[0]!.data = { connection_name: 'my-conn' }
    steps[1]!.data = { backup_name: 'my-backup', backup_location: '/backups' }
    expect(getAllStepData(steps)).toEqual({
      connection_name: 'my-conn',
      backup_name: 'my-backup',
      backup_location: '/backups',
    })
  })

  it('later step data overrides earlier step data for the same key', () => {
    const steps = [
      createStep('s1', 'Step 1', 'First'),
      createStep('s2', 'Step 2', 'Second'),
    ]
    steps[0]!.data = { connection_name: 'original' }
    steps[1]!.data = { connection_name: 'override' }
    expect(getAllStepData(steps)).toEqual({ connection_name: 'override' })
  })

  it('handles three steps correctly', () => {
    const steps = [
      createStep('s1', 'Step 1', 'First'),
      createStep('s2', 'Step 2', 'Second'),
      createStep('s3', 'Step 3', 'Third'),
    ]
    steps[0]!.data = { a: 1 }
    steps[1]!.data = { b: 2 }
    steps[2]!.data = { c: 3 }
    expect(getAllStepData(steps)).toEqual({ a: 1, b: 2, c: 3 })
  })
})

// ── isStepValid ───────────────────────────────────────────────────────────────

describe('isStepValid — validation logic', () => {
  it('returns true for a step with no validate fn and no errors', () => {
    const step = createStep('s1', 'Step 1', 'First')
    expect(isStepValid(step, [step])).toBe(true)
  })

  it('returns false for a step with errors but no validate fn', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.errors = { name: 'Required' }
    expect(isStepValid(step, [step])).toBe(false)
  })

  it('returns false when validate fn returns false (regardless of errors)', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => false
    expect(isStepValid(step, [step])).toBe(false)
  })

  it('returns true when validate fn returns true and no errors', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => true
    expect(isStepValid(step, [step])).toBe(true)
  })

  it('returns false when validate fn returns true but step has errors', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => true
    step.errors = { name: 'Too long' }
    expect(isStepValid(step, [step])).toBe(false)
  })
})

// ── canProceedFromStep ────────────────────────────────────────────────────────

describe('canProceedFromStep — step gating', () => {
  it('returns false for out-of-bounds index', () => {
    const steps = [createStep('s1', 'Step 1', 'First')]
    expect(canProceedFromStep(99, steps)).toBe(false)
  })

  it('returns false when step is loading', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.isLoading = true
    expect(canProceedFromStep(0, [step])).toBe(false)
  })

  it('returns false when step isLoading even if validate passes', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => true
    step.isLoading = true
    expect(canProceedFromStep(0, [step])).toBe(false)
  })

  it('returns true when step is valid and not loading', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => true
    expect(canProceedFromStep(0, [step])).toBe(true)
  })

  it('returns false when step is invalid and not loading', () => {
    const step = createStep('s1', 'Step 1', 'First')
    step.validate = () => false
    expect(canProceedFromStep(0, [step])).toBe(false)
  })
})

// ── connect update — workflow ──────────────────────────────────────────────────

describe('connect update — inter-step workflow', () => {
  let config: StepperFormConfig

  beforeEach(() => {
    config = freshConfig('connect update')
  })

  it('has exactly 2 steps: select_connection → update_details', () => {
    const [step1, step2] = config.steps
    expect(step1!.id).toBe('select_connection')
    expect(step2!.id).toBe('update_details')
  })

  it('step 1 cannot proceed when empty', () => {
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 can proceed after selecting a single connection', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 1 can proceed when connection_name is a 1-element array', () => {
    config.steps[0]!.data = { connection_name: ['my-conn'] }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 1 cannot proceed when connection_name is an empty array', () => {
    config.steps[0]!.data = { connection_name: [] }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 cannot proceed when connection_name is a 2-element array', () => {
    config.steps[0]!.data = { connection_name: ['conn-a', 'conn-b'] }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed without required fields', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {}
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed with name, host, port and no auth', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { name: 'my-conn', host: 'localhost', port: 27017 }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('step 2 cannot proceed when username given but no password', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      name: 'my-conn',
      host: 'localhost',
      port: 27017,
      username: 'admin',
      password: '',
    }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed when username and password are both provided', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      name: 'my-conn',
      host: 'localhost',
      port: 27017,
      username: 'admin',
      password: 'secret',
    }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('getAllStepData merges both steps into a flat submission payload', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { name: 'my-conn', host: 'new-host', port: 27017 }
    expect(getAllStepData(config.steps)).toEqual({
      connection_name: 'my-conn',
      name: 'my-conn',
      host: 'new-host',
      port: 27017,
    })
  })
})

// ── backup folder add — workflow ──────────────────────────────────────────────

describe('backup folder add — inter-step workflow', () => {
  let config: StepperFormConfig

  beforeEach(() => {
    config = freshConfig('backup folder add')
  })

  it('has exactly 2 steps: configure_folder → select_connection', () => {
    const [step1, step2] = config.steps
    expect(step1!.id).toBe('configure_folder')
    expect(step2!.id).toBe('select_connection')
  })

  it('step 1 cannot proceed when folder_path is absent', () => {
    config.steps[0]!.data = {}
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 cannot proceed when folder_path is empty string', () => {
    config.steps[0]!.data = { folder_path: '' }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 can proceed when folder_path is provided', () => {
    config.steps[0]!.data = { folder_path: '/backups/my-conn' }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 1 cannot proceed when step has errors', () => {
    config.steps[0]!.data = { folder_path: '/backups/my-conn' }
    config.steps[0]!.errors = { folder_path: 'Invalid path' }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed when connection_name is absent', () => {
    config.steps[0]!.data = { folder_path: '/backups/my-conn' }
    config.steps[1]!.data = {}
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed when connection_name is selected', () => {
    config.steps[0]!.data = { folder_path: '/backups/my-conn' }
    config.steps[1]!.data = { connection_name: 'my-conn' }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('getAllStepData merges folder path and connection into submission payload', () => {
    config.steps[0]!.data = { folder_path: '/backups/my-conn', create_if_missing: true }
    config.steps[1]!.data = { connection_name: 'my-conn' }
    expect(getAllStepData(config.steps)).toEqual({
      folder_path: '/backups/my-conn',
      create_if_missing: true,
      connection_name: 'my-conn',
    })
  })
})

// ── backup folder delete — workflow ───────────────────────────────────────────

describe('backup folder delete — inter-step workflow', () => {
  let config: StepperFormConfig

  beforeEach(() => {
    config = freshConfig('backup folder delete')
  })

  it('has exactly 2 steps: select_connection → confirm_delete', () => {
    const [step1, step2] = config.steps
    expect(step1!.id).toBe('select_connection')
    expect(step2!.id).toBe('confirm_delete')
  })

  it('step 1 cannot proceed when connection_name is absent', () => {
    config.steps[0]!.data = {}
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 can proceed when connection_name is selected', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 2 cannot proceed without folder_path', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { confirmation: true }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed without confirmation', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { folder_path: '/backups/my-conn', confirmation: false }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed when confirmation is absent', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { folder_path: '/backups/my-conn' }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed when folder_path and confirmation are both provided', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      folder_path: '/backups/my-conn',
      confirmation: true,
      connection_name: 'my-conn',
    }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('getAllStepData merges both steps — connection_name from step 1 available in payload', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      folder_path: '/backups/my-conn',
      confirmation: true,
      connection_name: 'my-conn',
    }
    const payload = getAllStepData(config.steps)
    expect(payload.connection_name).toBe('my-conn')
    expect(payload.folder_path).toBe('/backups/my-conn')
    expect(payload.confirmation).toBe(true)
  })
})

// ── backup create — workflow ───────────────────────────────────────────────────

describe('backup create — inter-step workflow', () => {
  let config: StepperFormConfig

  beforeEach(() => {
    config = freshConfig('backup create')
  })

  it('has exactly 2 steps: select_connection → configure_backup', () => {
    const [step1, step2] = config.steps
    expect(step1!.id).toBe('select_connection')
    expect(step2!.id).toBe('configure_backup')
  })

  it('step 1 cannot proceed when empty', () => {
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 can proceed when connection_name is provided', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 2 cannot proceed without backup_name', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { backup_location: '/backups/my-conn' }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed without backup_location', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = { backup_name: 'my-backup' }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed when backup_name and backup_location are both provided', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      backup_name: 'my-backup',
      backup_location: '/backups/my-conn',
      connection_name: 'my-conn',
    }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('step 2 cannot proceed when step has errors', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      backup_name: 'my-backup',
      backup_location: '/backups/my-conn',
    }
    config.steps[1]!.errors = { backup_name: 'Name already taken' }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('getAllStepData contains all fields needed for submission', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      connection_name: 'my-conn',
      backup_name: 'my-backup',
      backup_location: '/backups/my-conn',
    }
    const payload = getAllStepData(config.steps)
    // Step 2 overrides connection_name — that's fine, it's the same value
    expect(payload.connection_name).toBe('my-conn')
    expect(payload.backup_name).toBe('my-backup')
    expect(payload.backup_location).toBe('/backups/my-conn')
  })

  it('getAllStepData: step 1 connection_name is available even without step 2 override', () => {
    config.steps[0]!.data = { connection_name: 'my-conn' }
    config.steps[1]!.data = {
      backup_name: 'my-backup',
      backup_location: '/backups/my-conn',
    }
    const payload = getAllStepData(config.steps)
    // Step 1 provides connection_name, step 2 doesn't override it
    expect(payload.connection_name).toBe('my-conn')
  })
})

// ── backup restore — workflow ─────────────────────────────────────────────────

describe('backup restore — inter-step workflow', () => {
  let config: StepperFormConfig

  beforeEach(() => {
    config = freshConfig('backup restore')
  })

  it('has exactly 2 steps: select_backup → configure_restore', () => {
    const [step1, step2] = config.steps
    expect(step1!.id).toBe('select_backup')
    expect(step2!.id).toBe('configure_restore')
  })

  it('step 1 cannot proceed when empty', () => {
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 can proceed when backup_selector is provided', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    expect(canProceedFromStep(0, config.steps)).toBe(true)
  })

  it('step 1 cannot proceed when backup_selector is empty string', () => {
    config.steps[0]!.data = { backup_selector: '' }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 1 cannot proceed when step has errors', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[0]!.errors = { backup_selector: 'Invalid' }
    expect(canProceedFromStep(0, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed without connection_name', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      confirmation: true,
    }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed without confirmation', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      connection_name: 'my-conn',
    }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 cannot proceed when confirmation is false', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      connection_name: 'my-conn',
      confirmation: false,
    }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('step 2 can proceed when backup_selector, connection_name and confirmation are all present', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      connection_name: 'my-conn',
      confirmation: true,
    }
    expect(canProceedFromStep(1, config.steps)).toBe(true)
  })

  it('step 2 cannot proceed when step has errors', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      connection_name: 'my-conn',
      confirmation: true,
    }
    config.steps[1]!.errors = { connection_name: 'Not found' }
    expect(canProceedFromStep(1, config.steps)).toBe(false)
  })

  it('getAllStepData carries backup_selector from step 1 into merged payload', () => {
    config.steps[0]!.data = { backup_selector: '/backups/my-conn|my-backup' }
    config.steps[1]!.data = {
      backup_selector: '/backups/my-conn|my-backup',
      connection_name: 'my-conn',
      confirmation: true,
    }
    const payload = getAllStepData(config.steps)
    expect(payload.backup_selector).toBe('/backups/my-conn|my-backup')
    expect(payload.connection_name).toBe('my-conn')
    expect(payload.confirmation).toBe(true)
  })
})
