export type SafetyParamKey =
  | 'COM_RC_LOSS_T'
  | 'NAV_RCL_ACT'
  | 'COM_FAIL_ACT_T'
  | 'COM_DL_LOSS_T'
  | 'NAV_DLL_ACT'
  | 'BAT_LOW_THR'
  | 'BAT_CRIT_THR'
  | 'BAT_EMERGEN_THR'
  | 'COM_LOW_BAT_ACT'
  | 'COM_ARM_BAT_MIN'
  | 'RTL_RETURN_ALT'
  | 'GF_MAX_HOR_DIST'
  | 'GF_MAX_VER_DIST'
  | 'GF_ACTION'
  | 'COM_ARMABLE'
  | 'COM_ARM_WO_GPS'
  | 'COM_DISARM_PRFLT'
  | 'COM_DISARM_LAND'

export type SafetyDraft = Record<SafetyParamKey, number>
export type SafetyIssueLevel = 'warn' | 'error'

export interface SafetyIssue {
  code: string
  level: SafetyIssueLevel
  title: string
  detail: string
}

export const safetyParamKeys: SafetyParamKey[] = [
  'COM_RC_LOSS_T', 'NAV_RCL_ACT', 'COM_FAIL_ACT_T', 'COM_DL_LOSS_T', 'NAV_DLL_ACT',
  'BAT_LOW_THR', 'BAT_CRIT_THR', 'BAT_EMERGEN_THR', 'COM_LOW_BAT_ACT', 'COM_ARM_BAT_MIN',
  'RTL_RETURN_ALT', 'GF_MAX_HOR_DIST', 'GF_MAX_VER_DIST', 'GF_ACTION',
  'COM_ARMABLE', 'COM_ARM_WO_GPS', 'COM_DISARM_PRFLT', 'COM_DISARM_LAND',
]

export const recommendedSafetyProfile: SafetyDraft = {
  COM_RC_LOSS_T: 0.5,
  NAV_RCL_ACT: 2,
  COM_FAIL_ACT_T: 5,
  COM_DL_LOSS_T: 10,
  NAV_DLL_ACT: 2,
  BAT_LOW_THR: 0.15,
  BAT_CRIT_THR: 0.10,
  BAT_EMERGEN_THR: 0.05,
  COM_LOW_BAT_ACT: 3,
  COM_ARM_BAT_MIN: 0.15,
  RTL_RETURN_ALT: 15,
  GF_MAX_HOR_DIST: 50,
  GF_MAX_VER_DIST: 30,
  GF_ACTION: 2,
  COM_ARMABLE: 1,
  COM_ARM_WO_GPS: 0,
  COM_DISARM_PRFLT: 10,
  COM_DISARM_LAND: 2,
}

export const unsafeDemoSafetyProfile: SafetyDraft = {
  ...recommendedSafetyProfile,
  COM_RC_LOSS_T: 8,
  NAV_RCL_ACT: 0,
  NAV_DLL_ACT: 0,
  BAT_LOW_THR: 0.08,
  BAT_CRIT_THR: 0.10,
  BAT_EMERGEN_THR: 0.05,
  COM_LOW_BAT_ACT: 0,
  COM_ARM_BAT_MIN: 0,
  RTL_RETURN_ALT: 45,
  GF_MAX_VER_DIST: 30,
  GF_ACTION: 0,
  COM_ARM_WO_GPS: 1,
}

