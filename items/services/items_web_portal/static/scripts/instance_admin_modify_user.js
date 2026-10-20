/*
 * Modify User page behaviour:
 *   1. Save User / Cancel are hidden on the Projects tab.
 *   2. A role's Save button is enabled only once the role has changed.
 *   3. Projects tab remove-access confirmation.
 */
(function () {
  /* ----------------------------------------------------------------
   * Save User only covers the User and Access tabs: project access and
   * roles save on their own. So it is not offered on the Projects tab,
   * which has its own "Back to users". The server renders the right state
   * for the tab it opens on; this keeps it right as the tabs change.
   * ---------------------------------------------------------------- */
  var saveRow = document.getElementById('user-save-row');

  Array.prototype.forEach.call(
    document.querySelectorAll('#modifyUserTabs [data-bs-toggle="tab"]'),
    function (tab) {
      tab.addEventListener('shown.bs.tab', function (event) {
        if (saveRow) {
          saveRow.classList.toggle(
            'd-none',
            event.target.getAttribute('href') === '#tab-projects');
        }
      });
    });

  /* ----------------------------------------------------------------
   * Choosing a role does not save it - the Save button beside it does -
   * so make a change that is waiting impossible to miss: Save is enabled
   * only while the dropdown differs from the saved role, and the dropdown
   * is outlined while it does. Without this script the button is simply
   * always enabled, so saving still works.
   * ---------------------------------------------------------------- */
  Array.prototype.forEach.call(
    document.querySelectorAll('form.role-form'),
    function (form) {
      var select = form.querySelector('.role-select');
      var saveButton = form.querySelector('.role-save-btn');

      if (!select || !saveButton) {
        return;
      }

      var savedRole = select.getAttribute('data-saved-role') || '';

      function sync() {
        var changed = select.value !== savedRole;
        saveButton.disabled = !changed;
        select.classList.toggle('border-warning', changed);
      }

      select.addEventListener('change', sync);
      sync();
    });

  var deleteModal = document.getElementById('confirmRemoveProjectModal');
  var deleteForm = document.getElementById('removeProjectForm');
  var deleteName = document.getElementById('rp-project-name');
  var confirmCheckbox = document.getElementById('rpConfirmCheckbox');
  var confirmButton = document.getElementById('rpConfirmRemoveButton');

  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', function (event) {
      var trigger = event.relatedTarget;
      var userId = trigger.getAttribute('data-user-id');
      var projectId = trigger.getAttribute('data-project-id');
      deleteName.textContent = trigger.getAttribute('data-project-name') || '';
      deleteForm.action = '/admin/users_roles/' + userId +
        '/projects/' + projectId + '/delete';
      confirmCheckbox.checked = false;
      confirmButton.disabled = true;
    });

    deleteModal.addEventListener('hidden.bs.modal', function () {
      confirmCheckbox.checked = false;
      confirmButton.disabled = true;
    });
  }

  if (confirmCheckbox) {
    confirmCheckbox.addEventListener('change', function () {
      confirmButton.disabled = !this.checked;
    });
  }

  if (confirmButton) {
    confirmButton.addEventListener('click', function () {
      deleteForm.submit();
    });
  }
})();
