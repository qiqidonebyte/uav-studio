import { api } from './client'
import type { ComponentType } from '../types/aircraft'
import type { LibraryComponent, LibraryComponentUpdate } from '../types/componentLibrary'

export async function fetchLibraryComponents(
  type?: ComponentType | null,
  search = '',
): Promise<LibraryComponent[]> {
  const response = await api.get<LibraryComponent[]>('/library/components', {
    params: {
      type: type ?? undefined,
      search: search || undefined,
    },
  })
  return response.data
}

export async function fetchLibraryComponent(id: number): Promise<LibraryComponent> {
  const response = await api.get<LibraryComponent>(`/library/components/${id}`)
  return response.data
}

export async function cloneLibraryComponent(id: number, name: string): Promise<LibraryComponent> {
  const response = await api.post<LibraryComponent>(`/library/components/${id}/clone`, { name })
  return response.data
}

export async function updateLibraryComponent(
  id: number,
  payload: LibraryComponentUpdate,
): Promise<LibraryComponent> {
  const response = await api.put<LibraryComponent>(`/library/components/${id}`, payload)
  return response.data
}
