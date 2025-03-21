  document.getElementById('confirmCheckbox').addEventListener('change', function() {
    const confirmButton = document.getElementById('confirmDeleteButton');
    confirmButton.disabled = !this.checked;
  });

  document.getElementById('confirmDeleteButton').addEventListener('click', function() {
    const projectId = document.querySelector('[data-project-id]').getAttribute('data-project-id');

    // Set the projectId in the hidden form
    document.getElementById('projectId').value = projectId;

    // Submit the form
    document.getElementById('deleteForm').submit();
  });

  // Reset checkbox and button when modal is hidden
  const modalElement = document.getElementById('confirmDeleteModal');
  const modal = new bootstrap.Modal(modalElement);
  modalElement.addEventListener('hidden.bs.modal', function () {
    document.getElementById('confirmCheckbox').checked = false;
    document.getElementById('confirmDeleteButton').disabled = true;
  });

document.getElementById('confirmDeleteModal').addEventListener('hidden.bs.modal', function () {
  const checkbox = document.getElementById('confirmCheckbox');
  const button = document.getElementById('confirmDeleteButton');

  if (checkbox) {
    checkbox.checked = false;
  }
  if (button) {
    button.disabled = true;
  }
});