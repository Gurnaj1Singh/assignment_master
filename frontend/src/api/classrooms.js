import client from './client'

export const getMyClassrooms = () => client.get('/classrooms/my')

export const createClassroom = (data) => client.post('/classrooms/create', data)

export const joinClassroom = (class_code) =>
  client.post(`/classrooms/join/${class_code}`)

export const getClassroomMembers = (classroomId) =>
  client.get(`/classrooms/${classroomId}/members`)

export const getClassroomTasks = (classroomId) =>
  client.get(`/classrooms/${classroomId}/tasks`)

export const createTask = (classroomId, data) =>
  client.post(`/classrooms/${classroomId}/tasks`, data)
