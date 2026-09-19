import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const loader = new GLTFLoader()
const cache = new Map<string, Promise<THREE.Group>>()

function loadPrototype(url: string): Promise<THREE.Group> {
  const cached = cache.get(url)
  if (cached) return cached

  const pending = new Promise<THREE.Group>((resolve, reject) => {
    loader.load(
      url,
      gltf => resolve(gltf.scene),
      undefined,
      error => reject(error),
    )
  })
  cache.set(url, pending)
  return pending
}

function cloneMaterial(material: THREE.Material): THREE.Material {
  return material.clone()
}

export async function loadModel(url: string): Promise<THREE.Group> {
  const prototype = await loadPrototype(url)
  const clone = prototype.clone(true)
  clone.traverse(object => {
    const mesh = object as THREE.Mesh
    if (!mesh.isMesh) return
    mesh.castShadow = true
    mesh.receiveShadow = true
    if (Array.isArray(mesh.material)) mesh.material = mesh.material.map(cloneMaterial)
    else if (mesh.material) mesh.material = cloneMaterial(mesh.material)
  })
  return clone
}

export function clearModelCache(): void {
  cache.clear()
}
