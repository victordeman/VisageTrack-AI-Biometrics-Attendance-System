// Define the custom-navbar web component
class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <nav class="custom-navbar flex justify-between items-center px-6 py-4">
        <div class="text-xl font-bold text-primary-600">VisageTrack AI</div>
        <ul class="flex space-x-6">
          <li><a href="#" class="text-slate-700 dark:text-slate-300 hover:text-primary-600">Home</a></li>
          <li><a href="attendance.html" class="text-slate-700 dark:text-slate-300 hover:text-primary-600">Attendance</a></li>
          <li><a href="enroll.html" class="text-slate-700 dark:text-slate-300 hover:text-primary-600">Enroll</a></li>
          <li><a href="#" class="text-slate-700 dark:text-slate-300 hover:text-primary-600">Dashboard</a></li>
        </ul>
      </nav>
    `;
  }
}

customElements.define('custom-navbar', CustomNavbar);
