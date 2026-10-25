/* سامانه مدیریت دانشگاهی — اسکریپت‌های عمومی */
document.addEventListener('DOMContentLoaded', function () {
  // ۱) تأییدیه حذف برای فرم‌های دارای data-confirm
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!window.confirm(form.getAttribute('data-confirm'))) {
        event.preventDefault();
      }
    });
  });

  // ۲) بستن پیام‌ها با دکمه ضربدر (بدون رویداد inline، سازگار با CSP)
  document.addEventListener('click', function (event) {
    var closer = event.target.closest('[data-close-alert]');
    if (closer) {
      var alertBox = closer.closest('.alert');
      if (alertBox) alertBox.remove();
    }
  });

  // ۳) محو خودکار پیام‌های موفقیت/خطا پس از ۵ ثانیه
  document.querySelectorAll('.alert[data-autohide]').forEach(function (alert) {
    setTimeout(function () {
      alert.classList.add('hide');
      setTimeout(function () { alert.remove(); }, 500);
    }, 5000);
  });

  // ۴) ارسال خودکار فرم فیلتر نمرات با تغییر انتخاب دانشجو
  var studentFilter = document.querySelector('select[name="student_id"]');
  if (studentFilter) {
    studentFilter.addEventListener('change', function () {
      if (studentFilter.form) studentFilter.form.submit();
    });
  }
});
