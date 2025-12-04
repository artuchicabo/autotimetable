<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { authAPI, dataAPI, timetableAPI, scheduleAPI } from './services/api.js'

// ===== State =====
const isLoggedIn = ref(false)
const currentUser = ref(null)
const isLoading = ref(false)
const error = ref('')
const success = ref('')

// Navigation
const currentPage = ref('timetable')

// Login form
const loginForm = ref({ teacherId: '', password: '' })

// Dashboard data
const groups = ref([])
const teachers = ref([])
const rooms = ref([])
const subjects = ref([])
const timeslots = ref([])
const stats = ref({})
const registerList = ref([])
const teachList = ref([])

// Timetable view
const viewMode = ref('group')
const selectedId = ref('')
const timetableData = ref([])
const fitnessScore = ref(null)

// Scheduling
const isScheduling = ref(false)
const scheduleProgress = ref(0)
const scheduleMessage = ref('')

// Data Management
const activeDataTab = ref('teachers')
const showAddModal = ref(false)
const isEditMode = ref(false)
const editingItemId = ref(null)
const newItemForm = ref({})

// ===== Computed =====
const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
const dayLabels = { 'Mon': 'จันทร์', 'Tue': 'อังคาร', 'Wed': 'พุธ', 'Thu': 'พฤหัส', 'Fri': 'ศุกร์' }
// Neon Punk Colors
const dayColors = { 
  'Mon': '#ff0055', // Neon Pink
  'Tue': '#ffea00', // Neon Yellow
  'Wed': '#00f3ff', // Neon Cyan
  'Thu': '#ff9900', // Neon Orange
  'Fri': '#cc00ff'  // Neon Purple
}
const periods = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
const periodTimes = {
  1: '08:00-08:50', 2: '09:00-09:50', 3: '10:00-10:50', 4: '11:00-11:50',
  5: 'พักเที่ยง', 6: '13:00-13:50', 7: '14:00-14:50', 8: '15:00-15:50', 9: '16:00-16:50', 10: '17:00-17:50'
}

const isAdmin = computed(() => currentUser.value?.role === 'admin')

// Group timetable by day
const timetableByDay = computed(() => {
  const result = {}
  days.forEach(day => {
    result[day] = []
    for (let p = 1; p <= 10; p++) {
      const entry = timetableData.value.find(e => e.day === day && parseInt(e.period) === p)
      result[day].push(entry || null)
    }
  })
  return result
})

const selectOptions = computed(() => {
  if (viewMode.value === 'group') return groups.value.map(g => ({ id: g.group_id, name: g.group_name }))
  if (viewMode.value === 'teacher') return teachers.value.map(t => ({ id: t.teacher_id, name: t.teacher_name }))
  return rooms.value.map(r => ({ id: r.room_id, name: r.room_name }))
})

// ===== Methods =====
const checkAuth = () => {
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')
  if (token && user) {
    isLoggedIn.value = true
    currentUser.value = JSON.parse(user)
  }
}

