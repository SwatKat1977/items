document.getElementById('confirmCheckbox').addEventListener('change', function() {
  document.getElementById('confirmDeleteButton').disabled = !this.checked;
});

document.getElementById('confirmDeleteButton').addEventListener('click', function() {
  const projectId = document.getElementById('confirmDeleteModal').getAttribute('data-project-id');
  document.getElementById('projectId').value = projectId;
  document.getElementById('deleteForm').submit();
});

document.getElementById('confirmDeleteModal').addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const projectId = button.getAttribute('data-project-id');
  this.setAttribute('data-project-id', projectId);
});

document.getElementById('confirmDeleteModal').addEventListener('hidden.bs.modal', function () {
  document.getElementById('confirmCheckbox').checked = false;
  document.getElementById('confirmDeleteButton').disabled = true;
});
