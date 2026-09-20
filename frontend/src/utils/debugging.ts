import type {
  DebugCheck,
  DebuggingBenchState,
  DebuggingContext,
  DebuggingEvaluation,
  DebugSeverity,
} from '../types/debugging'

const EXPECTED_MOTOR_DIRECTIONS = {
  M1: 'CCW',
  M2: 'CW',
  M3: 'CCW',
  M4: 'CW',
} as const

function check(
  key: string,
  group: DebugCheck['group'],
  title: string,
  severity: DebugSeverity,
  value: string,
  recommendation: string,
): DebugCheck {
  return { key, group, title, severity, value, recommendation }
}

function fmt(value: number | null, digits = 1): string {
  return value === null || !Number.isFinite(value) ? '—' : value.toFixed(digits)
}

function finiteNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export function defaultDebuggingBenchState(
  batteryNominalVoltageV = 22.2,
): DebuggingBenchState {
  return {
    scenarioKey: 'normal',
    imuCalibrated: true,
    compassCalibrated: true,
    gpsSatellites: 14,
    gpsHdop: 1.0,
    rcCalibrated: true,
    rcSignalPercent: 95,
    batteryVoltageV: batteryNominalVoltageV,
    lowBatteryPercent: 25,
    criticalBatteryPercent: 15,
    failsafeMode: 'RTH',
    rthAltitudeM: 30,
    motors: {
      M1: { responding: true, direction: 'CCW' },
      M2: { responding: true, direction: 'CW' },
      M3: { responding: true, direction: 'CCW' },
      M4: { responding: true, direction: 'CW' },
    },
    propellersSecured: true,
    wiringSecured: true,
    environmentClear: true,
  }
}

export function applyDebuggingScenario(
  key: string,
  base: DebuggingBenchState,
): DebuggingBenchState {
  const next: DebuggingBenchState = structuredClone(base)
  next.scenarioKey = key

  if (key === 'gps') {
    next.gpsSatellites = 5
    next.gpsHdop = 3.2
  } else if (key === 'motor') {
    next.motors.M2.direction = 'CCW'
    next.motors.M4.responding = false
  } else if (key === 'failsafe') {
    next.rcSignalPercent = 58
    next.failsafeMode = 'HOLD'
    next.rthAltitudeM = 10
  } else if (key === 'exam') {
    next.imuCalibrated = false
    next.gpsSatellites = 7
    next.gpsHdop = 2.4
    next.motors.M3.direction = 'CW'
    next.lowBatteryPercent = 14
    next.criticalBatteryPercent = 15
    next.wiringSecured = false
  }
  return next
}

