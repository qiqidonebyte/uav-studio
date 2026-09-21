import type { RouteLocationNormalizedLoaded, RouteLocationRaw } from 'vue-router'

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
  completion: string
  why: string
  glossary: Array<{ term: string; definition: string }>
  nextLabel: string
  nextTo: RouteLocationRaw | null
}

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
  const query: Record<string, string> = {}
  for (const key of ['run', 'scenario', 'assignment']) {
    const value = firstQuery(route, key)
    if (value) query[key] = value
  }
  return query
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
  if (stage === 'assembly') return '/assembly'
  if (stage === 'debug') return '/debugging'
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
    steps: ['查看未通过门禁', '点击“检查”返回对应模块', '修复后重新验证', '生成当前飞机的飞行许可'],
    completion: '六项门禁全部通过，并生成未过期的飞行许可。',
    why: '最终检查把分散的调试证据收敛为一次明确的“可飞/不可飞”判断。',
    glossary: [{ term: 'Pre-Arm', definition: '飞控在解锁前执行的状态检查；存在阻断时不得起飞。' }],
    nextLabel: '进入飞行验证', nextTo: { path: '/flight', query: trainingQuery },
  }
  if (route.path === '/debugging') {
    const assigned = Boolean(trainingQuery.run || trainingQuery.scenario || firstQuery(route, 'guide') === 'diagnosis')
    return {
      eyebrow: `LEARNING GUIDE · ${assigned ? '故障诊断' : '系统调试'}`,
      title: assigned ? '先记录证据，再提交诊断' : '按模块完成系统调试',
      objective: `${assigned ? '根据现象形成“证据—原因—修复—验证”闭环。' : '掌握传感器、遥控、动力和安全设置的基本检查方法。'}${roleHint}`,
      currentTask: assigned ? '阅读案例现象，使用正确工具检查，并填写诊断工作单。' : '从飞控传感器开始，依次完成四个调试模块。',
      steps: assigned
        ? ['复述故障现象', '记录关键检查数据', '提出故障原因', '修复并重新验证', '完成诊断工作单后提交']
        : ['检查飞控与传感器', '验证遥控映射', '逐个测试电机', '检查Failsafe策略'],
      completion: assigned ? '案例成功条件满足，诊断工作单五项完整。' : '四个模块均完成验证，没有未处理的阻断项。',
      why: '诊断能力来自证据链，而不是记住某个“修复”按钮的位置。',
      glossary: [
        { term: 'EKF', definition: '融合IMU、磁罗盘和GNSS等数据，估计飞行器姿态与位置。' },
        { term: 'Failsafe', definition: '失联、低电量或越界时自动执行的安全保护策略。' },
      ],
      nextLabel: '进入起飞前检查', nextTo: { path: '/debugging', query: { ...trainingQuery, section: 'preflight' } },
    }
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
