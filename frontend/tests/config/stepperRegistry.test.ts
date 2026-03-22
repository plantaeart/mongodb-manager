import { describe, it, expect } from 'vitest'
import { getStepperConfig, isStepperCommand } from '~/config/stepperRegistry'

// ── isStepperCommand — Connection Management ───────────────────────────────

describe('isStepperCommand — Connection Management', () => {
  it('returns true for "connect update" (multi-step)', () => {
    expect(isStepperCommand('connect update')).toBe(true)
  })

  it('returns false for "connect add" (single-step, no stepper)', () => {
    expect(isStepperCommand('connect add')).toBe(false)
  })

  it('returns false for "connect list" (single-step, no stepper)', () => {
    expect(isStepperCommand('connect list')).toBe(false)
  })

  it('returns false for "connect remove" (single-step, no stepper)', () => {
    expect(isStepperCommand('connect remove')).toBe(false)
  })

  it('returns false for "connect test" (single-step, no stepper)', () => {
    expect(isStepperCommand('connect test')).toBe(false)
  })
})

// ── getStepperConfig — connect update ─────────────────────────────────────

describe('getStepperConfig — connect update', () => {
  it('returns non-null config for "connect update"', () => {
    expect(getStepperConfig('connect update', 'form-1')).not.toBeNull()
  })

  it('returns null for "connect add"', () => {
    expect(getStepperConfig('connect add', 'form-1')).toBeNull()
  })

  it('returns null for "connect list"', () => {
    expect(getStepperConfig('connect list', 'form-1')).toBeNull()
  })

  it('forwards formId correctly into returned config', () => {
    const config = getStepperConfig('connect update', 'my-form-id')
    expect(config?.formId).toBe('my-form-id')
  })

  it('sets command to "connect update" in returned config', () => {
    const config = getStepperConfig('connect update', 'form-1')
    expect(config?.command).toBe('connect update')
  })

  it('returns a config with exactly 2 steps', () => {
    const config = getStepperConfig('connect update', 'form-1')
    expect(config?.steps).toHaveLength(2)
  })

  it('step 1 has id "select_connection"', () => {
    const [step1] = getStepperConfig('connect update', 'form-1')!.steps
    expect(step1!.id).toBe('select_connection')
  })

  it('step 2 has id "update_details"', () => {
    const [, step2] = getStepperConfig('connect update', 'form-1')!.steps
    expect(step2!.id).toBe('update_details')
  })

  it('step 1 has a validate function', () => {
    const [step1] = getStepperConfig('connect update', 'form-1')!.steps
    expect(typeof step1!.validate).toBe('function')
  })

  it('step 2 has a validate function', () => {
    const [, step2] = getStepperConfig('connect update', 'form-1')!.steps
    expect(typeof step2!.validate).toBe('function')
  })
})

// ── step 1 validate — connect update ──────────────────────────────────────

describe('getStepperConfig connect update — step 1 validate', () => {
  function getStep1Validate() {
    const [step1] = getStepperConfig('connect update', 'form-1')!.steps
    return step1!.validate!
  }

  it('returns false when connection_name is absent', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({}, steps)).toBe(false)
  })

  it('returns false when connection_name is empty string', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({ connection_name: '' }, steps)).toBe(false)
  })

  it('returns true when connection_name is a non-empty string', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(true)
  })

  it('returns true when connection_name is an array with exactly one item', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({ connection_name: ['my-conn'] }, steps)).toBe(true)
  })

  it('returns false when connection_name is an array with more than one item', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({ connection_name: ['conn-a', 'conn-b'] }, steps)).toBe(false)
  })

  it('returns false when connection_name is an empty array', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    expect(validate({ connection_name: [] }, steps)).toBe(false)
  })

  it('returns false when step has field-level errors', () => {
    const validate = getStep1Validate()
    const { steps } = getStepperConfig('connect update', 'form-1')!
    const [step1] = steps
    step1!.errors = { connection_name: 'Required' }
    expect(validate({ connection_name: 'my-conn' }, steps)).toBe(false)
  })
})

// ── step 2 validate — connect update ──────────────────────────────────────

describe('getStepperConfig connect update — step 2 validate', () => {
  function getStep2Context() {
    const config = getStepperConfig('connect update', 'form-1')!
    const [, step2] = config.steps
    return { validate: step2!.validate!, steps: config.steps }
  }

  it('returns true when name, host, port are present and no errors', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ name: 'my-conn', host: 'localhost', port: 27017 }, steps)).toBe(true)
  })

  it('returns false when name is missing', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ host: 'localhost', port: 27017 }, steps)).toBe(false)
  })

  it('returns false when host is missing', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ name: 'my-conn', port: 27017 }, steps)).toBe(false)
  })

  it('returns false when port is missing', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ name: 'my-conn', host: 'localhost' }, steps)).toBe(false)
  })

  it('returns false when username is set but password is missing', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ name: 'my-conn', host: 'localhost', port: 27017, username: 'admin' }, steps)).toBe(false)
  })

  it('returns true when both username and password are set', () => {
    const { validate, steps } = getStep2Context()
    expect(validate({ name: 'my-conn', host: 'localhost', port: 27017, username: 'admin', password: 'secret' }, steps)).toBe(true)
  })

  it('returns false when step 2 has field-level errors', () => {
    const { validate, steps } = getStep2Context()
    const [, step2] = steps
    step2!.errors = { host: 'Required' }
    expect(validate({ name: 'my-conn', host: 'localhost', port: 27017 }, steps)).toBe(false)
  })
})
