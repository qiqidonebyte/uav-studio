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
  requirements: Record<string, unknown>
  score_weights: Record<string, number>
  requires_flight_validation: boolean
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
  requirements: Record<string, unknown>
  score_weights: Record<string, number>
  requires_flight_validation: boolean
  run_stage: string
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
  stage: string
  case_score: number | null
  operation_score: number | null
  flight_score: number | null
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

export interface GradebookAssignment {
  id: number
  title: string
  scenario_id: string
  scenario_title: string
  requires_flight_validation: boolean
}

export interface GradebookCell {
  assignment_id: number
  run_id: number | null
  status: string
  stage: string
  score: number | null
  case_score: number | null
  operation_score: number | null
  flight_score: number | null
  elapsed_seconds: number
  hints_used: number
  wrong_operations: number
  first_pass: boolean | null
  prearm_passed: boolean
  flight_validation_passed: boolean
}

export interface GradebookStudent {
  user_id: number
  display_name: string
  username: string
  completed_count: number
  average_score: number | null
  cells: GradebookCell[]
}

export interface GradebookView {
  class_id: number
  class_name: string
  assignment_count: number
  student_count: number
  completion_rate: number
  class_average: number | null
  assignments: GradebookAssignment[]
  students: GradebookStudent[]
}

export interface ScenarioAnalytics {
  assignment_id: number
  title: string
  scenario_id: string
  assigned_count: number
  started_count: number
  completed_count: number
  completion_rate: number
  average_score: number | null
  first_pass_rate: number | null
}

export interface ClassAnalytics {
  class_id: number
  class_name: string
  student_count: number
  assignment_count: number
  total_expected_runs: number
  started_run_count: number
  completed_run_count: number
  completion_rate: number
  average_score: number | null
  first_pass_rate: number | null
  average_elapsed_seconds: number | null
  average_hints: number | null
  average_wrong_operations: number | null
  flight_validation_rate: number | null
  scenarios: ScenarioAnalytics[]
}