const login = async () => {
  error.value = ''
  isLoading.value = true
  try {
    const res = await authAPI.login(loginForm.value.teacherId, loginForm.value.password)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    currentUser.value = res.data.user
    isLoggedIn.value = true
    await loadDashboardData()
  } catch (err) {
    error.value = err.response?.data?.status === 'USER_NOT_FOUND' ? 'ไม่พบผู้ใช้งาน' 
      : err.response?.data?.status === 'WRONG_PASSWORD' ? 'รหัสผ่านไม่ถูกต้อง' : 'เกิดข้อผิดพลาด'
  } finally {
    isLoading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  isLoggedIn.value = false
  currentUser.value = null
}

const loadDashboardData = async () => {
  isLoading.value = true
  try {
    const [groupsRes, teachersRes, roomsRes, subjectsRes, timeslotsRes, statsRes] = await Promise.all([
      dataAPI.getGroups(), dataAPI.getTeachers(), dataAPI.getRooms(),
      dataAPI.getSubjects(), dataAPI.getTimeslots(), dataAPI.getStats()
    ])
    groups.value = groupsRes.data
    teachers.value = teachersRes.data
    rooms.value = roomsRes.data
    subjects.value = subjectsRes.data
    timeslots.value = timeslotsRes.data
    stats.value = statsRes.data
    
    if (groups.value.length > 0 && !selectedId.value) selectedId.value = groups.value[0].group_id
    
    try {
      const [regRes, teachRes] = await Promise.all([dataAPI.getRegister(), dataAPI.getTeach()])
      registerList.value = regRes.data
      teachList.value = teachRes.data
    } catch (e) { console.error('Failed to load register/teach', e) }
    
    // Load fitness score if available
    try {
      const statusRes = await scheduleAPI.getStatus()
      if (statusRes.data.result && statusRes.data.result.fitness_score) {
        fitnessScore.value = statusRes.data.result.fitness_score
      }
    } catch (e) {}
    
  } catch (err) {
    error.value = 'ไม่สามารถโหลดข้อมูลได้'
  } finally {
    isLoading.value = false
  }
}

const loadTimetable = async () => {
  if (!selectedId.value) return
  isLoading.value = true
  error.value = ''
  try {
    let res
    if (viewMode.value === 'group') res = await timetableAPI.getByGroup(selectedId.value)
    else if (viewMode.value === 'teacher') res = await timetableAPI.getByTeacher(selectedId.value)
    else res = await timetableAPI.getByRoom(selectedId.value)
    timetableData.value = res.data || []
  } catch (err) {
    error.value = 'ไม่สามารถโหลดตารางได้'
    timetableData.value = []
  } finally {
    isLoading.value = false
  }
}

const runScheduling = async () => {
  if (isScheduling.value) return
  error.value = ''
  success.value = ''
  isScheduling.value = true
  scheduleProgress.value = 0
  scheduleMessage.value = 'กำลังเริ่มต้น...'
  
  try {
    await scheduleAPI.run()
    const pollStatus = async () => {
      try {
        const res = await scheduleAPI.getStatus()
        scheduleProgress.value = res.data.progress || 0
        scheduleMessage.value = res.data.message || ''
        
        if (res.data.running) setTimeout(pollStatus, 500)
        else {
          isScheduling.value = false
          if (res.data.result) {
            success.value = `สร้างตารางสำเร็จ! (${res.data.result.total_slots} คาบ)`
            fitnessScore.value = res.data.result.fitness_score
            await loadTimetable()
            await loadDashboardData()
          } else error.value = res.data.error || res.data.message || 'ไม่สามารถสร้างตารางได้'
        }
      } catch (e) { isScheduling.value = false; error.value = 'ไม่สามารถตรวจสอบสถานะได้' }
    }
    setTimeout(pollStatus, 500)
  } catch (err) { isScheduling.value = false; error.value = err.response?.data?.message || 'เกิดข้อผิดพลาด' }
}

const exportExcel = () => {
  window.open('autotimetable-backend-production.up.railway.app/api/export/excel', '_blank')
}

const printTimetable = () => {
  window.print()
}

// Data Management
const openAddModal = (type) => { 
  activeDataTab.value = type
  newItemForm.value = {}
  isEditMode.value = false
  editingItemId.value = null
  showAddModal.value = true
}

const openEditModal = (type, item) => {
  activeDataTab.value = type
  isEditMode.value = true
  
  // Copy item data to form based on type
  if (type === 'teachers') {
    editingItemId.value = item.teacher_id
    newItemForm.value = { ...item }
  } else if (type === 'subjects') {
    editingItemId.value = item.subject_id
    newItemForm.value = { ...item }
  } else if (type === 'rooms') {
    editingItemId.value = item.room_id
    newItemForm.value = { ...item }
  } else if (type === 'groups') {
    editingItemId.value = item.group_id
    newItemForm.value = { ...item }
  }
  
  showAddModal.value = true
}

const closeModal = () => { 
  showAddModal.value = false
  isEditMode.value = false
  editingItemId.value = null
  newItemForm.value = {}
}

const addItem = async () => {
  isLoading.value = true
  error.value = ''
  try {
    const actions = {
      teachers: () => dataAPI.addTeacher(newItemForm.value),
      subjects: () => dataAPI.addSubject(newItemForm.value),
      rooms: () => dataAPI.addRoom(newItemForm.value),
      groups: () => dataAPI.addGroup(newItemForm.value),
      register: () => dataAPI.addRegister(newItemForm.value),
      teach: () => dataAPI.addTeach(newItemForm.value)
    }
    await actions[activeDataTab.value]()
    success.value = 'เพิ่มข้อมูลสำเร็จ'
    closeModal()
    await loadDashboardData()
  } catch (err) { error.value = err.response?.data?.error || 'เกิดข้อผิดพลาด' }
  finally { isLoading.value = false }
}

const updateItem = async () => {
  isLoading.value = true
  error.value = ''
  try {
    const actions = {
      teachers: () => dataAPI.updateTeacher(editingItemId.value, newItemForm.value),
      subjects: () => dataAPI.updateSubject(editingItemId.value, newItemForm.value),
      rooms: () => dataAPI.updateRoom(editingItemId.value, newItemForm.value),
      groups: () => dataAPI.updateGroup(editingItemId.value, newItemForm.value)
    }
    await actions[activeDataTab.value]()
    success.value = 'แก้ไขข้อมูลสำเร็จ'
    closeModal()
    await loadDashboardData()
  } catch (err) { error.value = err.response?.data?.error || 'เกิดข้อผิดพลาด' }
  finally { isLoading.value = false }
}

const saveItem = async () => {
  if (isEditMode.value) {
    await updateItem()
  } else {
    await addItem()
  }
}

const deleteItem = async (type, id, id2 = null) => {
  if (!confirm('ต้องการลบข้อมูลนี้?')) return
  isLoading.value = true
  try {
    const actions = {
      teachers: () => dataAPI.deleteTeacher(id),
      subjects: () => dataAPI.deleteSubject(id),
      rooms: () => dataAPI.deleteRoom(id),
      groups: () => dataAPI.deleteGroup(id),
      register: () => dataAPI.deleteRegister({ group_id: id, subject_id: id2 }),
      teach: () => dataAPI.deleteTeach({ teacher_id: id, subject_id: id2 })
    }
    await actions[type]()
    success.value = 'ลบข้อมูลสำเร็จ'
    await loadDashboardData()
  } catch (err) { error.value = err.response?.data?.error || 'เกิดข้อผิดพลาด' }
  finally { isLoading.value = false }
}

// Watchers
watch([viewMode, selectedId], () => { if (selectedId.value) loadTimetable() })
watch(viewMode, () => { const opts = selectOptions.value; if (opts.length > 0) selectedId.value = opts[0].id })

onMounted(() => { checkAuth(); if (isLoggedIn.value) loadDashboardData() })
</script>

<template>
  <!-- Login -->
  <div v-if="!isLoggedIn" class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">📅</div>
        <h1>AutoTimetable</h1>
        <p>ระบบจัดตารางเรียนอัตโนมัติ</p>
      </div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <form @submit.prevent="login">
        <div class="form-group">
          <label>รหัสครู</label>
          <input v-model="loginForm.teacherId" type="text" placeholder="เช่น T01" required />
        </div>
        <div class="form-group">
          <label>รหัสผ่าน</label>
          <input v-model="loginForm.password" type="password" placeholder="รหัสผ่าน" required />
        </div>
        <button type="submit" class="btn-login" :disabled="isLoading">
          {{ isLoading ? 'กำลังเข้าสู่ระบบ...' : 'เข้าสู่ระบบ' }}
        </button>
      </form>
      <p class="login-hint">Admin: T01 / 12345 | Teacher: T02 / 12345</p>
    </div>
  </div>

  <!-- Dashboard -->
  <div v-else class="app-container">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="logo">📅</span>
        <span class="logo-text">AutoTimetable</span>
      </div>
      <nav class="sidebar-nav">
        <a :class="['nav-item', { active: currentPage === 'timetable' }]" @click="currentPage = 'timetable'">
          <span class="nav-icon">📊</span> ตารางเรียน
        </a>
        <a v-if="isAdmin" :class="['nav-item', { active: currentPage === 'data' }]" @click="currentPage = 'data'">
          <span class="nav-icon">📝</span> จัดการข้อมูล
        </a>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <span class="user-name">{{ currentUser?.teacher_name }}</span>
          <span v-if="isAdmin" class="user-role">Admin</span>
        </div>
        <button class="btn-logout" @click="logout">ออกจากระบบ</button>
      </div>
    </aside>

    <!-- Main -->
    <main class="main-content">
      <!-- Alerts -->
      <div v-if="error" class="alert alert-error">{{ error }} <button @click="error=''">×</button></div>
      <div v-if="success" class="alert alert-success">{{ success }} <button @click="success=''">×</button></div>

      <!-- TIMETABLE PAGE -->
      <div v-if="currentPage === 'timetable'">
        <!-- Stats Row -->
        <div class="stats-row">
          <div class="stat-item"><span class="stat-num">{{ stats.groups || 0 }}</span><span class="stat-label">กลุ่มเรียน</span></div>
          <div class="stat-item"><span class="stat-num">{{ stats.teachers || 0 }}</span><span class="stat-label">ครู</span></div>
          <div class="stat-item"><span class="stat-num">{{ stats.subjects || 0 }}</span><span class="stat-label">วิชา</span></div>
          <div class="stat-item"><span class="stat-num">{{ stats.timetable_entries || 0 }}</span><span class="stat-label">คาบในตาราง</span></div>
        </div>

        <!-- Progress -->
        <div v-if="isScheduling" class="progress-card">
          <h3>🤖 กำลังสร้างตารางด้วย AI...</h3>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" :style="{ width: scheduleProgress + '%' }"></div>
          </div>
          <p>{{ scheduleMessage }} ({{ scheduleProgress }}%)</p>
        </div>

        <!-- Controls -->
        <div class="controls-row">
          <div class="control-group">
            <label>ดูตาราง:</label>
            <select v-model="viewMode">
              <option value="group">กลุ่มเรียน</option>
              <option value="teacher">ครู</option>
              <option value="room">ห้อง</option>
            </select>
          </div>
          <div class="control-group">
            <label>เลือก:</label>
            <select v-model="selectedId">
              <option v-for="opt in selectOptions" :key="opt.id" :value="opt.id">{{ opt.name }}</option>
            </select>
          </div>
          <button class="btn btn-secondary" @click="loadTimetable" :disabled="isLoading">🔄 รีเฟรช</button>
          <button v-if="isAdmin" class="btn btn-primary" @click="runScheduling" :disabled="isScheduling">
            {{ isScheduling ? 'กำลังทำงาน...' : '🤖 สร้างตารางใหม่' }}
          </button>
        </div>

        <!-- THAI GOVERNMENT TIMETABLE LAYOUT -->
        <div class="timetable-header">
          <h2>📅 ตารางสอน: {{ selectOptions.find(o => o.id === selectedId)?.name || '-' }}</h2>
          <span class="timetable-badge">{{ timetableData.length }} คาบ</span>
          
          <div v-if="fitnessScore !== null" class="fitness-score">
            <span>⚡ Fitness: {{ fitnessScore }}</span>
          </div>
          
          <div class="export-actions">
            <button class="btn-export" @click="exportExcel">
              📊 Excel
            </button>
            <button class="btn-export" @click="printTimetable">
              🖨️ PDF / Print
            </button>
          </div>
        </div>

        <div class="gov-timetable-wrapper">
          <table class="gov-table">
            <thead>
              <tr>
                <th class="th-day">วัน / เวลา</th>
                <th v-for="p in periods" :key="p" class="th-period">
                  <div class="th-p-num">คาบที่ {{ p }}</div>
                  <div class="th-p-time">{{ periodTimes[p] }}</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in days" :key="day">
                <td class="td-day" :style="{ backgroundColor: dayColors[day] }">
                  {{ dayLabels[day] }}
                </td>
                <td v-for="p in periods" :key="p" :class="['td-slot', { 'lunch-break': p === 5 }]">
                  <div v-if="p === 5" class="lunch-label">พัก<br>เที่ยง</div>
                  <div v-else-if="timetableByDay[day][p - 1]" class="class-content">
                    <div class="subj-code">{{ timetableByDay[day][p - 1].subject_id }}</div>
                    <div class="subj-name">{{ timetableByDay[day][p - 1].subject_name }}</div>
                    <div class="class-detail">
                      <span class="teacher-name">{{ timetableByDay[day][p - 1].teacher_name || timetableByDay[day][p - 1].teacher_id }}</span>
                      <span class="room-name">{{ timetableByDay[day][p - 1].room_name || timetableByDay[day][p - 1].room_id }}</span>
                    </div>
                  </div>
                  <div v-else class="empty-slot"></div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- DATA PAGE -->
      <div v-if="currentPage === 'data' && isAdmin">
        <div class="data-tabs">
          <button v-for="tab in ['teachers', 'subjects', 'rooms', 'groups', 'teach', 'register']" 
                  :key="tab" :class="['tab', { active: activeDataTab === tab }]" @click="activeDataTab = tab">
            {{ {teachers:'ครู',subjects:'วิชา',rooms:'ห้อง',groups:'กลุ่ม',teach:'ครู-วิชา',register:'ลงทะเบียน'}[tab] }}
          </button>
        </div>

        <div class="data-card">
          <div class="data-header">
            <h3>{{ {teachers:'ครูผู้สอน',subjects:'วิชาเรียน',rooms:'ห้องเรียน',groups:'กลุ่มเรียน',teach:'ครู-วิชา',register:'ลงทะเบียน'}[activeDataTab] }}</h3>
            <button class="btn btn-primary" @click="openAddModal(activeDataTab)">+ เพิ่ม</button>
          </div>

          <!-- Teachers -->
          <table v-if="activeDataTab === 'teachers'" class="data-table">
            <thead><tr><th>รหัส</th><th>ชื่อ</th><th>Role</th><th>จัดการ</th></tr></thead>
            <tbody>
              <tr v-for="t in teachers" :key="t.teacher_id">
                <td>{{ t.teacher_id }}</td><td>{{ t.teacher_name }}</td>
                <td><span :class="['role-badge', t.role]">{{ t.role }}</span></td>
                <td class="action-cell">
                  <button class="btn-edit" @click="openEditModal('teachers', t)">แก้ไข</button>
                  <button class="btn-delete" @click="deleteItem('teachers', t.teacher_id)">ลบ</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Subjects -->
          <table v-if="activeDataTab === 'subjects'" class="data-table">
            <thead><tr><th>รหัส</th><th>ชื่อวิชา</th><th>ทฤษฎี</th><th>ปฏิบัติ</th><th>หน่วยกิต</th><th>จัดการ</th></tr></thead>
            <tbody>
              <tr v-for="s in subjects" :key="s.subject_id">
                <td>{{ s.subject_id }}</td><td>{{ s.subject_name }}</td>
                <td>{{ s.theory }}</td><td>{{ s.practice }}</td><td>{{ s.credit }}</td>
                <td class="action-cell">
                  <button class="btn-edit" @click="openEditModal('subjects', s)">แก้ไข</button>
                  <button class="btn-delete" @click="deleteItem('subjects', s.subject_id)">ลบ</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Rooms -->
          <table v-if="activeDataTab === 'rooms'" class="data-table">
            <thead><tr><th>รหัส</th><th>ชื่อห้อง</th><th>จัดการ</th></tr></thead>
            <tbody>
              <tr v-for="r in rooms" :key="r.room_id">
                <td>{{ r.room_id }}</td><td>{{ r.room_name }}</td>
                <td class="action-cell">
                  <button class="btn-edit" @click="openEditModal('rooms', r)">แก้ไข</button>
                  <button class="btn-delete" @click="deleteItem('rooms', r.room_id)">ลบ</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Groups -->
          <table v-if="activeDataTab === 'groups'" class="data-table">
            <thead><tr><th>รหัส</th><th>ชื่อกลุ่ม</th><th>จำนวน</th><th>จัดการ</th></tr></thead>
            <tbody>
              <tr v-for="g in groups" :key="g.group_id">
                <td>{{ g.group_id }}</td><td>{{ g.group_name }}</td><td>{{ g.student_count }}</td>
                <td class="action-cell">
                  <button class="btn-edit" @click="openEditModal('groups', g)">แก้ไข</button>
                  <button class="btn-delete" @click="deleteItem('groups', g.group_id)">ลบ</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Teach -->
          <table v-if="activeDataTab === 'teach'" class="data-table">
            <thead><tr><th>ครู</th><th>วิชา</th><th></th></tr></thead>
            <tbody>
              <tr v-for="(t, idx) in teachList" :key="idx">
                <td>{{ t.teacher_id }}</td><td>{{ t.subject_id }}</td>
                <td><button class="btn-delete" @click="deleteItem('teach', t.teacher_id, t.subject_id)">ลบ</button></td>
              </tr>
            </tbody>
          </table>

          <!-- Register -->
          <table v-if="activeDataTab === 'register'" class="data-table">
            <thead><tr><th>กลุ่ม</th><th>วิชา</th><th></th></tr></thead>
            <tbody>
              <tr v-for="(r, idx) in registerList" :key="idx">
                <td>{{ r.group_id }}</td><td>{{ r.subject_id }}</td>
                <td><button class="btn-delete" @click="deleteItem('register', r.group_id, r.subject_id)">ลบ</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>

  <!-- Modal -->
  <div v-if="showAddModal" class="modal-backdrop" @click.self="closeModal">
    <div class="modal">
      <div class="modal-header"><h3>{{ isEditMode ? 'แก้ไขข้อมูล' : 'เพิ่มข้อมูล' }}</h3><button @click="closeModal">×</button></div>
      <div class="modal-body">
        <!-- Teachers -->
        <template v-if="activeDataTab === 'teachers'">
          <div class="form-group"><label>รหัสครู</label><input v-model="newItemForm.teacher_id" placeholder="T20" :disabled="isEditMode" /></div>
          <div class="form-group"><label>ชื่อครู</label><input v-model="newItemForm.teacher_name" /></div>
          <div class="form-group" v-if="!isEditMode"><label>รหัสผ่าน</label><input v-model="newItemForm.password" placeholder="12345" /></div>
          <div class="form-group"><label>Role</label><select v-model="newItemForm.role"><option value="teacher">Teacher</option><option value="admin">Admin</option></select></div>
        </template>
        <!-- Subjects -->
        <template v-if="activeDataTab === 'subjects'">
          <div class="form-group"><label>รหัสวิชา</label><input v-model="newItemForm.subject_id" :disabled="isEditMode" /></div>
          <div class="form-group"><label>ชื่อวิชา</label><input v-model="newItemForm.subject_name" /></div>
          <div class="form-group"><label>ทฤษฎี</label><input v-model.number="newItemForm.theory" type="number" /></div>
          <div class="form-group"><label>ปฏิบัติ</label><input v-model.number="newItemForm.practice" type="number" /></div>
          <div class="form-group"><label>หน่วยกิต</label><input v-model.number="newItemForm.credit" type="number" /></div>
        </template>
        <!-- Rooms -->
        <template v-if="activeDataTab === 'rooms'">
          <div class="form-group"><label>รหัสห้อง</label><input v-model="newItemForm.room_id" placeholder="R101" :disabled="isEditMode" /></div>
          <div class="form-group"><label>ชื่อห้อง</label><input v-model="newItemForm.room_name" /></div>
        </template>
        <!-- Groups -->
        <template v-if="activeDataTab === 'groups'">
          <div class="form-group"><label>รหัสกลุ่ม</label><input v-model="newItemForm.group_id" placeholder="G8" :disabled="isEditMode" /></div>
          <div class="form-group"><label>ชื่อกลุ่ม</label><input v-model="newItemForm.group_name" /></div>
          <div class="form-group"><label>จำนวนนักเรียน</label><input v-model.number="newItemForm.student_count" type="number" /></div>
        </template>
        <!-- Teach -->
        <template v-if="activeDataTab === 'teach'">
          <div class="form-group"><label>ครู</label><select v-model="newItemForm.teacher_id"><option v-for="t in teachers" :key="t.teacher_id" :value="t.teacher_id">{{ t.teacher_id }} - {{ t.teacher_name }}</option></select></div>
          <div class="form-group"><label>วิชา</label><select v-model="newItemForm.subject_id"><option v-for="s in subjects" :key="s.subject_id" :value="s.subject_id">{{ s.subject_id }} - {{ s.subject_name }}</option></select></div>
        </template>
        <!-- Register -->
        <template v-if="activeDataTab === 'register'">
          <div class="form-group"><label>กลุ่มเรียน</label><select v-model="newItemForm.group_id"><option v-for="g in groups" :key="g.group_id" :value="g.group_id">{{ g.group_id }} - {{ g.group_name }}</option></select></div>
          <div class="form-group"><label>วิชา</label><select v-model="newItemForm.subject_id"><option v-for="s in subjects" :key="s.subject_id" :value="s.subject_id">{{ s.subject_id }} - {{ s.subject_name }}</option></select></div>
        </template>
        <button class="btn btn-primary w-full" @click="saveItem" :disabled="isLoading">{{ isLoading ? 'กำลังบันทึก...' : 'บันทึก' }}</button>
      </div>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  /* Aurora Theme - Premium Gradient Colors */
  --primary: #6366f1;           /* Indigo */
  --primary-dark: #4f46e5;
  --primary-light: #818cf8;
  --primary-glow: rgba(99, 102, 241, 0.4);
  
  --accent: #06b6d4;            /* Cyan */
  --accent-glow: rgba(6, 182, 212, 0.4);
  
  --success: #10b981;           /* Emerald */
  --warning: #f59e0b;           /* Amber */
  --error: #ef4444;             /* Red */
  
  /* Aurora Gradient */
  --aurora-1: #6366f1;
  --aurora-2: #8b5cf6;
  --aurora-3: #a855f7;
  --aurora-4: #06b6d4;
  
  /* Dark Mode Aurora */
  --bg-dark: #0f0f23;
  --bg-darker: #080816;
  --bg-card: rgba(255, 255, 255, 0.03);
  --bg-card-hover: rgba(255, 255, 255, 0.06);
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  
  --border-color: rgba(255, 255, 255, 0.08);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body { 
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-darker);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}

