import type { RouteLocationNormalizedLoaded, RouteLocationRaw } from 'vue-router'
import { activeTrainingQuery } from './trainingContext'

export type LearningRole = 'student' | 'teacher' | 'admin'
export type LearningStageKey = 'prepare' | 'assembly' | 'debug' | 'diagnosis' | 'preflight' | 'flight' | 'review'

export interface LearningStage {
  key: LearningStageKey
  title: string
  shortTitle: string
}

export interface PageLearningGuide {
  eyebrow: string
  title: string
  objective: string
  currentTask: string
  steps: string[]
  observe?: string[]
  mistakes?: string[]
  completion: string
  why: string
  glossary: Array<{ term: string; definition: string }>
  nextLabel: string
  nextTo: RouteLocationRaw | null
}

type DebugSectionKey = 'sensors' | 'rc' | 'power' | 'safety' | 'preflight'

export const LEARNING_STAGES: LearningStage[] = [
  { key: 'prepare', title: '任务准备', shortTitle: '准备' },
  { key: 'assembly', title: '装配确认', shortTitle: '装' },
  { key: 'debug', title: '系统调试', shortTitle: '调' },
  { key: 'diagnosis', title: '故障诊断', shortTitle: '检修' },
  { key: 'preflight', title: '起飞前检查', shortTitle: '检' },
  { key: 'flight', title: '飞行验证', shortTitle: '验' },
  { key: 'review', title: '训练复盘', shortTitle: '复盘' },
]

function firstQuery(route: RouteLocationNormalizedLoaded, key: string): string {
  const raw = route.query[key]
  return Array.isArray(raw) ? String(raw[0] ?? '') : String(raw ?? '')
}

function carryTrainingQuery(route: RouteLocationNormalizedLoaded): Record<string, string> {
  return activeTrainingQuery(route.query)
}

export function learningStageForRoute(route: RouteLocationNormalizedLoaded): LearningStageKey {
  if (route.path === '/review') return 'review'
  if (route.path === '/flight' || route.path.startsWith('/history')) return 'flight'
  if (route.path === '/assembly' || route.path === '/components') return 'assembly'
  if (route.path === '/debugging') {
    if (firstQuery(route, 'section') === 'preflight') return 'preflight'
    if (firstQuery(route, 'scenario') || firstQuery(route, 'run') || firstQuery(route, 'guide') === 'diagnosis') return 'diagnosis'
    return 'debug'
  }
  return 'prepare'
}

export function learningStageTarget(
  stage: LearningStageKey,
  role: LearningRole,
  route: RouteLocationNormalizedLoaded,
): RouteLocationRaw {
  const trainingQuery = carryTrainingQuery(route)
  if (stage === 'prepare') return role === 'student' ? '/training' : '/teacher'
  if (stage === 'assembly') return Object.keys(trainingQuery).length ? { path: '/assembly', query: trainingQuery } : '/assembly'
  if (stage === 'debug') return Object.keys(trainingQuery).length ? { path: '/debugging', query: trainingQuery } : '/debugging'
  if (stage === 'diagnosis') return { path: '/debugging', query: { ...trainingQuery, guide: 'diagnosis' } }
  if (stage === 'preflight') return { path: '/debugging', query: { ...trainingQuery, section: 'preflight' } }
  if (stage === 'flight') return { path: '/flight', query: trainingQuery }
  return { path: '/review', query: trainingQuery.run ? { run: trainingQuery.run } : {} }
}

function roleCopy(role: LearningRole): string {
  if (role === 'teacher') return '教师演示视角：讲清目标、观察学生证据，并用同一流程进行课堂示范。'
  if (role === 'admin') return '管理员验收视角：按真实教学链检查每一阶段是否可理解、可操作、可追溯。'
  return '学生学习视角：一次只完成一个明确任务，遇到问题先观察证据，再进行操作。'
}

function debugSectionRoute(
  section: DebugSectionKey,
  trainingQuery: Record<string, string>,
): RouteLocationRaw {
  return { path: '/debugging', query: { ...trainingQuery, section } }
}

