import { describe, it, expect } from 'vitest'
import { getStepperConfig, isStepperCommand } from '~/config/stepperRegistry'

// ── isStepperCommand — Backup Operations ───────────────────────────────────

describe('isStepperCommand — Backup Operations', () => {
  it('returns true for "backup create" (multi-step)', () => {
    expect(isStepperCommand('backup create')).toBe(true)
  })

  it('returns true for "backup restore" (multi-step)', () => {
    expect(isStepperCommand('backup restore')).toBe(true)
  })

  it('returns false for "backup list" (single-step, no stepper)', () => {
    expect(isStepperCommand('backup list')).toBe(false)
  })

  it('returns false for "backup delete" (single-step, no stepper)', () => {
    expect(isStepperCommand('backup delete')).toBe(false)
  })
})

// ── getStepperConfig — backup create shape ─────────────────────────────────

describe('getStepperConfig — backup create', () => {
  it('returns non-null config', () => {
    expect(getStepperConfig('backup create', 'form-1')).not.toBeNull()
  })

  it('forwards formId correctly', () => {
    const config = getStepperConfig('backup create', 'my-form-id')
    expect(config?.formId).toBe('my-form-id')
  })

  it('sets command to "backup create"', () => {
    const config = getStepperConfig('backup create', 'form-1')
    expect(config?.command).toBe('backup create')
  })

  it('returns exactly 2 steps', () => {
    const config = getStepperConfig('backup create', 'form-1')
    expect(config?.steps).toHaveLength(2)
  })

  it('step 1 has id "select_connection"', () => {
    const [step1] = getStepperConfig('backup create', 'form-1')!.steps
    expect(step1!.id).toBe('select_connection')
  })

  it('step 2 has id "configure_backup"', () => {
    const [, step2] = getStepperConfig('backup create', 'form-1')!.steps
    expect(step2!.id).toBe('configure_backup')
  })

  it('step 1 has a validate function', () => {
    const [step1] = getStepperConfig('backup create', 'form-1')!.steps
    expect(typeof step1!.validate).toBe('function')
  })

  it('step 2 has a validate function', () => {
    const [, step2] = getStepperConfig('backup create', 'form-1')!.steps
    expect(typeof step2!.validate).toBe('function')
  })
})

// ── getStepperConfig — backup restore shape ────────────────────────────────

describe('getStepperConfig — backup restore', () => {
  it('returns non-null config', () => {
    expect(getStepperConfig('backup restore', 'form-1')).not.toBeNull()
  })

  it('forwards formId correctly', () => {
    const config = getStepperConfig('backup restore', 'my-form-id')
    expect(config?.formId).toBe('my-form-id')
  })

  it('sets command to "backup restore"', () => {
    const config = getStepperConfig('backup restore', 'form-1')
    expect(config?.command).toBe('backup restore')
  })

  it('returns exactly 2 steps', () => {
    const config = getStepperConfig('backup restore', 'form-1')
    expect(config?.steps).toHaveLength(2)
  })

  it('step 1 has id "select_backup"', () => {
    const [step1] = getStepperConfig('backup restore', 'form-1')!.steps
    expect(step1!.id).toBe('select_backup')
  })

  it('step 2 has id "configure_restore"', () => {
    const [, step2] = getStepperConfig('backup restore', 'form-1')!.steps
    expect(step2!.id).toBe('configure_restore')
  })

  it('step 1 has a validate function', () => {
    const [step1] = getStepperConfig('backup restore', 'form-1')!.steps
    expect(typeof step1!.validate).toBe('function')
  })

  it('step 2 has a validate function', () => {
    const [, step2] = getStepperConfig('backup restore', 'form-1')!.steps
    expect(typeof step2!.validate).toBe('function')
  })
})

// ── returns null for non-stepper backup ops commands ──────────────────────

describe('getStepperConfig — backup list', () => {
  it('returns null for "backup list" (single-step)', () => {
    expect(getStepperConfig('backup list', 'form-1')).toBeNull()
  })
})

describe('getStepperConfig — backup delete', () => {
  it('returns null for "backup delete" (single-step)', () => {
    expect(getStepperConfig('backup delete', 'form-1')).toBeNull()
  })
})

// ── step validate — backup create ─────────────────────────────────────────

describe('getStepperConfig backup create — step 1 (select_connection) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup create', 'form-1')!
    const [step1] = config.steps
    return { validate: step1!.validate!, steps: config.steps }
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
    const [step1] = steps
    step1!.errors = { connection_name: 'Required' }
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(false)
  })
})

describe('getStepperConfig backup create — step 2 (configure_backup) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup create', 'form-1')!
    const [, step2] = config.steps
    return { validate: step2!.validate!, steps: config.steps }
  }

  it('returns true when backup_name and backup_location are both present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_name: 'my-backup', backup_location: '/backups' }, steps)).toBe(true)
  })

  it('returns false when backup_name is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_location: '/backups' }, steps)).toBe(false)
  })

  it('returns false when backup_location is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_name: 'my-backup' }, steps)).toBe(false)
  })

  it('returns false when backup_name is empty string', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_name: '', backup_location: '/backups' }, steps)).toBe(false)
  })

  it('returns false when backup_location is empty string', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_name: 'my-backup', backup_location: '' }, steps)).toBe(false)
  })

  it('returns false when step has errors', () => {
    const { validate, steps } = getContext()
    const [, step2] = steps
    step2!.errors = { backup_name: 'Required' }
    expect(validate({ backup_name: 'my-backup', backup_location: '/backups' }, steps)).toBe(false)
  })
})

// ── step validate — backup restore ────────────────────────────────────────

describe('getStepperConfig backup restore — step 1 (select_backup) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup restore', 'form-1')!
    const [step1] = config.steps
    return { validate: step1!.validate!, steps: config.steps }
  }

  it('returns false when backup_selector is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({}, steps)).toBe(false)
  })

  it('returns false when backup_selector is empty string', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_selector: '' }, steps)).toBe(false)
  })

  it('returns true when backup_selector is present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ backup_selector: 'my-conn/my-backup' }, steps)).toBe(true)
  })

  it('returns false when backup_selector is present but step has errors', () => {
    const { validate, steps } = getContext()
    const [step1] = steps
    step1!.errors = { backup_selector: 'Required' }
    expect(validate({ backup_selector: 'my-conn/my-backup' }, steps)).toBe(false)
  })
})

describe('getStepperConfig backup restore — step 2 (configure_restore) validate', () => {
  function getContext() {
    const config = getStepperConfig('backup restore', 'form-1')!
    const [, step2] = config.steps
    return { validate: step2!.validate!, steps: config.steps }
  }

  it('returns true when connection_name and confirmation are both present and no errors', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: 'my-conn', confirmation: true }, steps)).toBe(true)
  })

  it('returns false when connection_name is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({ confirmation: true }, steps)).toBe(false)
  })

  it('returns false when confirmation is absent', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(false)
  })

  it('returns false when confirmation is false', () => {
    const { validate, steps } = getContext()
    expect(validate({ connection_name: 'my-conn', confirmation: false }, steps)).toBe(false)
  })

  it('returns false when step has errors', () => {
    const { validate, steps } = getContext()
    const [, step2] = steps
    step2!.errors = { connection_name: 'Required' }
    expect(validate({ connection_name: 'my-conn', confirmation: true }, steps)).toBe(false)
  })
})
