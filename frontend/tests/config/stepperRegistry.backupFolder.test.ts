import { describe, it, expect } from 'vitest'
import { getStepperConfig, isStepperCommand } from '~/config/stepperRegistry'

// ── isStepperCommand — Backup Folder Management ────────────────────────────

describe('isStepperCommand — Backup Folder Management', () => {
  it('returns true for "backup folder add" (multi-step)', () => {
    expect(isStepperCommand('backup folder add')).toBe(true)
  })

  it('returns true for "backup folder delete" (multi-step)', () => {
    expect(isStepperCommand('backup folder delete')).toBe(true)
  })

  it('returns false for "backup folder list" (single-step, no stepper)', () => {
    expect(isStepperCommand('backup folder list')).toBe(false)
  })
})

// ── getStepperConfig — backup folder add shape ─────────────────────────────

describe('getStepperConfig — backup folder add', () => {
  it('returns non-null config', () => {
    expect(getStepperConfig('backup folder add', 'form-1')).not.toBeNull()
  })

  it('forwards formId correctly', () => {
    const config = getStepperConfig('backup folder add', 'my-form-id')
    expect(config?.formId).toBe('my-form-id')
  })

  it('sets command to "backup folder add"', () => {
    const config = getStepperConfig('backup folder add', 'form-1')
    expect(config?.command).toBe('backup folder add')
  })

  it('returns exactly 2 steps', () => {
    const config = getStepperConfig('backup folder add', 'form-1')
    expect(config?.steps).toHaveLength(2)
  })

  it('step 1 has id "configure_folder"', () => {
    const [step1] = getStepperConfig('backup folder add', 'form-1')!.steps
    expect(step1!.id).toBe('configure_folder')
  })

  it('step 2 has id "select_connection"', () => {
    const [, step2] = getStepperConfig('backup folder add', 'form-1')!.steps
    expect(step2!.id).toBe('select_connection')
  })

  it('step 1 has a validate function', () => {
    const [step1] = getStepperConfig('backup folder add', 'form-1')!.steps
    expect(typeof step1!.validate).toBe('function')
  })

  it('step 2 has a validate function', () => {
    const [, step2] = getStepperConfig('backup folder add', 'form-1')!.steps
    expect(typeof step2!.validate).toBe('function')
  })
})

// ── getStepperConfig — backup folder delete shape ──────────────────────────

describe('getStepperConfig — backup folder delete', () => {
  it('returns non-null config', () => {
    expect(getStepperConfig('backup folder delete', 'form-1')).not.toBeNull()
  })

  it('forwards formId correctly', () => {
    const config = getStepperConfig('backup folder delete', 'my-form-id')
    expect(config?.formId).toBe('my-form-id')
  })

  it('sets command to "backup folder delete"', () => {
    const config = getStepperConfig('backup folder delete', 'form-1')
    expect(config?.command).toBe('backup folder delete')
  })

  it('returns exactly 2 steps', () => {
    const config = getStepperConfig('backup folder delete', 'form-1')
    expect(config?.steps).toHaveLength(2)
  })

  it('step 1 has id "select_connection"', () => {
    const [step1] = getStepperConfig('backup folder delete', 'form-1')!.steps
    expect(step1!.id).toBe('select_connection')
  })

  it('step 2 has id "confirm_delete"', () => {
    const [, step2] = getStepperConfig('backup folder delete', 'form-1')!.steps
    expect(step2!.id).toBe('confirm_delete')
  })

  it('step 1 has a validate function', () => {
    const [step1] = getStepperConfig('backup folder delete', 'form-1')!.steps
    expect(typeof step1!.validate).toBe('function')
  })

  it('step 2 has a validate function', () => {
    const [, step2] = getStepperConfig('backup folder delete', 'form-1')!.steps
    expect(typeof step2!.validate).toBe('function')
  })
})

// ── returns null for non-stepper backup folder command ─────────────────────

describe('getStepperConfig — backup folder list', () => {
  it('returns null for "backup folder list" (single-step)', () => {
    expect(getStepperConfig('backup folder list', 'form-1')).toBeNull()
  })
})

// ── step validate — backup folder add ─────────────────────────────────────

describe('getStepperConfig backup folder add — step 1 (configure_folder) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup folder add', 'form-1')!
    const [step1] = config.steps
    return { validate: step1!.validate!, steps: config.steps }
  }

  it('returns false when folder_path is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({}, steps)).toBe(false)
  })

  it('returns false when folder_path is empty string', () => {
    const { validate, steps } = getContext()
    expect(validate({ folder_path: '' }, steps)).toBe(false)
  })

  it('returns true when folder_path is present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ folder_path: '/backups/my-conn' }, steps)).toBe(true)
  })

  it('returns false when folder_path is present but step has errors', () => {
    const { validate, steps } = getContext()
    const [step1] = steps
    step1!.errors = { folder_path: 'Invalid path' }
    expect(validate({ folder_path: '/backups/my-conn' }, steps)).toBe(false)
  })
})

describe('getStepperConfig backup folder add — step 2 (select_connection) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup folder add', 'form-1')!
    const [, step2] = config.steps
    return { validate: step2!.validate!, steps: config.steps }
  }

  it('returns false when connection_name is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({}, steps)).toBe(false)
  })

  it('returns false when connection_name is empty string', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: '' }, steps)).toBe(false)
  })

  it('returns true when connection_name is present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(true)
  })

  it('returns false when connection_name is present but step has errors', () => {
    const { validate, steps } = getContext()
    const [, step2] = steps
    step2!.errors = { connection_name: 'Required' }
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(false)
  })
})

// ── step validate — backup folder delete ───────────────────────────────────

describe('getStepperConfig backup folder delete — step 1 (select_connection) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup folder delete', 'form-1')!
    const [step1] = config.steps
    return { validate: step1!.validate!, steps: config.steps }
  }

  it('returns false when connection_name is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({}, steps)).toBe(false)
  })

  it('returns true when connection_name is present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(true)
  })

  it('returns false when step has errors', () => {
    const { validate, steps } = getContext()
    const [step1] = steps
    step1!.errors = { connection_name: 'Required' }
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(false)
  })
})

describe('getStepperConfig backup folder delete — step 2 (confirm_delete) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup folder delete', 'form-1')!
    const [, step2] = config.steps
    return { validate: step2!.validate!, steps: config.steps }
  }

  it('returns true when folder_path and confirmation are both present', () => {
    const { validate, steps } = getContext()
    expect(validate({ folder_path: '/backups/my-conn', confirmation: true }, steps)).toBe(true)
  })

  it('returns false when folder_path is missing', () => {
    const { validate, steps } = getContext()
    expect(validate({ confirmation: true }, steps)).toBe(false)
  })

  it('returns false when confirmation is missing', () => {
    const { validate, steps } = getContext()
    expect(validate({ folder_path: '/backups/my-conn' }, steps)).toBe(false)
  })

  it('returns false when confirmation is false', () => {
    const { validate, steps } = getContext()
    expect(validate({ folder_path: '/backups/my-conn', confirmation: false }, steps)).toBe(false)
  })

  it('returns false when step has errors', () => {
    const { validate, steps } = getContext()
    const [, step2] = steps
    step2!.errors = { folder_path: 'Required' }
    expect(validate({ folder_path: '/backups/my-conn', confirmation: true }, steps)).toBe(false)
  })
})
