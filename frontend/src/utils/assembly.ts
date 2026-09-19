import type {
  AircraftDefinition,
  AssemblyIssue,
  AssemblyValidationResult,
  Component,
  ComponentType,
} from '../types/aircraft'

export type AssemblySlot = ComponentType
export type AssemblyStepId =
  | 'frame'
  | 'power'
  | 'supply'
  | 'avionics'
  | 'payload'
  | 'propeller'
  | 'check'
export type StepStatus = 'pending' | 'done' | 'warning' | 'error'

export interface AssemblyStep {
  id: AssemblyStepId
  title: string
  detail: string
  slots: AssemblySlot[]
  requiredSlots: AssemblySlot[]
}

export const SLOT_FIELDS: Record<AssemblySlot, keyof AircraftDefinition> = {
  frame: 'frame_id',
  motor: 'motor_id',
  esc: 'esc_id',
  propeller: 'propeller_id',
  battery: 'battery_id',
  power_module: 'power_module_id',
  flight_controller: 'flight_controller_id',
  gnss: 'gnss_id',
  payload: 'payload_id',
}

export const SLOT_LABELS: Record<AssemblySlot, string> = {
  frame: '机架',
  motor: '电机',
  esc: '电调',
  propeller: '螺旋桨',
  battery: '电池',
  power_module: '电源模块',
  flight_controller: '飞控',
  gnss: 'GNSS/罗盘',
  payload: '任务载荷',
}

export const ASSEMBLY_STEPS: AssemblyStep[] = [
  {
    id: 'frame',
    title: '机架',
    detail: '建立四旋翼安装槽位',
    slots: ['frame'],
    requiredSlots: ['frame'],
  },
  {
    id: 'power',
    title: '动力系统',
    detail: '安装 4 组电机与电调',
    slots: ['motor', 'esc'],
    requiredSlots: ['motor', 'esc'],
  },
  {
    id: 'supply',
    title: '供电系统',
    detail: '安装电源模块与电池',
    slots: ['power_module', 'battery'],
    requiredSlots: ['power_module', 'battery'],
  },
  {
    id: 'avionics',
    title: '飞控与导航',
    detail: '安装飞控及可选 GNSS/罗盘',
    slots: ['flight_controller', 'gnss'],
    requiredSlots: ['flight_controller'],
  },
  {
    id: 'payload',
    title: '任务载荷',
    detail: '安装前部或底部中心载荷',
    slots: ['payload'],
    requiredSlots: [],
  },
  {
    id: 'propeller',
    title: '螺旋桨',
    detail: '安装匹配顺时针/逆时针的桨组',
    slots: ['propeller'],
    requiredSlots: ['propeller'],
  },
  {
    id: 'check',
    title: '装配检查',
    detail: '运行后端兼容性与安全检查',
    slots: [],
    requiredSlots: [],
  },
]

const STEP_ISSUE_CODES: Partial<Record<AssemblyStepId, string[]>> = {
  frame: ['CG_OFFSET_WARNING'],
  power: [
    'INSUFFICIENT_TOTAL_THRUST',
    'LOW_THRUST_WEIGHT_RATIO',
    'ESC_CURRENT_LIMIT_EXCEEDED',
    'MOTOR_PERFORMANCE_CURVE_MISSING',
  ],
  supply: [
    'VOLTAGE_INCOMPATIBLE',
    'BATTERY_DISCHARGE_LIMIT_EXCEEDED',
    'POWER_MODULE_CURRENT_LIMIT_EXCEEDED',
    'SHORT_ESTIMATED_ENDURANCE',
  ],
  payload: ['HIGH_PAYLOAD_MASS_FRACTION'],
  propeller: ['PROPELLER_DIRECTION_MISMATCH'],
}

const SCENE_PART_PREFIXES: Array<[string, AssemblySlot]> = [
  ['frame', 'frame'],
  ['battery', 'battery'],
  ['power_module', 'power_module'],
  ['flight_controller', 'flight_controller'],
  ['gnss', 'gnss'],
  ['payload', 'payload'],
  ['motor_', 'motor'],
  ['esc_', 'esc'],
  ['propeller_', 'propeller'],
  ['rotor_', 'propeller'],
]

function issuesForStep(
  stepId: AssemblyStepId,
  validation: AssemblyValidationResult,
): AssemblyIssue[] {
  const codes = STEP_ISSUE_CODES[stepId]
  if (!codes) return []
  return [...validation.blocking_errors, ...validation.warnings].filter(issue =>
    codes.includes(issue.code),
  )
}

export function isSlotInstalled(
  aircraft: AircraftDefinition,
  slot: AssemblySlot,
): boolean {
  const value = aircraft[SLOT_FIELDS[slot]]
  return typeof value === 'number' && value > 0
}

export function getStepStatus(
  step: AssemblyStep,
  aircraft: AircraftDefinition,
  validation: AssemblyValidationResult,
): StepStatus {
  if (step.id === 'check') {
    if (validation.blocking_errors.length > 0) return 'error'
    if (validation.warnings.length > 0) return 'warning'
    return 'done'
  }

  if (step.requiredSlots.some(slot => !isSlotInstalled(aircraft, slot))) {
    return 'pending'
  }

  const issues = issuesForStep(step.id, validation)
  if (issues.some(issue => issue.severity === 'error')) return 'error'
  if (issues.some(issue => issue.severity === 'warning')) return 'warning'
  return 'done'
}

export function assemblySlotFromScenePart(part: string): AssemblySlot | null {
  for (const [prefix, slot] of SCENE_PART_PREFIXES) {
    if (part === prefix || part.startsWith(prefix)) return slot
  }
  return null
}

export function slotComponents(
  components: Component[],
  slot: AssemblySlot,
): Component[] {
  return components.filter(component => component.type === slot)
}

export function componentFitsSlot(
  component: Component,
  slot: AssemblySlot,
): boolean {
  return component.type === slot
}

export function installedComponentId(
  aircraft: AircraftDefinition,
  slot: AssemblySlot,
): number | null {
  const value = aircraft[SLOT_FIELDS[slot]]
  return typeof value === 'number' ? value : null
}