function debugSectionGuide(
  section: Exclude<DebugSectionKey, 'preflight'>,
  role: LearningRole,
  assigned: boolean,
  trainingQuery: Record<string, string>,
): PageLearningGuide {
  const roleHint = roleCopy(role)
  const taskHint = assigned
    ? '当前处于故障诊断任务中：所有观察都要服务于“现象—证据—原因—修复—验证”证据链。'
    : '当前处于自由调试：先理解正常状态，再练习发现异常。'
  const guides: Record<Exclude<DebugSectionKey, 'preflight'>, Omit<PageLearningGuide, 'eyebrow' | 'objective'>> = {
    sensors: {
      title: assigned ? '故障诊断 · 飞控与传感器' : '飞控与传感器调试',
      currentTask: '判断 IMU、GNSS、磁罗盘、气压计和 EKF 的数据是否健康、可信且相互一致。',
      steps: [
        '先确认数据来源：教学模拟或 PX4 MAVLink，并观察 Heartbeat 与数据延迟。',
        '飞机静止在地面时，检查姿态是否稳定，角速度是否接近零，加速度是否符合重力方向。',
        '检查 GNSS Fix、卫星数和 EPH，不要只看“有坐标”。',
        '比较磁场强度、航向、气压高度和 EKF 状态，寻找彼此矛盾的数据。',
        '执行“传感器检查”；仅对异常传感器校准，校准后重新检查。',
      ],
      observe: [
        '数据是否持续刷新，延迟是否异常增大。',
        '静止状态下姿态、角速度和高度是否仍明显漂移。',
        'GNSS、磁罗盘与 EKF 是否同时支持当前的位置和航向判断。',
        'Pre-Arm 阻断信息具体指向哪个传感器。',
      ],
      mistakes: [
        '看到数值就认为传感器正常，没有判断数值是否合理。',
        '未记录异常证据就直接点击校准。',
        '把“校准命令已受理”当作“校准已经通过”。',
      ],
      completion: '完成传感器检查；关键数据合理，EKF无未解释异常，相关校准状态为通过，并记录诊断证据。',
      why: '传感器和状态估计是后续遥控、动力与飞行判断的基础。错误数据会让正常执行机构也表现为不可控。',
      glossary: [
        { term: 'Heartbeat', definition: '飞控周期发送的在线信号；持续超时说明连接或飞控进程异常。' },
        { term: 'EPH', definition: 'GNSS水平位置估计误差；数值越小通常表示水平定位越可靠。' },
        { term: 'EKF', definition: '融合IMU、磁罗盘、GNSS和气压计等数据，估计飞行器姿态与位置。' },
      ],
      nextLabel: '继续遥控系统调试',
      nextTo: debugSectionRoute('rc', trainingQuery),
    },
    rc: {
      title: assigned ? '故障诊断 · 遥控系统' : '遥控系统调试',
      currentTask: '验证 Roll、Pitch、Yaw、Throttle 的通道映射、方向、中位、行程和失控保护。',
      steps: [
        '确认当前使用虚拟教学输入还是真实 PX4 遥控数据，并检查链路质量。',
        '依次单独推动 Roll、Pitch、Yaw、Throttle，确认只有目标通道产生主要变化。',
        '检查 Roll、Pitch、Yaw 中位值，检查四个主通道的最小值和最大值是否覆盖有效行程。',
        '核对每个通道方向；方向错误时只修改对应反向设置，不要交换无关通道。',
        '应用参数后重新执行完整行程与失控保护检查。',
      ],
      observe: [
        '摇杆动作与通道编号是否一一对应。',
        '中位是否接近1500 μs，行程是否接近1000–2000 μs。',
        'Throttle最低位是否能被正确识别。',
        '信号丢失后是否进入预期的Failsafe状态。',
      ],
      mistakes: [
        '把通道映射错误和通道方向错误混为一谈。',
        '只检查摇杆中位，没有完成全行程采集。',
        '同时修改多个参数，导致无法判断是哪项修改解决了问题。',
      ],
      completion: '四个主通道映射、方向、中位和行程均正确，失控保护可触发，遥控系统验证通过。',
      why: '遥控输入错误可能在地面看似正常，却在起飞后把一个动作解释成另一个动作。',
      glossary: [
        { term: 'Channel Mapping', definition: '把接收机通道分配给 Roll、Pitch、Yaw、Throttle 等控制功能。' },
        { term: 'RC Failsafe', definition: '遥控信号丢失时飞控自动进入的保护状态与动作。' },
      ],
      nextLabel: '继续动力系统调试',
      nextTo: debugSectionRoute('power', trainingQuery),
    },
    power: {
      title: assigned ? '故障诊断 · 动力系统' : '动力系统调试',
      currentTask: '逐个验证 M1–M4 的映射、旋向和响应，确认动力配置与装配结果一致。',
      steps: [
        '确认飞机处于未解锁状态，并理解实体操作时必须拆桨或固定机体。',
        '对照机架编号和页面三维位置，先明确 M1–M4 各自对应的物理电机。',
        '按 M1、M2、M3、M4 顺序逐个执行低功率测试，观察“指令电机”和“实际响应电机”。',
        '核对每个电机的 CW/CCW 旋向与对应螺旋桨方向。',
        '检查四个电机响应一致性以及电池、ESC和电源模块的电流余量。',
      ],
      observe: [
        '页面高亮的实际电机是否与测试按钮编号一致。',
        '四个电机是否都能响应，且没有某一路明显迟滞或缺失。',
        '电机旋向与螺旋桨 CW/CCW 配置是否匹配。',
        '最大电流是否超过 ESC、电池或电源模块能力。',
      ],
      mistakes: [
        '只确认电机会转，没有确认转动的是正确电机。',
        '混淆电机编号、安装位置和旋转方向。',
        '一次测试多个电机，失去定位映射错误的依据。',
      ],
      completion: 'M1–M4逐项测试完成，编号与实际响应一致，旋向正确，动力系统没有未处理的工程阻断。',
      why: '动力映射或旋向错误会在解锁后立即产生错误力矩，是起飞前必须排除的高风险问题。',
      glossary: [
        { term: 'Motor Mapping', definition: '飞控输出编号与飞机上实际电机安装位置之间的对应关系。' },
        { term: 'CW / CCW', definition: '顺时针与逆时针旋转方向；必须与机架布局和螺旋桨匹配。' },
      ],
      nextLabel: '继续安全设置调试',
      nextTo: debugSectionRoute('safety', trainingQuery),
    },
    safety: {
      title: assigned ? '故障诊断 · 安全设置' : '安全设置调试',
      currentTask: '检查失联、低电量、返航和地理围栏策略，确保异常发生时飞机执行可预期动作。',
      steps: [
        '读取当前安全参数，先保存或理解基线值。',
        '检查 RC Loss 动作，确认失联后不会继续保持不可控飞行。',
        '检查低电量阈值与动作，确认 Warning、Critical、Emergency 的关系合理。',
        '核对 RTL高度和Geofence范围，结合教学场地判断数值是否安全。',
        '处理红色冲突项，应用修改后重新读取参数并运行安全／Pre-Arm验证。',
      ],
      observe: [
        '参数单位、阈值大小关系和动作枚举是否正确。',
        'RTL高度是否高于典型障碍物，同时符合教学场地限制。',
        '修改后的值是否真正回读成功。',
        '安全验证是否仍报告失联、电池或围栏阻断。',
      ],
      mistakes: [
        '直接载入推荐值却不能解释每个参数的作用。',
        '忽略单位，把米、百分比或秒当作同一种量。',
        '把“参数写入成功”当作“安全策略验证通过”。',
      ],
      completion: '安全参数无冲突，修改已回读确认，RC Loss、低电量、RTL和Geofence策略通过安全验证。',
      why: '安全参数决定系统失效时的行为。正常飞行表现良好，并不能证明异常情况下仍然安全。',
      glossary: [
        { term: 'RTL', definition: 'Return to Launch，触发后按设定高度和逻辑返回起飞点。' },
        { term: 'Geofence', definition: '限制飞行高度或水平范围的虚拟边界。' },
        { term: 'Failsafe', definition: '检测到失联、低电量等异常后自动执行的保护策略。' },
      ],
      nextLabel: '进入起飞前检查',
      nextTo: debugSectionRoute('preflight', trainingQuery),
    },
  }
  const selected = guides[section]
  return {
    ...selected,
    eyebrow: `LEARNING GUIDE · ${assigned ? '故障诊断' : '系统调试'} · ${section.toUpperCase()}`,
    objective: `${taskHint}${roleHint}`,
    completion: assigned
      ? `${selected.completion} 将本页异常现象、关键数据和验证结果写入诊断工作单。`
      : selected.completion,
  }
}

