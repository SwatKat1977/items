/*
 * Modify User page behaviour: Projects tab remove-access confirmation.
 */
(function () {
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
