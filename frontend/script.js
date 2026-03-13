// Initialize API URL - empty string for relative paths if on same domain, or specify your backend URL
window.API_URL = ''; // e.g., 'http://localhost:5000'

// Initialize Feather icons
feather.replace();

// Theme toggle
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  });
}

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
}

// Login form (on index.html)
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const roleInput = document.querySelector('input[name="role"]:checked');
    const role = roleInput ? roleInput.value : 'employee';
    const email = loginForm.querySelector('input[type="text"]').value;
    const password = loginForm.querySelector('input[type="password"]').value;

    try {
      const response = await fetch(`${window.API_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('jwt_token', data.access_token);
        localStorage.setItem('user_role', data.role);
        alert('Login successful!');
        window.location.href = data.role === 'admin' ? './admin.html' : './attendance.html';
      } else {
        alert(data.message || 'Login failed');
      }
    } catch (err) {
      alert('Error connecting to backend API. Please ensure the server is running.');
      console.error(err);
    }
  });
}

// Helper to get auth headers
function getAuthHeaders(headers = {}) {
  const token = localStorage.getItem('jwt_token');
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// Record Attendance (on attendance.html)
async function recordAttendance(video, status, clockInBtn) {
  clockInBtn.disabled = true;
  status.textContent = 'Capturing and verifying your face...';

  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));
  const formData = new FormData();
  formData.append('image', blob, 'capture.jpg');

  try {
    const response = await fetch(`${window.API_URL}/api/recognize`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData
    });

    let data;
    const text = await response.text();
    try {
      data = JSON.parse(text);
    } catch (parseErr) {
      console.error('Error parsing JSON response:', parseErr);
      console.error('Raw response:', text);
      throw new Error(response.status === 405 ? 'Method Not Allowed. Check server configuration.' : 'Invalid response from server.');
    }

    const message = data.message || (response.ok ? 'Success!' : 'Unknown error');
    status.innerHTML = response.ok ? `<span class="text-emerald-600 font-bold">${message}</span>` : `<span class="text-red-600">${message}</span>`;
    if (response.ok) {
      clockInBtn.innerHTML = '<i data-feather="check-circle"></i> Attendance Recorded!';
      clockInBtn.classList.add('bg-emerald-600');
    } else {
      clockInBtn.disabled = false;
    }
  } catch (err) {
    status.textContent = err.message || 'Error connecting to API server. Try again.';
    clockInBtn.disabled = false;
    console.error(err);
  }
}

// If on attendance page, attach listener
const clockInBtn = document.getElementById('clock-in-btn');
if (clockInBtn) {
  const video = document.getElementById('video');
  const status = document.getElementById('status');
  const statusText = document.getElementById('status-text');

  // Initialize camera for attendance
  async function initAttendanceCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      if (statusText) statusText.textContent = 'Camera ready';
    } catch (err) {
      console.error('Camera error:', err);
      if (statusText) statusText.textContent = 'Camera error or permission denied';
    }
  }
  initAttendanceCamera();

  clockInBtn.addEventListener('click', () => recordAttendance(video, status, clockInBtn));
}

// Fetch and display logs (on admin or dashboard pages)
const logsContainer = document.getElementById('logs');
if (logsContainer && !window.location.pathname.includes('dashboard.html')) {
  async function fetchLogs() {
    try {
      const response = await fetch(`${window.API_URL}/api/logs`, {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      if (response.ok) {
        logsContainer.innerHTML = data.logs.map(log => `
          <div class="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 flex justify-between items-center">
            <div>
              <p class="font-bold">${log.name}</p>
              <p class="text-sm text-slate-500">${log.timestamp}</p>
            </div>
            <span class="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold uppercase">${log.status}</span>
          </div>
        `).join('') || '<p class="text-center text-slate-500 py-8">No attendance logs found yet.</p>';
      } else if (response.status === 401 || response.status === 422) {
        localStorage.removeItem('jwt_token');
        if (window.location.pathname.indexOf('index.html') === -1 && window.location.pathname !== '/') {
            window.location.href = './index.html';
        }
      }
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  }
  fetchLogs();
}

// Admin Dashboard Functions
async function loadAdminDashboard() {
    const statsUsers = document.getElementById('stat-users');
    const statsLogs = document.getElementById('stat-logs');
    const userTableBody = document.getElementById('user-table-body');

    try {
        const [statsRes, usersRes] = await Promise.all([
            fetch(`${window.API_URL}/api/admin/stats`, { headers: getAuthHeaders() }),
            fetch(`${window.API_URL}/api/admin/users`, { headers: getAuthHeaders() })
        ]);

        if (statsRes.ok) {
            const stats = await statsRes.json();
            if (statsUsers) statsUsers.textContent = stats.user_count;
            if (statsLogs) statsLogs.textContent = stats.log_count;
        }

        if (usersRes.ok) {
            const usersData = await usersRes.json();
            if (userTableBody) {
                userTableBody.innerHTML = usersData.users.map(user => `
                    <tr class="group">
                        <td class="py-4">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center font-bold text-primary-600">
                                    ${user.name.charAt(0)}
                                </div>
                                <div>
                                    <p class="font-semibold">${user.name}</p>
                                    <p class="text-xs text-slate-500">${user.email}</p>
                                </div>
                            </div>
                        </td>
                        <td class="py-4">
                            <span class="px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-medium uppercase">${user.role}</span>
                        </td>
                        <td class="py-4">
                            <button onclick="deleteUser(${user.id})" class="p-2 text-slate-400 hover:text-red-600 transition">
                                <i data-feather="trash-2" class="w-4 h-4"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
                feather.replace();
            }
        }
    } catch (err) {
        console.error("Failed to load admin dashboard:", err);
    }
}

async function deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user and all their records?')) return;
    try {
        const response = await fetch(`${window.API_URL}/api/admin/users/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            loadAdminDashboard();
        } else {
            alert('Failed to delete user');
        }
    } catch (err) {
        console.error("Delete user error:", err);
    }
}

window.loadAdminDashboard = loadAdminDashboard;
window.deleteUser = deleteUser;

console.log('Frontend initialized. API Server:', window.API_URL || 'Local relative');
