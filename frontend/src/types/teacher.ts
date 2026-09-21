export interface ClassroomView {
  id: number
  name: string
  academic_year: string
  teacher_user_id: number
  teacher_name: string
  invite_code: string
  student_count: number
  assignment_count: number
  created_at: string
}

export interface EnrollmentView {
  class_id: number
  class_name: string
  teacher_name: string
  joined_at: string
}

export interface AssignmentView {
  id: number
  class_id: number
  class_name: string
  title: string
  scenario_id: string
  scenario_title: string
  description: string
  start_at: string | null
  due_at: string | null
  status: string
  assigned_count: number
  started_count: number
  completed_count: number
  average_score: number | null
  created_at: string
}

export interface StudentAssignmentView {
  id: number
  class_id: number
  class_name: string
  teacher_name: string
  title: string
  scenario_id: string
  scenario_title: string
  description: string
  difficulty: number
  recommended_minutes: number
  due_at: string | null
  assignment_status: string
  run_id: number | null
  run_status: 'not_started' | 'in_progress' | 'completed' | string
  score: number | null
  elapsed_seconds: number
}

export interface TrainingRunView {
  id: number
  assignment_id: number
  assignment_title: string
  class_id: number
  class_name: string
  student_user_id: number
  student_name: string
  scenario_id: string
  scenario_title: string
  aircraft_id: number | null
  started_at: string
  ended_at: string | null
  status: string
  score: number | null
  elapsed_seconds: number
  hints_used: number
  wrong_operations: number
  first_pass: boolean | null
  prearm_passed: boolean
  flight_validation_passed: boolean
  result: Record<string, unknown>
}

export interface TrainingEventView {
  id: number
  created_at: string
  event_type: string
  title: string
  detail: string
  payload: Record<string, unknown>
}

export interface TrainingRunDetail {
  run: TrainingRunView
  events: TrainingEventView[]
}

export interface TeacherOverview {
  class_count: number
  student_count: number
  assignment_count: number
  active_assignment_count: number
  completed_run_count: number
  average_score: number | null
  recent_assignments: AssignmentView[]
}

export interface StudentSummary {
  user_id: number
  display_name: string
  username: string
  class_id: number
  class_name: string
  completed_runs: number
  average_score: number | null
  average_elapsed_seconds: number | null
  total_hints: number
  total_wrong_operations: number
  first_pass_rate: number | null
}

export interface AdminUserView {
  id: number
  username: string
  display_name: string
  role: string
  is_active: boolean
  created_at: string
}
