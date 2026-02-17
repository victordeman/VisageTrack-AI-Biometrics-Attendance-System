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
    const role = document.querySelector('input[name="role"]:checked').value;
    const email = loginForm.querySelector('input[type="text"]').value;
    const password = loginForm.querySelector('input[type="password"]').value;

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('jwt_token', data.access_token);
        console.log('Login successful, token saved.');
        alert('Logged in! Redirecting...');
        window.location.href = role === 'admin' ? '/admin' : '/dashboard';
      } else {
        alert(data.message || 'Login failed');
      }
    } catch (err) {
      alert('Error logging in');
      console.error(err);
    }
  });
}

// Camera helper
async function startCamera(videoElement) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoElement.srcObject = stream;
    console.log("Camera started successfully.");
  } catch (err) {
    console.error("Error accessing camera:", err);
    alert("Could not access camera. Please ensure you have given permission and are using HTTPS.");
  }
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
    const token = localStorage.getItem('jwt_token');
    console.log("Recording attendance. Token present:", !!token);

    const response = await fetch('/api/recognize', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    const data = await response.json();
    const message = data.message || (response.ok ? 'Success!' : 'Unknown error');
    status.innerHTML = response.ok ? `<span class="text-emerald-600 font-bold">${message}</span>` : `<span class="text-red-600">${message}</span>`;

    if (response.ok) {
      clockInBtn.innerHTML = '<i data-feather="check-circle"></i> Attendance Recorded!';
      clockInBtn.classList.add('bg-emerald-600');
      feather.replace();
    } else {
      clockInBtn.disabled = false;
      if (response.status === 401 || response.status === 422) {
        alert("Session expired or invalid. Please login again.");
        window.location.href = '/';
      }
    }
  } catch (err) {
    status.textContent = 'Error connecting to server. Try again.';
    clockInBtn.disabled = false;
    console.error(err);
  }
}

// If on attendance page, attach listener
const clockInBtn = document.getElementById('clock-in-btn');
if (clockInBtn) {
  const video = document.getElementById('video');
  const status = document.getElementById('status');
  startCamera(video);
  clockInBtn.addEventListener('click', () => recordAttendance(video, status, clockInBtn));
}

// Enroll Face Logic
const enrollBtn = document.getElementById('enroll-btn');
if (enrollBtn) {
  const video = document.getElementById('video');
  const status = document.getElementById('status');
  startCamera(video);

  enrollBtn.addEventListener('click', async () => {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    if (!name || !email) {
      alert("Please enter name and email");
      return;
    }

    enrollBtn.disabled = true;
    status.textContent = 'Capturing image...';

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));

    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('image1', blob, 'enroll.jpg');

    try {
      const token = localStorage.getItem('jwt_token');
      console.log("Enrolling. Token present:", !!token);

      if (!token) {
        alert("Please login first");
        window.location.href = '/';
        return;
      }

      status.textContent = 'Uploading enrollment data...';
      const response = await fetch('/api/enroll', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        status.innerHTML = `<span class="text-emerald-600 font-bold">Enrollment Successful! Image saved.</span>`;
        enrollBtn.innerHTML = '<i data-feather="check-circle"></i> Enrolled';
        feather.replace();
      } else {
        status.innerHTML = `<span class="text-red-600">${data.message || 'Enrollment failed'}</span>`;
        enrollBtn.disabled = false;
        if (response.status === 401 || response.status === 422) {
          alert("Session expired. Please login again.");
          window.location.href = '/';
        }
      }
    } catch (err) {
      status.textContent = 'Error connecting to server.';
      enrollBtn.disabled = false;
      console.error(err);
    }
  });
}

// Fetch and display logs
async function loadLogs() {
  const logsContainer = document.getElementById('logs');
  if (!logsContainer) return;

  try {
    const token = localStorage.getItem('jwt_token');
    console.log("Loading logs. Token present:", !!token);
    if (!token) return;

    const response = await fetch('/api/logs', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    if (response.ok) {
      logsContainer.innerHTML = data.logs.map(log => `
        <div class="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg flex justify-between items-center border border-slate-200 dark:border-slate-700">
          <div>
            <p class="font-bold text-primary-600">${log.name}</p>
            <p class="text-sm text-slate-500">${log.timestamp}</p>
          </div>
          <span class="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold uppercase">${log.status}</span>
        </div>
      `).join('') || '<p class="text-center text-slate-500">No logs found.</p>';
    } else if (response.status === 401 || response.status === 422) {
        console.warn("Unauthorized access to logs. User may need to re-login.");
    }
  } catch (err) {
    console.error("Error loading logs:", err);
  }
}

loadLogs();

console.log('VisageTrack AI Frontend Script Loaded.');
