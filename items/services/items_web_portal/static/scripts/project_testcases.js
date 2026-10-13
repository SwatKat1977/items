/*
 * Project test case pages: the delete confirmation pop-up, shared by the list
 * and the view page. A button with data-bs-target="#confirmDeleteTestcaseModal"
 * and data-id / data-name opens it; confirming submits a POST to the delete
 * route for that test case.
 */
(function () {
  const modal = document.getElementById('confirmDeleteTestcaseModal');
  const form = document.getElementById('tcDeleteForm');
  const nameLabel = document.getElementById('tc-delete-name');
  const checkbox = document.getElementById('tcConfirmCheckbox');
  const confirmButton = document.getElementById('tcConfirmDeleteButton');

  if (!modal || !form) {
    return;
  }

  function reset() {
    checkbox.checked = false;
    confirmButton.disabled = true;
  }

  modal.addEventListener('show.bs.modal', function (event) {
    const trigger = event.relatedTarget;
    nameLabel.textContent = trigger.getAttribute('data-name') || '';
    form.action = form.getAttribute('data-action-template')
      .replace('__ID__', trigger.getAttribute('data-id'));
    reset();
  });

  modal.addEventListener('hidden.bs.modal', reset);

  checkbox.addEventListener('change', function () {
    confirmButton.disabled = !this.checked;
  });

  confirmButton.addEventListener('click', function () {
    form.submit();
  });
})();
