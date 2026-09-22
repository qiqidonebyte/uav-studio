import type { RouteLocationRaw } from 'vue-router'

export interface TrainingContext {
  run: string
  scenario?: string
  assignment?: string
}

export const TRAINING_CONTEXT_KEY = 'uav-training-context:v1'

function first(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] ?? '').trim()
  return String(value ?? '').trim()
}

function positiveInteger(value: unknown): string | undefined {
  const text = first(value)
  const number = Number(text)
  return Number.isInteger(number) && number > 0 ? String(number) : undefined
}

export function trainingContextFromQuery(query: Record<string, unknown>): TrainingContext | null {
  const run = positiveInteger(query.run)
  if (!run) return null
  const scenario = first(query.scenario)
  const assignment = positiveInteger(query.assignment)
  return {
    run,
    ...(scenario ? { scenario } : {}),
    ...(assignment ? { assignment } : {}),
  }
}

function browserStorage(): Storage | null {
  try { return globalThis.sessionStorage ?? null } catch { return null }
}

export function saveTrainingContext(context: TrainingContext, storage: Storage | null = browserStorage()): void {
  try { storage?.setItem(TRAINING_CONTEXT_KEY, JSON.stringify(context)) } catch { /* optional browser storage */ }
}

export function loadTrainingContext(storage: Storage | null = browserStorage()): TrainingContext | null {
  try {
    const raw = storage?.getItem(TRAINING_CONTEXT_KEY)
    if (!raw) return null
    return trainingContextFromQuery(JSON.parse(raw) as Record<string, unknown>)
  } catch { return null }
}

export function clearTrainingContext(storage: Storage | null = browserStorage()): void {
  try { storage?.removeItem(TRAINING_CONTEXT_KEY) } catch { /* optional browser storage */ }
}

export function activeTrainingContext(
  query: Record<string, unknown>,
  storage: Storage | null = browserStorage(),
): TrainingContext | null {
  const routeContext = trainingContextFromQuery(query)
  if (!routeContext) return loadTrainingContext(storage)
  const saved = loadTrainingContext(storage)
  const merged = saved?.run === routeContext.run ? { ...saved, ...routeContext } : routeContext
  saveTrainingContext(merged, storage)
  return merged
}

export function activeTrainingQuery(
  query: Record<string, unknown>,
  storage: Storage | null = browserStorage(),
): Record<string, string> {
  return { ...(activeTrainingContext(query, storage) ?? {}) }
}

export function trainingAwareTarget(
  path: string,
  query: Record<string, unknown>,
  storage: Storage | null = browserStorage(),
): RouteLocationRaw {
  const context = activeTrainingQuery(query, storage)
  return Object.keys(context).length ? { path, query: context } : path
}
