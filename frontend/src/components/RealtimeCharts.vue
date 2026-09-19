<template>
  <div class="charts-panel">
    <div class="chart-tabs">
      <button v-for="tab in tabs" :key="tab" :class="['chart-tab',{active:active===tab}]" @click="active=tab">{{ tab }}</button>
      <div class="chart-live"><span class="dot"></span>实时 {{ telemetry.t.toFixed(0) }} s · {{ windowSeconds }} s 窗口</div>
    </div>
    <div class="charts-grid">
      <div ref="altEl" class="chart-box"></div>
      <div ref="attEl" class="chart-box"></div>
      <div ref="motorEl" class="chart-box"></div>
      <div ref="batteryEl" class="chart-box"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { TelemetryFrame } from '../types/telemetry'

const props = withDefaults(defineProps<{
  telemetry: TelemetryFrame
  history: TelemetryFrame[]
  windowSeconds?: number
}>(), { windowSeconds: 60 })

const tabs=['飞行状态','姿态','电机','动力','轨迹','实验结果']
const active=ref('飞行状态')
const altEl=ref<HTMLDivElement|null>(null)
const attEl=ref<HTMLDivElement|null>(null)
const motorEl=ref<HTMLDivElement|null>(null)
const batteryEl=ref<HTMLDivElement|null>(null)
let charts:echarts.ECharts[]=[]

const base=(title:string)=>({
  animation:false,
  title:{text:title,left:10,top:8,textStyle:{fontSize:12,fontWeight:600,color:'#22324a'}},
  grid:{left:42,right:14,top:42,bottom:28},
  xAxis:{type:'category',boundaryGap:false,axisLabel:{fontSize:10},data:[]},
  yAxis:{type:'value',axisLabel:{fontSize:10},splitLine:{lineStyle:{color:'#eef2f7'}}},
  tooltip:{trigger:'axis'},
})

function visibleHistory(): TelemetryFrame[] {
  if (props.history.length === 0) return []
  const latest = props.history[props.history.length - 1]?.t ?? props.telemetry.t
  const from = Math.max(0, latest - props.windowSeconds)
  return props.history.filter(frame => frame.t >= from)
}

function render(){
  if(charts.length!==4)return
  const h=visibleHistory()
  const x=h.map(f=>f.t.toFixed(1))
  charts[0].setOption({...base('高度 (m)'),xAxis:{...base('').xAxis,data:x},series:[{type:'line',showSymbol:false,data:h.map(f=>f.position.z)}]},true)
  charts[1].setOption({...base('姿态 (°)'),xAxis:{...base('').xAxis,data:x},legend:{top:9,right:8,textStyle:{fontSize:9}},series:[{name:'横滚',type:'line',showSymbol:false,data:h.map(f=>f.attitude.roll*180/Math.PI)},{name:'俯仰',type:'line',showSymbol:false,data:h.map(f=>f.attitude.pitch*180/Math.PI)},{name:'偏航',type:'line',showSymbol:false,data:h.map(f=>f.attitude.yaw*180/Math.PI)}]},true)
  charts[2].setOption({...base('电机输出'),xAxis:{...base('').xAxis,data:x},legend:{top:9,right:8,textStyle:{fontSize:9}},yAxis:{...base('').yAxis,min:0,max:1},series:[0,1,2,3].map(i=>({name:`M${i+1}`,type:'line',showSymbol:false,data:h.map(f=>f.motors.outputs[i])}))},true)
  charts[3].setOption({...base('剩余电量 (%)'),xAxis:{...base('').xAxis,data:x},yAxis:{...base('').yAxis,min:0,max:100},series:[{type:'line',showSymbol:false,data:h.map(f=>Math.round(f.power.battery_remaining*100))}]},true)
}

onMounted(async()=>{
  await nextTick()
  charts=[altEl,attEl,motorEl,batteryEl].map(r=>echarts.init(r.value!))
  render()
  window.addEventListener('resize',resize)
})
function resize(){charts.forEach(c=>c.resize())}
watch([()=>props.history.length,()=>props.windowSeconds],render)
onBeforeUnmount(()=>{window.removeEventListener('resize',resize);charts.forEach(c=>c.dispose())})
</script>
