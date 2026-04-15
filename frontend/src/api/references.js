import client from './client'

export const uploadReference = (taskId, file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/references/upload/${taskId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listReferences = (taskId) =>
  client.get(`/references/list/${taskId}`)

export const deleteReference = (referenceId) =>
  client.delete(`/references/${referenceId}`)
