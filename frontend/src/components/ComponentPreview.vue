<template>
  <div ref="host" class="component-preview">
    <div v-if="error" class="component-preview-error">{{ error }}</div>
    <div v-else-if="loading" class="component-preview-loading">正在加载 3D 资产…</div>
    <span class="component-preview-hint">拖动旋转 · 滚轮缩放</span>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import type { LibraryComponent } from '../types/componentLibrary'
import { UAV_ASSET_BASE } from '../three/assetRegistry'

const props = defineProps<{ component: LibraryComponent | null }>()
const host = ref<HTMLDivElement | null>(null)
const loading = ref(false)
const error = ref('')

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let objectRoot: THREE.Group
let animationId = 0
let generation = 0
let resizeObserver: ResizeObserver | null = null

function visualFile(component: LibraryComponent): string | null {
  const visual = component.visual
  if (!visual) return null
  return visual.file ?? visual.cw_file ?? visual.ccw_file ?? null
}

function disposeRoot(): void {
  objectRoot?.traverse(object => {
    const mesh = object as THREE.Mesh
    mesh.geometry?.dispose?.()
    const material = mesh.material
    if (Array.isArray(material)) material.forEach(item => item.dispose())
    else material?.dispose?.()
  })
  objectRoot?.clear()
}

function fitObject(): void {
  const box = new THREE.Box3().setFromObject(objectRoot)
  if (box.isEmpty()) return
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  objectRoot.position.sub(center)
  const span = Math.max(size.x, size.y, size.z, 0.08)
  const distance = Math.max(0.45, span * 2.5)
  camera.position.set(distance * 0.75, distance * 0.55, distance)
  controls.target.set(0, 0, 0)
  controls.minDistance = Math.max(span * 0.8, 0.15)
  controls.maxDistance = Math.max(span * 8, 2)
  camera.near = Math.max(0.001, span / 100)
  camera.far = Math.max(10, span * 30)
  camera.updateProjectionMatrix()
  controls.update()
}

async function loadComponent(): Promise<void> {
  const component = props.component
  if (!component || !objectRoot) return
  const file = visualFile(component)
  if (!file) {
    error.value = '该组件没有可预览的 GLB 资产。'
    disposeRoot()
    return
  }
  const current = ++generation
  loading.value = true
  error.value = ''
  disposeRoot()
  try {
    const gltf = await new GLTFLoader().loadAsync(`${UAV_ASSET_BASE}${file}`)
    if (current !== generation) return
    const model = gltf.scene
    const scale = component.visual?.scale ?? 1
    model.scale.setScalar(scale)
    model.traverse(object => {
      const mesh = object as THREE.Mesh
      if (!mesh.isMesh) return
      mesh.castShadow = true
      mesh.receiveShadow = true
    })
    objectRoot.add(model)
    fitObject()
  } catch (caught) {
    if (current !== generation) return
    error.value = caught instanceof Error ? caught.message : '3D资产加载失败'
  } finally {
    if (current === generation) loading.value = false
  }
}

function resize(): void {
  if (!host.value || !renderer || !camera) return
  const width = Math.max(1, host.value.clientWidth)
  const height = Math.max(1, host.value.clientHeight)
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function animate(): void {
  animationId = requestAnimationFrame(animate)
  controls?.update()
  renderer?.render(scene, camera)
}

onMounted(() => {
  if (!host.value) return
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf3f7fc)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x6c7f96, 1.5))
  const key = new THREE.DirectionalLight(0xffffff, 1.8)
  key.position.set(2.8, 4.2, 3.2)
  scene.add(key)
  const fill = new THREE.DirectionalLight(0xb8dcff, 0.55)
  fill.position.set(-3, 2, -2)
  scene.add(fill)

  objectRoot = new THREE.Group()
  scene.add(objectRoot)
  scene.add(new THREE.GridHelper(4, 20, 0xb9c9db, 0xdce5ef))

  camera = new THREE.PerspectiveCamera(42, 1, 0.01, 100)
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
  host.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.07
  controls.enablePan = false

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(host.value)
  resize()
  void loadComponent()
  animate()
})

watch(() => props.component?.id, () => { void loadComponent() })

onBeforeUnmount(() => {
  generation += 1
  cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  controls?.dispose()
  disposeRoot()
  renderer?.dispose()
  renderer?.domElement.remove()
})
</script>

<style scoped>
.component-preview {
  position: relative;
  width: 100%;
  height: 230px;
  overflow: hidden;
  border: 1px solid #dce6f2;
  border-radius: 10px;
  background: #f3f7fc;
}
.component-preview :deep(canvas) { display: block; width: 100%; height: 100%; }
.component-preview-loading,
.component-preview-error {
  position: absolute;
  z-index: 3;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  text-align: center;
  font-size: 11px;
  background: rgba(247, 250, 254, .88);
  color: #67778d;
}
.component-preview-error { color: #b42318; }
.component-preview-hint {
  position: absolute;
  z-index: 2;
  left: 10px;
  bottom: 8px;
  padding: 4px 7px;
  border-radius: 5px;
  background: rgba(255,255,255,.82);
  color: #718096;
  font-size: 9px;
  pointer-events: none;
}
</style>
