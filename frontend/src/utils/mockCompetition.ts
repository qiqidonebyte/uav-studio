import type { StudentAssignmentView } from '../types/teacher'

export interface MockCompetitionMeta {
  id: string
  title: string
  sequence: number
  total_cases: number
  total_duration_minutes: number
  case_recommended_minutes: number
}

export interface MockCompetitionGroup extends MockCompetitionMeta {
  class_name: string
  assignments: StudentAssignmentView[]
  completed_count: number
  elapsed_seconds: number
  average_score: number | null
  next_assignment_id: number | null
}

export function mockCompetitionMeta(requirements: Record<string, unknown>): MockCompetitionMeta | null {
  const raw = requirements.mock_competition
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  const value = raw as Record<string, unknown>
  const id = typeof value.id === 'string' ? value.id.trim() : ''
  const title = typeof value.title === 'string' ? value.title.trim() : ''
  const sequence = Number(value.sequence)
  const totalCases = Number(value.total_cases)
  const totalDuration = Number(value.total_duration_minutes)
  const recommended = Number(value.case_recommended_minutes)
  if (!id || !title || !Number.isInteger(sequence) || sequence < 1 || !Number.isInteger(totalCases) || totalCases < 2) return null
  if (!Number.isFinite(totalDuration) || totalDuration < 1 || !Number.isFinite(recommended) || recommended < 1) return null
  return {
    id,
    title,
    sequence,
    total_cases: totalCases,
    total_duration_minutes: totalDuration,
    case_recommended_minutes: recommended,
  }
}

export function groupMockCompetitions(assignments: StudentAssignmentView[]): MockCompetitionGroup[] {
  const groups = new Map<string, { meta: MockCompetitionMeta; assignments: StudentAssignmentView[] }>()
  for (const assignment of assignments) {
    const meta = mockCompetitionMeta(assignment.requirements)
    if (!meta) continue
    const group = groups.get(meta.id) ?? { meta, assignments: [] }
    group.assignments.push(assignment)
    groups.set(meta.id, group)
  }

  return [...groups.values()].map(({ meta, assignments: items }) => {
    const ordered = [...items].sort((left, right) => {
      const leftOrder = mockCompetitionMeta(left.requirements)?.sequence ?? 0
      const rightOrder = mockCompetitionMeta(right.requirements)?.sequence ?? 0
      return leftOrder - rightOrder
    })
    const completed = ordered.filter(item => item.run_status === 'completed')
    const next = ordered.find(item => item.run_status !== 'completed')
    const scores = completed.flatMap(item => item.score === null ? [] : [item.score])
    return {
      ...meta,
      class_name: ordered[0]?.class_name ?? '',
      assignments: ordered,
      completed_count: completed.length,
      elapsed_seconds: ordered.reduce((sum, item) => sum + Math.max(0, item.elapsed_seconds || 0), 0),
      average_score: scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : null,
      next_assignment_id: next?.id ?? null,
    }
  }).sort((left, right) => left.title.localeCompare(right.title, 'zh-CN'))
}

export function canStartMockCompetitionAssignment(group: MockCompetitionGroup, assignment: StudentAssignmentView): boolean {
  return assignment.run_status === 'completed' || group.next_assignment_id === assignment.id
}
