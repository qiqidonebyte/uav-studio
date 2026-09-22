<template>
  <div class="debug-motor-scene">
    <DroneScene
      :telemetry="telemetry"
      :aircraft="aircraft"
      :components="components"
      :engineering="engineering"
      grounded
    />

    <div class="motor-overlay" aria-hidden="true">
      <div
        v-for="motor in motors"
        :key="motor.name"
        :class="['motor-badge', motor.name.toLowerCase(), {
          active: actualMotor === motor.name,
          commanded: commandedMotor === motor.name,
          fault: faultMotor === motor.name,
        }]"
      >
        <span class="pulse-ring"></span>
        <b>{{ motor.name }}</b>
        <small>{{ motor.position }}</small>
      </div>
    </div>

    <div class="scene-caption">
      <span>地面动力测试 · 数据源：</span>
      <b>{{ live ? 'PX4 SIH / MAVLink' : '教学模拟' }}</b>
      <em>· {{ aircraft?.name || '当前飞机' }}</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import DroneScene from './DroneScene.vue'
import type { AircraftDefinition, AircraftEngineeringSummary, Component, MotorName } from '../types/aircraft'
import type { TelemetryFrame } from '../types/telemetry'

withDefaults(defineProps<{
  telemetry: TelemetryFrame
  aircraft?: AircraftDefinition | null
  components?: Component[]
  engineering?: AircraftEngineeringSummary | null
  commandedMotor?: MotorName | null
  actualMotor?: MotorName | null
  faultMotor?: MotorName | null
  live?: boolean
}>(), {
  aircraft: null,
  components: () => [],
  engineering: null,
  commandedMotor: null,
  actualMotor: null,
  faultMotor: null,
  live: false,
})

const motors: Array<{ name: MotorName; position: string }> = [
  { name: 'M1', position: '右前' },
  { name: 'M2', position: '右后' },
  { name: 'M3', position: '左后' },
  { name: 'M4', position: '左前' },
]
</script>

<style scoped>
.debug-motor-scene {
  position: relative;
  height: 100%;
  min-height: 390px;
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(6, 24, 42, .98), rgba(5, 18, 33, .98));
}
.debug-motor-scene :deep(.drone-scene) { height: 100%; min-height: 390px; }
.debug-motor-scene :deep(.scene-readout),
.debug-motor-scene :deep(.wind-readout) { opacity: .72; }
.debug-motor-scene :deep(.scene-legend) { opacity: .7; }
.motor-overlay { position:absolute; inset:0; pointer-events:none; z-index:8; }
.motor-badge {
  position:absolute;
  width:58px;
  height:58px;
  display:grid;
  place-content:center;
  justify-items:center;
  border:1px solid rgba(101, 157, 203, .28);
  border-radius:50%;
  background:rgba(4, 22, 39, .78);
  box-shadow:0 8px 28px rgba(0,0,0,.24);
  color:#c9def2;
  transition:.18s ease;
}
.motor-badge b { font-size:13px; line-height:15px; }
.motor-badge small { margin-top:1px; color:#7897b5; font-size:9px; }
.motor-badge.m1 { right:19%; top:20%; }
.motor-badge.m2 { left:18%; top:23%; }
.motor-badge.m3 { left:19%; bottom:21%; }
.motor-badge.m4 { right:18%; bottom:20%; }
.motor-badge.commanded { border-color:rgba(60, 171, 255, .75); color:#dff3ff; }
.motor-badge.active {
  border-color:#2da8ff;
  color:white;
  background:rgba(8, 106, 177, .42);
  box-shadow:0 0 0 5px rgba(39, 167, 255, .08), 0 0 28px rgba(39, 167, 255, .44);
}
.motor-badge.fault { border-color:#ff635c; box-shadow:0 0 22px rgba(255, 82, 70, .32); }
.pulse-ring { position:absolute; inset:-8px; border:1px solid transparent; border-radius:50%; }
.motor-badge.active .pulse-ring { border-color:rgba(42, 170, 255, .5); animation:motorPulse 1s ease-out infinite; }
.scene-caption {
  position:absolute;
  left:14px;
  bottom:12px;
  z-index:9;
  padding:7px 10px;
  border:1px solid rgba(102, 149, 190, .2);
  border-radius:8px;
  background:rgba(5, 19, 34, .84);
  color:#86a6c2;
  font-size:10px;
  backdrop-filter:blur(8px);
}
.scene-caption b { color:#d9edff; }
.scene-caption em { color:#5f829f; font-style:normal; }
@keyframes motorPulse { from { transform:scale(.92); opacity:1; } to { transform:scale(1.34); opacity:0; } }
@media(max-width:1100px){
  .motor-badge { width:48px;height:48px; }
  .scene-caption em { display:none; }
}
</style>