export function validateSafetyDraft(v: SafetyDraft): SafetyIssue[] {
  const issues: SafetyIssue[] = []
  const push = (code: string, level: SafetyIssueLevel, title: string, detail: string) =>
    issues.push({ code, level, title, detail })

  if (!(Number(v.BAT_LOW_THR) > Number(v.BAT_CRIT_THR) && Number(v.BAT_CRIT_THR) > Number(v.BAT_EMERGEN_THR))) {
    push('BATTERY_ORDER', 'error', '电量阈值顺序错误', '应满足 BAT_LOW_THR > BAT_CRIT_THR > BAT_EMERGEN_THR，否则电量状态机无法形成合理的告警、返航和紧急阶段。')
  }
  if (Number(v.COM_ARM_BAT_MIN) > 0 && Number(v.COM_ARM_BAT_MIN) < Number(v.BAT_CRIT_THR)) {
    push('ARM_BAT_LOW', 'warn', '最低解锁电量偏低', 'COM_ARM_BAT_MIN 低于 Critical 阈值，可能允许飞机在已经接近严重低电量时解锁。')
  }
  if (Number(v.GF_MAX_VER_DIST) > 0 && Number(v.RTL_RETURN_ALT) >= Number(v.GF_MAX_VER_DIST)) {
    push('RTL_GEOFENCE', 'error', '返航高度与地理围栏冲突', 'RTL_RETURN_ALT 不应达到或超过垂直围栏高度，否则返航爬升可能与围栏策略发生冲突。')
  }
  if (Number(v.NAV_RCL_ACT) === 0) push('RC_DISABLED', 'warn', '遥控失联保护已禁用', '训练飞行建议至少设置 Hold、Return 或 Land。')
  if (Number(v.NAV_DLL_ACT) === 0) push('DLL_DISABLED', 'warn', '数据链路失联保护已禁用', '若课程依赖地面站或网页控制链路，建议配置链路丢失后的保护动作。')
  if (Number(v.COM_LOW_BAT_ACT) === 0) push('BAT_ONLY_WARN', 'warn', '低电量仅告警', 'Critical/Emergency 阶段没有自动返航或降落动作。')
  if (Number(v.GF_MAX_HOR_DIST) === 0 && Number(v.GF_MAX_VER_DIST) === 0) push('GF_DISABLED', 'warn', '地理围栏未启用', '水平与垂直限制均为 0；教学飞行验证建议使用有限边界。')
  if ((Number(v.GF_MAX_HOR_DIST) > 0 || Number(v.GF_MAX_VER_DIST) > 0) && Number(v.GF_ACTION) === 0) push('GF_NO_ACTION', 'warn', '围栏越界动作为空', '已设置围栏尺寸，但 GF_ACTION=None，越界不会触发保护动作。')
  if (Number(v.COM_ARM_WO_GPS) === 1) push('ARM_NO_GPS', 'warn', '允许无 GPS 解锁', '这可能适用于室内或特殊任务；当前教学飞行验证若依赖定位，建议要求有效 GPS/位置估计。')
  if (Number(v.COM_ARMABLE) === 0) push('NOT_ARMABLE', 'warn', '飞控被设置为禁止解锁', '适合维护状态，但会阻止后续起飞验证。')
  if (Number(v.COM_RC_LOSS_T) > 3) push('RC_TIMEOUT_LONG', 'warn', '遥控失联判定时间较长', '失联期间飞机可能继续使用最后的控制输入；教学训练建议保持较短超时。')

  const dangerous =
    [Number(v.NAV_RCL_ACT), Number(v.NAV_DLL_ACT)].some(value => value === 5 || value === 6)
    || Number(v.GF_ACTION) === 4
    || Number(v.COM_LOW_BAT_ACT) === 4
  if (dangerous) push('DANGEROUS_ACTION', 'error', '检测到高风险终止/空中上锁策略', '教学界面不建议使用 Terminate 或飞行中 Disarm。请改为 Hold、Return 或 Land 后再应用。')

  return issues
}

export function calculateSafetyScore(v: SafetyDraft, failsafeFaultActive = false): number {
  const issues = validateSafetyDraft(v)
  const errors = issues.filter(issue => issue.level === 'error').length
  const warnings = issues.filter(issue => issue.level === 'warn').length
  let value = 100 - errors * 18 - warnings * 6
  if (failsafeFaultActive) value -= 10
  return Math.max(0, Math.min(100, value))
}