export function pageLearningGuide(
  route: RouteLocationNormalizedLoaded,
  role: LearningRole,
): PageLearningGuide {
  const trainingQuery = carryTrainingQuery(route)
  const roleHint = roleCopy(role)
  if (route.path === '/teacher') return {
    eyebrow: 'LEARNING GUIDE · 教学组织',
    title: role === 'admin' ? '验收班级任务与学习证据' : '发布任务并观察学生学习过程',
    objective: `让班级、任务、TrainingRun、诊断证据和成绩形成可追溯闭环。${roleHint}`,
    currentTask: role === 'admin' ? '检查角色权限、班级任务和训练记录是否能够完整追溯。' : '选择班级，发布案例任务，并从成绩册打开学生训练复盘。',
    steps: role === 'admin'
      ? ['核对用户角色', '检查班级与任务', '抽查TrainingRun事件', '打开训练复盘', '确认数据可导出']
      : ['创建或选择班级', '发布故障案例', '观察任务进度', '从成绩册查看复盘', '根据共性问题调整教学'],
    completion: '能够从一名学生的成绩追溯到诊断工作单、过程事件、Pre-Arm和飞行验证。',
    why: '教师和管理员使用与学生一致的任务链，才能准确判断问题发生在学习、操作还是平台环节。',
    glossary: [{ term: '学习证据', definition: '能说明学生如何判断、操作和验证的过程记录，而不只是最终分数。' }],
    nextLabel: '进入装配教学演示', nextTo: '/assembly',
  }
  if (route.path === '/training') return {
    eyebrow: 'LEARNING GUIDE · 任务准备',
    title: '先确认今天要完成的任务',
    objective: `理解任务目标、案例现象、完成标准和截止时间。${roleHint}`,
    currentTask: '加入教师班级，并从任务卡片开始或继续一次实训。',
    steps: ['确认班级和任务名称', '阅读故障现象与建议时间', '检查当前飞机', '点击开始或继续实训'],
    completion: '已创建 TrainingRun，并进入教师指定的故障案例。',
    why: '从任务入口开始，系统才能持续记录诊断、修复、Pre-Arm和飞行验证过程。',
    glossary: [{ term: 'TrainingRun', definition: '一次独立的课程实训记录，保存过程、成绩和验证状态。' }],
    nextLabel: '查看当前飞机', nextTo: '/aircraft',
  }
  if (route.path === '/aircraft') return {
    eyebrow: 'LEARNING GUIDE · 飞机准备',
    title: '选择本次训练使用的飞机',
    objective: `确认装配、参数和实验记录都绑定到正确飞机。${roleHint}`,
    currentTask: '打开教师指定或本次准备使用的飞机设计。',
    steps: ['确认飞机名称与用途', '查看工程检查状态', '选择“继续设计”', '进入装配确认'],
    completion: '顶部“当前飞机”显示正确，且已进入装配页面。',
    why: '不同飞机的部件、工程参数和飞行许可相互隔离，选错飞机会导致后续证据不一致。',
    glossary: [{ term: '工程检查', definition: '检查推力、电流、电压、重心和部件匹配是否满足基本安全要求。' }],
    nextLabel: '进入装配确认', nextTo: '/assembly',
  }
  if (route.path === '/assembly' || route.path === '/components') return {
    eyebrow: 'LEARNING GUIDE · 装配确认',
    title: '先装正确，再讨论能否起飞',
    objective: `认识部件作用，完成物理安装和工程兼容性检查。${roleHint}`,
    currentTask: '按左侧顺序完成机架、动力、供电、飞控导航和螺旋桨安装。',
    steps: ['选择当前装配步骤', '比较候选部件关键参数', '在3D视图选择安装点', '运行装配检查并处理阻断项'],
    completion: '必需安装位完整，空间检查和工程检查均通过。',
    why: '部件“能够放上去”不等于系统“能够安全工作”，必须同时验证物理位置和电气性能。',
    glossary: [
      { term: 'Mount Anchor', definition: '3D模型中真实的部件安装位置。' },
      { term: '推重比', definition: '最大总推力与整机重量之比，反映起飞和机动余量。' },
    ],
    nextLabel: '进入系统调试', nextTo: '/debugging',
  }
  if (route.path === '/debugging' && firstQuery(route, 'section') === 'preflight') return {
    eyebrow: 'LEARNING GUIDE · 起飞前检查',
    title: '用六项门禁确认飞机是否允许起飞',
    objective: `汇总装配、传感器、遥控、动力、安全策略和Pre-Arm结果。${roleHint}`,
    currentTask: '逐项处理阻断卡片，再执行最终起飞检查。',
    steps: [
      '确认页面中的飞机名称和配置与本次训练一致。',
      '逐项查看装配、传感器、遥控、动力、安全设置和PX4 Pre-Arm六项门禁。',
      '对未通过项目点击“检查”，回到对应模块修复并重新验证。',
      '所有阻断项清除后执行最终起飞检查。',
      '确认飞行许可已生成、未过期，再进入飞行验证。',
    ],
    observe: ['阻断项与提醒项的区别。', '每项门禁引用的是当前飞机的最新验证结果。', '飞行许可的生成时间和有效期。'],
    mistakes: ['只看总分，不处理仍存在的阻断项。', '更换飞机或修改配置后继续使用旧许可。', '把教学模拟通过等同于真实飞控状态通过。'],
    completion: '六项门禁全部通过，并生成未过期的飞行许可。',
    why: '最终检查把分散的调试证据收敛为一次明确的“可飞/不可飞”判断。',
    glossary: [{ term: 'Pre-Arm', definition: '飞控在解锁前执行的状态检查；存在阻断时不得起飞。' }],
    nextLabel: '进入飞行验证', nextTo: { path: '/flight', query: trainingQuery },
  }
  if (route.path === '/debugging') {
    const assigned = Boolean(trainingQuery.run || trainingQuery.scenario || firstQuery(route, 'guide') === 'diagnosis')
    const requested = firstQuery(route, 'section')
    const section: Exclude<DebugSectionKey, 'preflight'> = ['sensors', 'rc', 'power', 'safety'].includes(requested)
      ? requested as Exclude<DebugSectionKey, 'preflight'>
      : 'power'
    return debugSectionGuide(section, role, assigned, trainingQuery)
  }
  if (route.path === '/flight') return {
    eyebrow: 'LEARNING GUIDE · 飞行验证',
    title: '用基础飞行闭环验证装调结果',
    objective: `完成地面静止、解锁、起飞、悬停、降落和上锁。${roleHint}`,
    currentTask: '确认飞机在地面且未解锁，再按按钮提示完成飞行闭环。',
    steps: ['连接或开始仿真', '确认地面状态并解锁', '起飞至2米并观察悬停', '执行降落并确认回到地面', '上锁并保存结果'],
    completion: '系统观察到起飞、悬停、降落，且最终处于地面未解锁状态。',
    why: '飞行验证不是练习炫技，而是确认此前装配、调试和检修结果能够支持安全基础飞行。',
    glossary: [
      { term: '解锁（Arm）', definition: '允许飞控驱动电机；解锁前必须通过安全检查。' },
      { term: 'SIH', definition: 'PX4的软件在环/硬件抽象仿真方式，用于验证飞控逻辑。' },
    ],
    nextLabel: '查看训练复盘', nextTo: { path: '/review', query: trainingQuery.run ? { run: trainingQuery.run } : {} },
  }
  if (route.path === '/review') return {
    eyebrow: 'LEARNING GUIDE · 训练复盘',
    title: '把一次操作转化为可迁移的经验',
    objective: `回看诊断证据、评分构成、错误和后续建议。${roleHint}`,
    currentTask: '说明本次故障为什么发生、你如何证明修复有效。',
    steps: ['查看任务结果', '核对诊断工作单', '回顾提示和错误', '确认Pre-Arm与飞行验证', '记录下一次改进重点'],
    completion: '能够独立说出“现象—证据—原因—修复—验证”完整链条。',
    why: '复盘让平台成绩变成下一次实体操作可使用的方法，而不是一次性的过关记录。',
    glossary: [{ term: '形成性评价', definition: '在学习过程中持续提供反馈，用来决定下一步如何改进。' }],
    nextLabel: role === 'student' ? '返回我的实训' : '返回教师工作台', nextTo: role === 'student' ? '/training' : '/teacher',
  }
  return {
    eyebrow: 'LEARNING GUIDE · 平台导航',
    title: '围绕“装—调—检—修—验”开展学习',
    objective: roleHint,
    currentTask: '从顶部任务导航选择当前教学阶段。',
    steps: ['准备任务', '确认装配', '完成调试与诊断', '执行起飞检查', '完成飞行验证并复盘'],
    completion: '能够找到当前阶段、完成标准和下一步入口。',
    why: '统一任务链帮助不同角色使用同一套教学语言和验收标准。',
    glossary: [],
    nextLabel: role === 'student' ? '进入我的实训' : '进入教师工作台', nextTo: role === 'student' ? '/training' : '/teacher',
  }
}
