import { describe, expect, it } from 'vitest'
import type { StudentAssignmentView } from '../src/types/teacher'
import { canStartMockCompetitionAssignment, groupMockCompetitions, mockCompetitionMeta } from '../src/utils/mockCompetition'

function assignment(id: number, sequence: number, runStatus: string, score: number | null, elapsed: number): StudentAssignmentView {
  return {
    id, class_id: 2, class_name: '无人机实训班', teacher_name: '教师', title: `环节${sequence}`,
    scenario_id: `F0${sequence}`, scenario_title: `故障案例${sequence}`, description: '', difficulty: 2,
    recommended_minutes: 20, due_at: null, assignment_status: 'active', run_id: null, run_status: runStatus,
    score, elapsed_seconds: elapsed, requirements: { mock_competition: {
      id: 'contest-a', title: '基础模拟赛', sequence, total_cases: 3, total_duration_minutes: 90,
      case_recommended_minutes: 20,
    } }, score_weights: {}, requires_flight_validation: false, run_stage: '',
  }
}

describe('mock competition grouping and progression', () => {
  it('groups and orders assignments, then summarizes completed progress', () => {
    const groups = groupMockCompetitions([
      assignment(3, 3, 'not_started', null, 0),
      assignment(1, 1, 'completed', 80, 600),
      assignment(2, 2, 'in_progress', null, 125),
    ])
    expect(groups).toHaveLength(1)
    expect(groups[0].assignments.map(item => item.id)).toEqual([1, 2, 3])
    expect(groups[0]).toMatchObject({ completed_count: 1, elapsed_seconds: 725, average_score: 80, next_assignment_id: 2 })
  })

  it('allows current and completed review, but locks later steps', () => {
    const first = assignment(1, 1, 'completed', 80, 600)
    const current = assignment(2, 2, 'in_progress', null, 20)
    const later = assignment(3, 3, 'not_started', null, 0)
    const [group] = groupMockCompetitions([first, current, later])
    expect(canStartMockCompetitionAssignment(group, first)).toBe(true)
    expect(canStartMockCompetitionAssignment(group, current)).toBe(true)
    expect(canStartMockCompetitionAssignment(group, later)).toBe(false)
  })

  it('ignores malformed competition metadata', () => {
    expect(mockCompetitionMeta({ mock_competition: { id: '', sequence: 0, total_cases: 1 } })).toBeNull()
    expect(groupMockCompetitions([{
      ...assignment(1, 1, 'not_started', null, 0), requirements: {},
    }])).toEqual([])
  })
})
