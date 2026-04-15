import client from './client'

export const generateQuestions = (taskId) =>
  client.post(`/questions/generate/${taskId}`)

export const listQuestions = (taskId) =>
  client.get(`/questions/list/${taskId}`)

export const selectQuestions = (taskId, question_ids) =>
  client.post(`/questions/select/${taskId}`, { question_ids })

export const distributeQuestions = (taskId, num_per_student) =>
  client.post(`/questions/distribute/${taskId}`, { num_per_student })

export const getMyQuestions = (taskId) =>
  client.get(`/questions/my-questions/${taskId}`)
