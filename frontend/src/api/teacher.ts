import { api } from './client'
import type {
  AdminUserView,
  AssignmentView,
  ClassroomView,
  EnrollmentView,
  GradebookView,
  ClassAnalytics,
  StudentAssignmentView,
  StudentSummary,
  TeacherOverview,
  TrainingEventView,
  TrainingRunDetail,
  TrainingRunView,
} from '../types/teacher'

export const teacherApi = {
  async overview(): Promise<TeacherOverview> {
    return (await api.get<TeacherOverview>('/teacher/overview')).data
  },
  async classes(): Promise<ClassroomView[]> {
    return (await api.get<ClassroomView[]>('/teacher/classes')).data
  },
  async createClass(payload: { name: string; academic_year?: string }): Promise<ClassroomView> {
    return (await api.post<ClassroomView>('/teacher/classes', payload)).data
  },
  async assignments(classId?: number): Promise<AssignmentView[]> {
    return (await api.get<AssignmentView[]>('/teacher/assignments', { params: classId ? { class_id: classId } : undefined })).data
  },
  async createAssignment(payload: {
    class_id: number
    title: string
    scenario_id: string
    description?: string
    start_at?: string | null
    due_at?: string | null
    requirements?: Record<string, unknown>
    score_weights?: Record<string, number>
  }): Promise<AssignmentView> {
    return (await api.post<AssignmentView>('/teacher/assignments', payload)).data
  },
  async runs(params?: { assignment_id?: number; class_id?: number; status?: string }): Promise<TrainingRunView[]> {
    return (await api.get<TrainingRunView[]>('/teacher/runs', { params })).data
  },
  async runDetail(runId: number): Promise<TrainingRunDetail> {
    return (await api.get<TrainingRunDetail>(`/teacher/runs/${runId}`)).data
  },
  async students(classId?: number): Promise<StudentSummary[]> {
    return (await api.get<StudentSummary[]>('/teacher/students', { params: classId ? { class_id: classId } : undefined })).data
  },
  async gradebook(classId: number): Promise<GradebookView> {
    return (await api.get<GradebookView>('/teacher/gradebook', { params: { class_id: classId } })).data
  },
  async analytics(classId: number): Promise<ClassAnalytics> {
    return (await api.get<ClassAnalytics>('/teacher/analytics', { params: { class_id: classId } })).data
  },
  async exportGradebook(classId: number): Promise<Blob> {
    return (await api.get('/teacher/gradebook/export.csv', { params: { class_id: classId }, responseType: 'blob' })).data as Blob
  },
  async adminUsers(): Promise<AdminUserView[]> {
    return (await api.get<AdminUserView[]>('/admin/users')).data
  },
  async updateRole(userId: number, role: 'student' | 'teacher'): Promise<AdminUserView> {
    return (await api.patch<AdminUserView>(`/admin/users/${userId}/role`, { role })).data
  },
}

export const studentTrainingApi = {
  async classes(): Promise<EnrollmentView[]> {
    return (await api.get<EnrollmentView[]>('/training/classes')).data
  },
  async joinClass(inviteCode: string): Promise<EnrollmentView> {
    return (await api.post<EnrollmentView>('/training/classes/join', { invite_code: inviteCode })).data
  },
  async assignments(): Promise<StudentAssignmentView[]> {
    return (await api.get<StudentAssignmentView[]>('/training/assignments')).data
  },
  async startAssignment(assignmentId: number, aircraftId?: number | null): Promise<TrainingRunView> {
    return (await api.post<TrainingRunView>(`/training/assignments/${assignmentId}/start`, {
      aircraft_id: aircraftId ?? null,
    })).data
  },
  async runDetail(runId: number): Promise<TrainingRunDetail> {
    return (await api.get<TrainingRunDetail>(`/training/runs/${runId}`)).data
  },
  async appendEvent(runId: number, payload: {
    event_type?: string
    title: string
    detail?: string
    event_key?: string
    payload?: Record<string, unknown>
  }): Promise<TrainingEventView> {
    return (await api.post<TrainingEventView>(`/training/runs/${runId}/events`, payload)).data
  },
  async progressRun(runId: number, payload: {
    passed?: boolean
    score: number
    elapsed_seconds: number
    hints_used: number
    wrong_operations: number
    prearm_passed: boolean
    flight_validation_passed?: boolean
    result: Record<string, unknown>
  }): Promise<TrainingRunView> {
    return (await api.post<TrainingRunView>(`/training/runs/${runId}/progress`, payload)).data
  },
  async submitRun(runId: number, payload: {
    passed: boolean
    score: number
    elapsed_seconds: number
    hints_used: number
    wrong_operations: number
    prearm_passed: boolean
    flight_validation_passed?: boolean
    result: Record<string, unknown>
  }): Promise<TrainingRunView> {
    return (await api.post<TrainingRunView>(`/training/runs/${runId}/submit`, payload)).data
  },
  async flightValidation(runId: number, passed = true, detail = ''): Promise<TrainingRunView> {
    const result = (await api.post<TrainingRunView>(`/training/runs/${runId}/flight-validation`, { passed, detail })).data
    if (result.status === 'completed') {
      try { await api.post(`/training/runs/${runId}/px4/release`) } catch { /* backend also releases completed runs */ }
    }
    return result
  },
}
