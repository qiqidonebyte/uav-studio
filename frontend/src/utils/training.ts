export type TrainingCategory = 'sensors' | 'rc' | 'power' | 'safety' | 'integrated'
export type TrainingSection = 'sensors' | 'rc' | 'power' | 'safety' | 'preflight'
export type TrainingScenario = 'standard' | 'mapping' | 'compass' | 'failsafe'
export type TrainingConditionGroup = 'repair' | 'validation'

export interface TrainingCondition {
  key: string
  group: TrainingConditionGroup
}

export interface FaultTrainingCase {
  id: string
  title: string
  category: TrainingCategory
  difficulty: 1 | 2 | 3
  recommended_minutes: number
  icon: string
  fault_source: string
  legacy_scenario: TrainingScenario
  initial_section: TrainingSection
  target_sections: TrainingSection[]
  student_brief: {
    symptom: string
    task: string
  }
  injections: string[]
  success_conditions: TrainingCondition[]
  hints: string[]
}

export interface TrainingScoreInput {
  trainingCase: FaultTrainingCase
  conditionState: Record<string, boolean>
  visitedSections: string[]
  elapsedSeconds: number
  hintsUsed: number
  wrongOperations: number
}

export interface TrainingEvaluation {
  passed: boolean
  score: number
  diagnosisScore: number
  repairScore: number
  validationScore: number
  efficiencyScore: number
  penalty: number
  completedConditions: number
  totalConditions: number
  repairCompleted: number
  repairTotal: number
  validationCompleted: number
  validationTotal: number
}

export async function loadFaultTrainingCases(): Promise<FaultTrainingCase[]> {
  const base = String(import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
  const response = await fetch(`${base}training/scenarios/index.json`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`案例库加载失败：HTTP ${response.status}`)
  const value = await response.json()
  if (!Array.isArray(value)) throw new Error('案例库格式错误')
  return value as FaultTrainingCase[]
}

function fraction(done: number, total: number): number {
  return total <= 0 ? 1 : Math.max(0, Math.min(1, done / total))
}

export function scoreFaultTraining(input: TrainingScoreInput): TrainingEvaluation {
  const { trainingCase, conditionState } = input
  const repair = trainingCase.success_conditions.filter(item => item.group === 'repair')
  const validation = trainingCase.success_conditions.filter(item => item.group === 'validation')
  const repairCompleted = repair.filter(item => conditionState[item.key] === true).length
  const validationCompleted = validation.filter(item => conditionState[item.key] === true).length
  const completedConditions = repairCompleted + validationCompleted
  const totalConditions = repair.length + validation.length

  const visited = new Set(input.visitedSections)
  const targetVisited = trainingCase.target_sections.filter(section => visited.has(section)).length
  const diagnosisScore = Math.round(30 * fraction(targetVisited, trainingCase.target_sections.length))
  const repairScore = Math.round(35 * fraction(repairCompleted, repair.length))
  const validationScore = Math.round(25 * fraction(validationCompleted, validation.length))

  const recommendedSeconds = Math.max(60, trainingCase.recommended_minutes * 60)
  const ratio = Math.max(0, input.elapsedSeconds) / recommendedSeconds
  const efficiencyScore = ratio <= 1
    ? 10
    : ratio <= 1.5
      ? Math.max(5, Math.round(10 - (ratio - 1) * 10))
      : Math.max(0, Math.round(5 - (ratio - 1.5) * 5))

  const penalty = Math.min(30, Math.max(0, input.hintsUsed) * 8 + Math.max(0, input.wrongOperations) * 3)
  const raw = diagnosisScore + repairScore + validationScore + efficiencyScore - penalty
  const passed = totalConditions > 0 && completedConditions === totalConditions

  return {
    passed,
    score: Math.max(0, Math.min(100, Math.round(raw))),
    diagnosisScore,
    repairScore,
    validationScore,
    efficiencyScore,
    penalty,
    completedConditions,
    totalConditions,
    repairCompleted,
    repairTotal: repair.length,
    validationCompleted,
    validationTotal: validation.length,
  }
}

export function trainingDifficultyText(value: number): string {
  return '★'.repeat(Math.max(1, Math.min(3, Math.round(value))))
}

export function trainingCategoryText(category: TrainingCategory): string {
  return ({
    sensors: '飞控传感器',
    rc: '遥控系统',
    power: '动力系统',
    safety: '安全设置',
    integrated: '综合检修',
  } as const)[category]
}
