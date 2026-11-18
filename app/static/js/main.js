/**
 * National Retirement Clearance Portal - Core Client-Side Logic
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Navigation Toggle
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const mobileNavToggle = document.getElementById('mobileNavToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');

  function openSidebar() {
    if (sidebar && sidebarOverlay) {
      sidebar.classList.add('show');
      sidebarOverlay.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeSidebar() {
    if (sidebar && sidebarOverlay) {
      sidebar.classList.remove('show');
      sidebarOverlay.classList.remove('show');
      document.body.style.overflow = '';
    }
  }

  if (mobileNavToggle) {
    mobileNavToggle.addEventListener('click', openSidebar);
  }
  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', closeSidebar);
  }
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // 2. Password Visibility Toggle
  const passwordToggles = document.querySelectorAll('.toggle-password-btn');
  passwordToggles.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetInput = document.querySelector(btn.getAttribute('data-target'));
      if (targetInput) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          targetInput.type = 'password';
          btn.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  // 3. Auto-dismiss alerts after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      } catch (e) {}
    }, 6000);
  });
});
