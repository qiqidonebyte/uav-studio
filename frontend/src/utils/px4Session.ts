import type { Px4Status } from '../api/px4'

export type Px4SessionTone = 'waiting' | 'queued' | 'starting' | 'ready' | 'error'

export interface Px4SessionPresentation {
  tone: Px4SessionTone
  title: string
  detail: string
  statusText: string
}

export function px4SessionPresentation(status: Px4Status | null | undefined): Px4SessionPresentation {
  const sessionStatus = status?.session_status ?? 'unassigned'
  const queuePosition = Math.max(0, Number(status?.queue_position) || 0)
  const slotId = status?.slot_id

  if (sessionStatus === 'queued' || queuePosition > 0) {
    return {
      tone: 'queued',
      title: 'PX4 资源排队中',
      detail: `12 个仿真槽位当前均在使用，你排在第 ${queuePosition || 1} 位。获得槽位后系统将自动连接。`,
      statusText: `排队第 ${queuePosition || 1} 位`,
    }
  }

  if (sessionStatus === 'starting' || (slotId != null && !status?.connected)) {
    return {
      tone: 'starting',
      title: `PX4 槽位 #${slotId ?? '—'} 启动中`,
      detail: '资源已经分配，正在启动 PX4 SIH 并等待 Heartbeat，请保持页面打开。',
      statusText: `槽位 #${slotId ?? '—'} · 准备中`,
    }
  }

  if (sessionStatus === 'failed') {
    return {
      tone: 'error',
      title: 'PX4 会话启动失败',
      detail: status?.last_error || '请重新连接；仍失败时请联系教师检查仿真服务。',
      statusText: '启动失败',
    }
  }

  if (status?.connected || sessionStatus === 'ready' || sessionStatus === 'active') {
    return {
      tone: 'ready',
      title: 'PX4 SIH · MAVLink',
      detail: `${slotId != null ? `槽位 #${slotId} · ` : ''}${status?.connection_url || 'MAVLink'} · SYSID ${status?.system_id ?? '—'}`,
      statusText: slotId != null ? `槽位 #${slotId} · 已连接` : 'PX4 已连接',
    }
  }

  return {
    tone: 'waiting',
    title: 'PX4 SIH · 等待资源',
    detail: status?.last_error || '正在申请课堂仿真资源，请保持页面打开。',
    statusText: '等待资源',
  }
}
