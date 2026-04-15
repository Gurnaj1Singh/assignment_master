import client from './client'

export const submitAssignment = (taskId, file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/assignments/submit/${taskId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadTaskPdf = (taskId, file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/assignments/task-pdf/${taskId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getTaskDetail = (taskId) =>
  client.get(`/assignments/task/${taskId}`)

export const publishTask = (taskId, is_published) =>
  client.patch(`/assignments/task/${taskId}/publish`, { is_published })

export const getReport = (taskId) => client.get(`/assignments/report/${taskId}`)

export const getHeatmap = (taskId) => client.get(`/assignments/heatmap/${taskId}`)

export const getSimilarityMatrix = (taskId) =>
  client.get(`/assignments/matrix/${taskId}`)

export const getSubmissionStatus = (taskId) =>
  client.get(`/assignments/status/${taskId}`)

export const getCollusionGroups = (taskId) =>
  client.get(`/assignments/collusion-groups/${taskId}`)

export const getSubmissionDetail = (submissionId) =>
  client.get(`/assignments/submission-detail/${submissionId}`)

export const getMySubmissions = () => client.get('/assignments/my-submissions')