/* Aurora Background Effect */
.login-page::before,
.app-container::before {
  content: '';
  position: fixed;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: 
    radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
  animation: aurora 20s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes aurora {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(2%, 2%) rotate(1deg); }
  66% { transform: translate(-1%, 1%) rotate(-1deg); }
}

/* ===== LOGIN PAGE ===== */
.login-page { 
  min-height: 100vh; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: var(--bg-darker);
  position: relative;
  overflow: hidden;
}

.login-card { 
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 48px; 
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  width: 100%; 
  max-width: 420px;
  position: relative;
  z-index: 1;
}

.login-header { text-align: center; margin-bottom: 36px; }
.login-icon { 
  font-size: 56px; 
  margin-bottom: 16px; 
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.login-header h1 { 
  font-size: 28px; 
  font-weight: 700;
  background: linear-gradient(135deg, var(--aurora-1), var(--aurora-2), var(--aurora-4));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}
.login-header p { color: var(--text-secondary); font-size: 14px; }

.login-card .form-group { margin-bottom: 24px; }
.login-card label { 
  display: block; 
  margin-bottom: 8px; 
  font-weight: 500; 
  color: var(--text-secondary); 
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.login-card input { 
  width: 100%; 
  padding: 14px 16px; 
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-primary);
  font-size: 15px;
  transition: all 0.3s ease;
}
.login-card input::placeholder { color: var(--text-muted); }
.login-card input:focus { 
  outline: none; 
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-glow);
  background: rgba(0, 0, 0, 0.4);
}

