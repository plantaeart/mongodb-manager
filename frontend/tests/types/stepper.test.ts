import { describe, it, expect, vi } from 'vitest'
import { createStep, getAllStepData, isStepValid, canProceedFromStep } from '~/types/stepper'
import type { StepDefinition } from '~/types/stepper'

// ── Helpers ────────────────────────────────────────────────────────────────
function makeStep(overrides: Partial<StepDefinition> = {}): StepDefinition {
  return {
    id: 'test-step',
    config: { title: 'Test', description: 'A test step', disabled: false },
    data: {},
    errors: {},
    isLoading: false,
    ...overrides,
  }
}

// ── createStep ─────────────────────────────────────────────────────────────
describe('createStep', () => {
  it('creates a step with correct id, title and description', () => {
    const step = createStep('my-id', 'My Title', 'My Description')
    expect(step.id).toBe('my-id')
    expect(step.config.title).toBe('My Title')
    expect(step.config.description).toBe('My Description')
  })

  it('sets disabled to false by default', () => {
    const step = createStep('id', 'Title', 'Desc')
    expect(step.config.disabled).toBe(false)
  })

  it('sets icon when provided', () => {
    const step = createStep('id', 'Title', 'Desc', 'i-lucide-database')
    expect(step.config.icon).toBe('i-lucide-database')
  })

  it('initialises data, errors and isLoading to empty/false', () => {
    const step = createStep('id', 'Title', 'Desc')
    expect(step.data).toEqual({})
    expect(step.errors).toEqual({})
    expect(step.isLoading).toBe(false)
  })
})

// ── getAllStepData ──────────────────────────────────────────────────────────
describe('getAllStepData', () => {
  it('merges data from all steps into one object', () => {
    const steps: StepDefinition[] = [
      makeStep({ data: { name: 'my-db' } }),
      makeStep({ data: { host: 'localhost', port: 27017 } }),
    ]
    const result = getAllStepData(steps)
    expect(result).toEqual({ name: 'my-db', host: 'localhost', port: 27017 })
  })

  it('returns empty object for empty steps array', () => {
    expect(getAllStepData([])).toEqual({})
  })

  it('later step data overwrites earlier step data on key collision', () => {
    const steps: StepDefinition[] = [
      makeStep({ data: { host: 'localhost' } }),
      makeStep({ data: { host: 'remotehost' } }),
    ]
    const result = getAllStepData(steps)
    expect(result.host).toBe('remotehost')
  })
})

// ── isStepValid ────────────────────────────────────────────────────────────
describe('isStepValid', () => {
  it('returns true when there are no errors and no validate fn', () => {
    const step = makeStep({ errors: {} })
    expect(isStepValid(step, [step])).toBe(true)
  })

  it('returns false when there are field-level errors', () => {
    const step = makeStep({ errors: { host: 'Host is required' } })
    expect(isStepValid(step, [step])).toBe(false)
  })

  it('returns false when custom validate() returns false', () => {
    const step = makeStep({
      errors: {},
      validate: vi.fn().mockReturnValue(false),
    })
    expect(isStepValid(step, [step])).toBe(false)
  })

  it('returns true when custom validate() returns true and no errors', () => {
    const step = makeStep({
      errors: {},
      validate: vi.fn().mockReturnValue(true),
    })
    expect(isStepValid(step, [step])).toBe(true)
  })

  it('calls custom validate() with step data and all steps', () => {
    const validateFn = vi.fn().mockReturnValue(true)
    const step = makeStep({ data: { host: 'localhost' }, validate: validateFn })
    isStepValid(step, [step])
    expect(validateFn).toHaveBeenCalledWith({ host: 'localhost' }, [step])
  })

  it('returns false when custom validate() returns true but errors exist', () => {
    const step = makeStep({
      errors: { name: 'Required' },
      validate: vi.fn().mockReturnValue(true),
    })
    expect(isStepValid(step, [step])).toBe(false)
  })
})

// ── canProceedFromStep ─────────────────────────────────────────────────────
describe('canProceedFromStep', () => {
  it('returns true for a valid non-loading step', () => {
    const steps = [makeStep({ errors: {}, isLoading: false })]
    expect(canProceedFromStep(0, steps)).toBe(true)
  })

  it('returns false when step is loading', () => {
    const steps = [makeStep({ errors: {}, isLoading: true })]
    expect(canProceedFromStep(0, steps)).toBe(false)
  })

  it('returns false when step has errors', () => {
    const steps = [makeStep({ errors: { host: 'Required' }, isLoading: false })]
    expect(canProceedFromStep(0, steps)).toBe(false)
  })

  it('returns false for an out-of-bounds index', () => {
    const steps = [makeStep()]
    expect(canProceedFromStep(5, steps)).toBe(false)
  })

  it('returns false for negative index', () => {
    const steps = [makeStep()]
    expect(canProceedFromStep(-1, steps)).toBe(false)
  })
})
