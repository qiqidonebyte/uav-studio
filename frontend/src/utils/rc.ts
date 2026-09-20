export type RcRole = 'roll' | 'pitch' | 'throttle' | 'yaw'

export interface RcChannelCalibration {
  min: number
  trim: number
  max: number
  reverse: 1 | -1
  deadzone: number
}

export interface RcDraft {
  mapping: Record<RcRole, number>
  channels: Record<number, RcChannelCalibration>
}

export interface RcIssue {
  code: string
  level: 'warn' | 'error'
  title: string
  detail: string
}

export const rcRoles: RcRole[] = ['roll', 'pitch', 'throttle', 'yaw']

export const rcRoleLabels: Record<RcRole, string> = {
  roll: 'Roll 横滚',
  pitch: 'Pitch 俯仰',
  throttle: 'Throttle 油门',
  yaw: 'Yaw 偏航',
}

export const rcMapParams: Record<RcRole, string> = {
  roll: 'RC_MAP_ROLL',
  pitch: 'RC_MAP_PITCH',
  throttle: 'RC_MAP_THROTTLE',
  yaw: 'RC_MAP_YAW',
}

export function defaultRcDraft(channelCount = 8): RcDraft {
  const channels: Record<number, RcChannelCalibration> = {
    0: { min: 1000, trim: 1500, max: 2000, reverse: 1, deadzone: 10 },
  }
  for (let channel = 1; channel <= channelCount; channel += 1) {
    channels[channel] = {
      min: 1000,
      trim: channel === 3 ? 1000 : 1500,
      max: 2000,
      reverse: 1,
      deadzone: 10,
    }
  }
  return {
    mapping: { roll: 1, pitch: 2, throttle: 3, yaw: 4 },
    channels,
  }
}

export function cloneRcDraft(value: RcDraft): RcDraft {
  return {
    mapping: { ...value.mapping },
    channels: Object.fromEntries(
      Object.entries(value.channels).map(([channel, calibration]) => [
        Number(channel),
        { ...calibration },
      ]),
    ),
  }
}

export function calibrationParamNames(channel: number): string[] {
  return [
    `RC${channel}_MIN`,
    `RC${channel}_TRIM`,
    `RC${channel}_MAX`,
    `RC${channel}_REV`,
  ]
}

export function flattenRcDraft(value: RcDraft): Record<string, number> {
  const result: Record<string, number> = {}
  for (const role of rcRoles) result[rcMapParams[role]] = Number(value.mapping[role])
  const mappedChannels = new Set(rcRoles.map(role => Number(value.mapping[role])).filter(channel => channel >= 1 && channel <= 18))
  for (const channel of mappedChannels) {
    const calibration = value.channels[channel]
    if (!calibration) continue
    result[`RC${channel}_MIN`] = Number(calibration.min)
    result[`RC${channel}_TRIM`] = Number(calibration.trim)
    result[`RC${channel}_MAX`] = Number(calibration.max)
    result[`RC${channel}_REV`] = Number(calibration.reverse)
  }
  return result
}

export function normalizeRcInput(
  pwm: number | null | undefined,
  calibration: RcChannelCalibration,
  throttle = false,
): number {
  if (typeof pwm !== 'number' || !Number.isFinite(pwm)) return 0
  const min = Number(calibration.min)
  const max = Number(calibration.max)
  const trim = Number(calibration.trim)
  const deadzone = Math.max(0, Number(calibration.deadzone) || 0)
  const reverse = Number(calibration.reverse) < 0 ? -1 : 1
  if (!(max > min)) return 0

  if (throttle) {
    const value = Math.max(0, Math.min(1, (pwm - min) / (max - min)))
    return reverse < 0 ? 1 - value : value
  }

  if (Math.abs(pwm - trim) <= deadzone) return 0
  const denominator = pwm >= trim ? max - trim : trim - min
  if (denominator <= 0) return 0
  return Math.max(-1, Math.min(1, ((pwm - trim) / denominator) * reverse))
}

export function validateRcDraft(value: RcDraft): RcIssue[] {
  const issues: RcIssue[] = []
  const push = (code: string, level: RcIssue['level'], title: string, detail: string) =>
    issues.push({ code, level, title, detail })

  const mapped = rcRoles.map(role => Number(value.mapping[role]))
  if (mapped.some(channel => !Number.isInteger(channel) || channel < 1 || channel > 18)) {
    push('MAP_RANGE', 'error', '主通道映射超出范围', 'Roll/Pitch/Throttle/Yaw 必须映射到 RC 1-18 的有效通道。')
  }
  if (new Set(mapped).size !== mapped.length) {
    push('MAP_DUPLICATE', 'error', '主控制通道重复', 'Roll、Pitch、Throttle 与 Yaw 不应映射到同一个 RC 通道。')
  }

  const mappedChannels = new Set(mapped.filter(channel => channel >= 1 && channel <= 18))
  for (const channel of mappedChannels) {
    const c = value.channels[channel]
    if (!c) {
      push(`CH${channel}_MISSING`, 'error', `CH${channel} 缺少校准参数`, '请重新读取 PX4 参数或恢复教学默认值。')
      continue
    }
    if (!(c.min >= 800 && c.min <= 1500 && c.max >= 1500 && c.max <= 2200 && c.max - c.min >= 400)) {
      push(`CH${channel}_RANGE`, 'error', `CH${channel} 行程范围异常`, '建议检查接收机输入，Min/Max 应形成足够的有效行程。')
    }
    if (!(c.trim >= c.min && c.trim <= c.max)) {
      push(`CH${channel}_TRIM`, 'error', `CH${channel} 中位超出行程`, 'Trim 必须位于 Min 与 Max 之间。')
    }
    if (![1, -1].includes(Number(c.reverse))) {
      push(`CH${channel}_REV`, 'error', `CH${channel} 方向参数无效`, 'RCx_REV 只能使用 1（正常）或 -1（反向）。')
    }
    if (c.deadzone < 0 || c.deadzone > 100) {
      push(`CH${channel}_DZ`, 'error', `CH${channel} 死区超出范围`, 'Deadzone 建议保持在 0-100 μs。')
    }
  }

  const throttleChannel = Number(value.mapping.throttle)
  const throttle = value.channels[throttleChannel]
  if (throttle && Math.abs(throttle.trim - throttle.min) > 35) {
    push('THROTTLE_TRIM', 'warn', '油门 Trim 未接近最小值', 'PX4 遥控校准中油门通道 Trim 通常应与 Min 保持一致或非常接近。')
  }

  for (const role of ['roll', 'pitch', 'yaw'] as RcRole[]) {
    const channel = Number(value.mapping[role])
    const c = value.channels[channel]
    if (!c) continue
    const center = (c.min + c.max) / 2
    if (Math.abs(c.trim - center) > 120) {
      push(`${role.toUpperCase()}_CENTER`, 'warn', `${rcRoleLabels[role]} 中位偏离`, '中位距离行程中心较远，请确认摇杆回中和微调设置。')
    }
  }

  return issues
}

export function calculateRcScore(value: RcDraft, hasLiveInput: boolean, captureComplete: boolean): number {
  const issues = validateRcDraft(value)
  let score = 100
  score -= issues.filter(issue => issue.level === 'error').length * 18
  score -= issues.filter(issue => issue.level === 'warn').length * 6
  if (!hasLiveInput) score -= 8
  if (!captureComplete) score -= 5
  return Math.max(0, Math.min(100, score))
}