.btn-login { 
  width: 100%; 
  padding: 16px; 
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white; 
  border: none; 
  border-radius: 12px;
  font-size: 15px; 
  font-weight: 600; 
  cursor: pointer; 
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px -4px var(--primary-glow);
}
.btn-login:hover { 
  transform: translateY(-2px);
  box-shadow: 0 8px 30px -4px var(--primary-glow);
}
.btn-login:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.login-hint { 
  text-align: center; 
  margin-top: 24px; 
  font-size: 12px; 
  color: var(--text-muted);
  padding: 12px;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
}

/* ===== LAYOUT ===== */
.app-container { 
  display: flex; 
  min-height: 100vh;
  position: relative;
}

/* Sidebar */
.sidebar { 
  width: 260px; 
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex; 
  flex-direction: column; 
  border-right: 1px solid var(--glass-border);
  position: relative;
  z-index: 10;
}

.sidebar-header { 
  padding: 24px; 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  border-bottom: 1px solid var(--border-color);
}
.logo { font-size: 32px; }
.logo-text { 
  font-size: 18px; 
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-nav { flex: 1; padding: 16px 12px; }
.nav-item { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  padding: 14px 16px; 
  color: var(--text-secondary); 
  cursor: pointer; 
  transition: all 0.2s ease;
  text-decoration: none; 
  font-weight: 500;
  font-size: 14px;
  border-radius: 12px;
  margin-bottom: 4px;
}
.nav-item:hover { 
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.nav-item.active { 
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white;
  box-shadow: 0 4px 15px -4px var(--primary-glow);
}
.nav-icon { font-size: 18px; }

.sidebar-footer { 
  padding: 20px; 
  border-top: 1px solid var(--border-color);
  background: rgba(0,0,0,0.2);
}
.user-info { margin-bottom: 12px; }
.user-name { 
  display: block; 
  font-weight: 600; 
  color: var(--text-primary);
  font-size: 14px;
}
.user-role { 
  font-size: 11px; 
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.btn-logout { 
  width: 100%; 
  padding: 10px; 
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #f87171;
  cursor: pointer; 
  transition: all 0.2s;
  font-weight: 500;
  font-size: 13px;
}
.btn-logout:hover { 
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
}

/* Main Content */
.main-content { 
  flex: 1; 
  padding: 32px; 
  overflow-y: auto; 
  position: relative;
  z-index: 1;
}

/* ===== ALERTS ===== */
.alert { 
  padding: 16px 20px; 
  margin-bottom: 20px; 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  border-radius: 12px;
  font-weight: 500;
  font-size: 14px;
  backdrop-filter: blur(10px);
}
.alert button { 
  background: none; 
  border: none; 
  font-size: 20px; 
  cursor: pointer; 
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.alert button:hover { opacity: 1; }
.alert-error { 
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}
.alert-success { 
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #6ee7b7;
}

/* ===== STATS ===== */
.stats-row { 
  display: grid; 
  grid-template-columns: repeat(4, 1fr); 
  gap: 20px; 
  margin-bottom: 28px;
}
.stat-item { 
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 16px;
  border: 1px solid var(--glass-border);
  text-align: center;
  transition: all 0.3s ease;
}
.stat-item:hover { 
  transform: translateY(-4px);
  border-color: var(--primary);
  box-shadow: 0 12px 40px -12px var(--primary-glow);
}
.stat-num { 
  display: block; 
  font-size: 36px; 
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.stat-label { 
  color: var(--text-secondary); 
  font-size: 13px; 
  margin-top: 8px;
  font-weight: 500;
}

/* ===== PROGRESS ===== */
.progress-card { 
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  padding: 28px;
  border-radius: 16px;
  border: 1px solid var(--primary);
  margin-bottom: 28px;
  box-shadow: 0 0 40px -10px var(--primary-glow);
}
.progress-card h3 { 
  margin-bottom: 16px; 
  color: var(--text-primary);
  font-weight: 600;
  font-size: 16px;
}
.progress-bar-container { 
  height: 8px; 
  background: rgba(255,255,255,0.1);
  border-radius: 100px;
  margin-bottom: 12px;
  overflow: hidden;
}
.progress-bar-fill { 
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--aurora-2), var(--accent));
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
  border-radius: 100px;
  transition: width 0.3s ease;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.progress-card p { color: var(--text-secondary); font-size: 13px; }

/* ===== CONTROLS ===== */
.controls-row { 
  display: flex; 
  gap: 16px; 
  align-items: center; 
  flex-wrap: wrap; 
  margin-bottom: 28px;
  padding: 20px 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid var(--glass-border);
}
.control-group { display: flex; align-items: center; gap: 10px; }
.control-group label { 
  font-weight: 500; 
  color: var(--text-secondary);
  font-size: 13px;
}
.control-group select { 
  padding: 10px 16px;
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  font-size: 14px;
  min-width: 160px;
  background: rgba(0,0,0,0.3);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}
.control-group select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.btn { 
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-primary { 
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white;
  box-shadow: 0 4px 15px -4px var(--primary-glow);
}
.btn-primary:hover { 
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -4px var(--primary-glow);
}
.btn-secondary { 
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--glass-border);
}
.btn-secondary:hover { 
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

/* ===== TIMETABLE HEADER ===== */
.timetable-header { 
  display: flex; 
  align-items: center; 
  gap: 16px; 
  margin-bottom: 24px;
  padding: 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid var(--glass-border);
}
.timetable-header h2 { 
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.timetable-badge { 
  font-size: 12px;
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white;
  padding: 6px 14px;
  border-radius: 100px;
  font-weight: 600;
}

.fitness-score {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
  color: var(--warning);
  background: rgba(245, 158, 11, 0.15);
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid rgba(245, 158, 11, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-actions { display: flex; gap: 10px; margin-left: 16px; }
.btn-export {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--bg-card);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 500;
  font-size: 13px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-export:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

/* ===== TIMETABLE ===== */
.gov-timetable-wrapper {
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  overflow-x: auto;
}

.gov-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 4px;
  min-width: 1000px;
}

.gov-table th, .gov-table td {
  text-align: center;
  vertical-align: middle;
}

.th-day {
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white;
  font-weight: 600;
  width: 100px;
  padding: 12px;
  font-size: 13px;
  border-radius: 10px;
}

.th-period {
  background: rgba(255,255,255,0.05);
  padding: 10px;
  min-width: 85px;
  border-radius: 10px;
}

.th-p-num {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.th-p-time {
  font-size: 10px;
  color: var(--text-muted);
}

/* Day Colors - Soft Gradients */
.td-day {
  font-weight: 700;
  font-size: 14px;
  padding: 12px;
  border-radius: 10px;
  color: white;
}

.td-slot {
  height: 95px;
  padding: 6px;
  background: rgba(255,255,255,0.02);
  border-radius: 10px;
  transition: all 0.2s;
}

.td-slot:hover {
  background: rgba(255,255,255,0.05);
}

.lunch-break {
  background: rgba(245, 158, 11, 0.1);
  border: 1px dashed rgba(245, 158, 11, 0.3);
}

.lunch-label {
  writing-mode: vertical-rl;
  text-orientation: upright;
  margin: 0 auto;
  font-weight: 600;
  color: var(--warning);
  font-size: 12px;
  letter-spacing: 2px;
}

.class-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 11px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  padding: 8px;
  transition: all 0.2s;
}
.class-content:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 20px -4px var(--primary-glow);
}

.subj-code {
  font-weight: 700;
  color: var(--accent);
  font-size: 12px;
}

.subj-name {
  margin: 4px 0;
  line-height: 1.2;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-weight: 600;
  font-size: 11px;
}

.class-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--text-muted);
  font-size: 9px;
}

.empty-slot { height: 100%; }

/* ===== DATA MANAGEMENT ===== */
.data-tabs { 
  display: flex; 
  gap: 8px; 
  margin-bottom: 24px; 
  flex-wrap: wrap;
  background: var(--glass-bg);
  padding: 8px;
  border-radius: 16px;
  border: 1px solid var(--glass-border);
}

.tab { 
  padding: 12px 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.2s;
  border-radius: 10px;
}
.tab:hover { 
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.tab.active { 
  background: linear-gradient(135deg, var(--primary), var(--aurora-2));
  color: white;
  box-shadow: 0 4px 15px -4px var(--primary-glow);
}

.data-card { 
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  overflow: hidden;
}

.data-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(0,0,0,0.2);
}
.data-header h3 { 
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { 
  padding: 16px 24px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}
.data-table th { 
  background: rgba(0,0,0,0.3);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.data-table tr:hover { background: var(--bg-card-hover); }
.data-table tr:last-child td { border-bottom: none; }

.role-badge { 
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 100px;
  letter-spacing: 0.5px;
}
.role-badge.admin { 
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}
.role-badge.teacher { 
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent);
}

.btn-delete { 
  padding: 6px 14px;
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
}
.btn-delete:hover { 
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
}

.btn-edit { 
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-light);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-edit:hover { 
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
}

.action-cell {
  display: flex;
  gap: 6px;
  align-items: center;
}

/* ===== MODAL ===== */
.modal-backdrop { 
  position: fixed; 
  inset: 0; 
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(8px);
  display: flex; 
  align-items: center; 
  justify-content: center; 
  z-index: 1000;
}

.modal { 
  background: var(--bg-dark);
  border: 1px solid var(--glass-border);
  border-radius: 24px;
  width: 100%;
  max-width: 480px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(0,0,0,0.3);
}
.modal-header h3 { 
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.modal-header button { 
  background: var(--bg-card);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.modal-header button:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.modal-body { padding: 24px; }
.modal-body .form-group { margin-bottom: 20px; }
.modal-body label { 
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
}
.modal-body input, 
.modal-body select { 
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  font-size: 14px;
  background: rgba(0,0,0,0.3);
  color: var(--text-primary);
  transition: all 0.2s;
}
.modal-body input:focus, 
.modal-body select:focus { 
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}
.modal-body input::placeholder { color: var(--text-muted); }

.w-full { width: 100%; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .main-content { padding: 16px; }
  .gov-timetable-wrapper { padding: 12px; }
  .td-slot { height: 75px; }
}

/* ===== PRINT ===== */
@media print {
  .sidebar, .controls-row, .timetable-header, .alert, .stats-row, .progress-card {
    display: none !important;
  }
  .app-container { display: block; }
  .main-content { padding: 0; }
  .gov-timetable-wrapper {
    box-shadow: none;
    border: none;
    padding: 0;
    background: white;
  }
  .gov-table { min-width: 100%; color: black; }
}
</style>
