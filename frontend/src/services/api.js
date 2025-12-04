import axios from 'axios'

// Dynamic API URL - automatically uses the same host as the frontend
// This allows access from any network/IP
const getApiBaseUrl = () => {
    // If environment variable is set, use it (for development)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL
    }

    // In production, use the same host that user is accessing
    // This works for localhost, private IP (172.29.61.56), or public domain
    const protocol = window.location.protocol // http: or https:
    const hostname = window.location.hostname  // e.g., 172.29.61.56 or yourdomain.com

    return `${protocol}//${hostname}:5000/api`
}

const API_BASE_URL = getApiBaseUrl()

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.reload()
        }
        return Promise.reject(error)
    }
)

// Auth APIs
export const authAPI = {
    login: (teacherId, password) =>
        api.post('/login', { teacher_id: teacherId, password }),
    getMe: () => api.get('/me')
}

// Data APIs
export const dataAPI = {
    // GET
    getTeachers: () => api.get('/teachers'),
    getSubjects: () => api.get('/subjects'),
    getRooms: () => api.get('/rooms'),
    getGroups: () => api.get('/groups'),
    getTimeslots: () => api.get('/timeslots'),
    getStats: () => api.get('/stats'),
    getRegister: () => api.get('/register'),
    getTeach: () => api.get('/teach'),

    // Teachers CRUD
    addTeacher: (data) => api.post('/teachers', data),
    updateTeacher: (id, data) => api.put(`/teachers/${id}`, data),
    deleteTeacher: (id) => api.delete(`/teachers/${id}`),

    // Subjects CRUD
    addSubject: (data) => api.post('/subjects', data),
    updateSubject: (id, data) => api.put(`/subjects/${id}`, data),
    deleteSubject: (id) => api.delete(`/subjects/${id}`),

    // Rooms CRUD
    addRoom: (data) => api.post('/rooms', data),
    updateRoom: (id, data) => api.put(`/rooms/${id}`, data),
    deleteRoom: (id) => api.delete(`/rooms/${id}`),

    // Groups CRUD
    addGroup: (data) => api.post('/groups', data),
    updateGroup: (id, data) => api.put(`/groups/${id}`, data),
    deleteGroup: (id) => api.delete(`/groups/${id}`),

    // Register CRUD
    addRegister: (data) => api.post('/register', data),
    deleteRegister: (data) => api.delete('/register', { data }),

    // Teach CRUD
    addTeach: (data) => api.post('/teach', data),
    deleteTeach: (data) => api.delete('/teach', { data })
}

// Timetable APIs
export const timetableAPI = {
    getAll: () => api.get('/timetable'),
    getByGroup: (groupId) => api.get(`/timetable/group/${groupId}`),
    getByTeacher: (teacherId) => api.get(`/timetable/teacher/${teacherId}`),
    getByRoom: (roomId) => api.get(`/timetable/room/${roomId}`)
}

// Scheduling APIs
export const scheduleAPI = {
    run: () => api.post('/schedule/run'),
    runSync: () => api.post('/schedule/run-sync'),
    getStatus: () => api.get('/schedule/status')
}

export default api