export function evaluateDebugging(
  state: DebuggingBenchState,
  context: DebuggingContext,
): DebuggingEvaluation {
  const checks: DebugCheck[] = []
  const batteryVoltageV = finiteNumber(state.batteryVoltageV)
  const gpsSatellites = finiteNumber(state.gpsSatellites)
  const gpsHdop = finiteNumber(state.gpsHdop, 99)
  const rcSignalPercent = finiteNumber(state.rcSignalPercent)
  const rthAltitudeM = finiteNumber(state.rthAltitudeM)
  const lowBatteryPercent = finiteNumber(state.lowBatteryPercent)
  const criticalBatteryPercent = finiteNumber(state.criticalBatteryPercent)

  checks.push(check(
    'assembly', 'engineering', '装配与工程校核',
    context.validationPassed ? 'pass' : 'error',
    context.validationPassed ? '装配校核通过' : `${context.blockingErrorCount} 项阻断错误`,
    context.validationPassed ? '保持当前装配配置。' : '返回装配工作台处理阻断错误后再进入系统调试。',
  ))

  checks.push(check(
    'engineering-model', 'engineering', '工程模型完整性',
    context.engineeringAvailable ? 'pass' : 'error',
    context.engineeringAvailable ? '参数可计算' : '缺少可用工程结果',
    context.engineeringAvailable ? '可继续执行动力与电源检查。' : '补齐组件和工程参数后重新计算。',
  ))

  const twr = context.thrustWeightRatio
  const twrSeverity: DebugSeverity = twr === null ? 'error' : twr >= 1.8 ? 'pass' : twr >= 1.5 ? 'warning' : 'error'
  checks.push(check(
    'twr', 'engineering', '推重比', twrSeverity,
    twr === null ? '—' : twr.toFixed(2),
    twrSeverity === 'pass' ? '满足本课程调试推荐范围。' : '检查电机、螺旋桨、电池和整机质量匹配。',
  ))

  const cg = context.cgHorizontalM
  const cgSeverity: DebugSeverity = cg === null ? 'error' : cg <= 0.03 ? 'pass' : cg <= 0.05 ? 'warning' : 'error'
  checks.push(check(
    'cg', 'engineering', '水平重心偏移', cgSeverity,
    cg === null ? '—' : `${(cg * 1000).toFixed(0)} mm`,
    cgSeverity === 'pass' ? '重心位置适合进入后续调试。' : '调整电池或载荷安装位置，减小重心偏移。',
  ))

  const margins = [
    context.escCurrentMarginA,
    context.batteryContinuousMarginA,
    context.powerModuleCurrentMarginA,
  ].filter((value): value is number => value !== null)
  const minMargin = margins.length ? Math.min(...margins) : null
  const marginSeverity: DebugSeverity = minMargin === null ? 'error' : minMargin >= 5 ? 'pass' : minMargin >= 0 ? 'warning' : 'error'
  checks.push(check(
    'current-margin', 'propulsion', '电流裕量', marginSeverity,
    minMargin === null ? '—' : `${minMargin.toFixed(1)} A`,
    marginSeverity === 'pass' ? 'ESC、电池和电源模块电流裕量正常。' : '检查最大电流能力，避免带载时超过器件能力。',
  ))

  const batteryMin = context.batteryMinVoltageV
  const batteryMax = context.batteryMaxVoltageV
  const batteryNominal = context.batteryNominalVoltageV
  let batterySeverity: DebugSeverity = 'warning'
  if (batteryMin !== null && batteryMax !== null) {
    batterySeverity = batteryVoltageV < batteryMin || batteryVoltageV > batteryMax
      ? 'error'
      : batteryNominal !== null && batteryVoltageV < batteryNominal * 0.9
        ? 'warning'
        : 'pass'
  }
  checks.push(check(
    'battery-voltage', 'propulsion', '上电电压', batterySeverity,
    `${batteryVoltageV.toFixed(1)} V`,
    batterySeverity === 'pass' ? '电池电压位于当前配置可用范围。' : `核对电池状态与电压范围 ${fmt(batteryMin)}–${fmt(batteryMax)} V。`,
  ))

  checks.push(check(
    'imu', 'sensors', 'IMU 校准',
    state.imuCalibrated ? 'pass' : 'error',
    state.imuCalibrated ? '已校准' : '未校准',
    state.imuCalibrated ? '姿态基准可用。' : '重新完成加速度计/陀螺仪校准，并复核安装方向。',
  ))
  checks.push(check(
    'compass', 'sensors', '罗盘校准',
    state.compassCalibrated ? 'pass' : 'error',
    state.compassCalibrated ? '已校准' : '未校准',
    state.compassCalibrated ? '航向基准可用。' : '移除磁干扰源后重新执行罗盘校准。',
  ))

  const gpsSeverity: DebugSeverity = gpsSatellites >= 10 && gpsHdop <= 1.5
    ? 'pass'
    : gpsSatellites >= 7 && gpsHdop <= 2.5
      ? 'warning'
      : 'error'
  checks.push(check(
    'gps', 'sensors', 'GNSS 定位质量', gpsSeverity,
    `${gpsSatellites.toFixed(0)} 星 / HDOP ${gpsHdop.toFixed(1)}`,
    gpsSeverity === 'pass' ? '定位质量满足本课程起飞前检查。' : '检查天线环境、遮挡和干扰，等待定位质量改善。',
  ))

  checks.push(check(
    'rc-calibration', 'link', '遥控器通道校准',
    state.rcCalibrated ? 'pass' : 'error',
    state.rcCalibrated ? '已完成' : '未完成',
    state.rcCalibrated ? '通道中位与行程已确认。' : '执行遥控器校准并确认通道映射、正反向和行程。',
  ))

  const rcSeverity: DebugSeverity = rcSignalPercent >= 80 ? 'pass' : rcSignalPercent >= 60 ? 'warning' : 'error'
  checks.push(check(
    'rc-signal', 'link', '控制链路质量', rcSeverity,
    `${rcSignalPercent.toFixed(0)}%`,
    rcSeverity === 'pass' ? '控制链路状态正常。' : '检查接收机供电、天线布置、绑定状态和现场干扰。',
  ))

  for (const motor of ['M1', 'M2', 'M3', 'M4'] as const) {
    const item = state.motors[motor]
    const expected = EXPECTED_MOTOR_DIRECTIONS[motor]
    const severity: DebugSeverity = item.responding && item.direction === expected ? 'pass' : 'error'
    checks.push(check(
      `motor-${motor}`, 'propulsion', `${motor} 电机测试`, severity,
      `${item.responding ? '响应' : '无响应'} / ${item.direction}`,
      severity === 'pass' ? `响应正常，旋向 ${expected}。` : `检查电机输出、ESC 连接，并将课程标准旋向校正为 ${expected}。`,
    ))
  }

  const failsafeSeverity: DebugSeverity = state.failsafeMode === 'RTH' ? 'pass' : state.failsafeMode === 'LAND' ? 'warning' : 'error'
  checks.push(check(
    'failsafe', 'link', '失控保护策略', failsafeSeverity,
    state.failsafeMode,
    state.failsafeMode === 'RTH' ? '课程场景采用返航策略。' : '根据课程任务重新核对失控后的动作策略。',
  ))

  const rthSeverity: DebugSeverity = rthAltitudeM >= 20 ? 'pass' : rthAltitudeM >= 15 ? 'warning' : 'error'
  checks.push(check(
    'rth-altitude', 'link', '返航高度', rthSeverity,
    `${rthAltitudeM.toFixed(0)} m`,
    rthSeverity === 'pass' ? '达到本课程默认场景推荐值。' : '结合训练场障碍物高度重新设置返航高度。',
  ))

  const batteryThresholdSeverity: DebugSeverity = lowBatteryPercent >= criticalBatteryPercent + 5 && criticalBatteryPercent >= 10
    ? 'pass'
    : lowBatteryPercent > criticalBatteryPercent
      ? 'warning'
      : 'error'
  checks.push(check(
    'battery-thresholds', 'link', '低电量保护阈值', batteryThresholdSeverity,
    `${lowBatteryPercent.toFixed(0)}% / ${criticalBatteryPercent.toFixed(0)}%`,
    batteryThresholdSeverity === 'pass' ? '低电量与严重低电量阈值层级合理。' : '保证低电量阈值高于严重低电量阈值，并保留足够处置余量。',
  ))

  checks.push(check(
    'propellers-secured', 'preflight', '螺旋桨紧固检查',
    state.propellersSecured ? 'pass' : 'error',
    state.propellersSecured ? '已确认' : '未确认',
    state.propellersSecured ? '完成最终机械检查。' : '断电状态下检查桨叶型号、方向和紧固状态。',
  ))
  checks.push(check(
    'wiring-secured', 'preflight', '线束与接插件检查',
    state.wiringSecured ? 'pass' : 'error',
    state.wiringSecured ? '已确认' : '未确认',
    state.wiringSecured ? '线束状态已确认。' : '检查插头锁止、极性、线束固定与旋翼干涉。',
  ))
  checks.push(check(
    'environment-clear', 'preflight', '测试环境确认',
    state.environmentClear ? 'pass' : 'error',
    state.environmentClear ? '安全' : '未确认',
    state.environmentClear ? '可在教师规定流程下进入下一阶段。' : '清空桨盘区域并完成场地、人员和防护检查。',
  ))

  const passCount = checks.filter(item => item.severity === 'pass').length
  const warningCount = checks.filter(item => item.severity === 'warning').length
  const errorCount = checks.filter(item => item.severity === 'error').length
  const score = Math.round(((passCount + warningCount * 0.5) / checks.length) * 100)
  const readiness = errorCount > 0 ? 'BLOCKED' : warningCount > 0 ? 'CONDITIONAL' : 'READY'

  return { readiness, score, checks, passCount, warningCount, errorCount }
}
