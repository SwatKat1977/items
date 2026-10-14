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

/*
 * The add / rename section pop-up (list page only). A button with
 * data-bs-target="#sectionModal" and data-section-mode opens it:
 *   add      - a new top-level section
 *   add-sub  - a new sub-section of data-parent-id (named data-parent-name)
 *   rename   - rename section data-id, currently named data-name
 */
(function () {
  const modal = document.getElementById('sectionModal');
  const form = document.getElementById('sectionForm');

  if (!modal || !form) {
    return;
  }

  const title = document.getElementById('sectionModalLabel');
  const nameInput = document.getElementById('section-name');
  const parentInput = document.getElementById('section-parent-id');

  modal.addEventListener('show.bs.modal', function (event) {
    const trigger = event.relatedTarget;
    const mode = trigger.getAttribute('data-section-mode');

    if (mode === 'rename') {
      title.textContent = 'Rename Section';
      form.action = form.getAttribute('data-rename-action-template')
        .replace('__ID__', trigger.getAttribute('data-id'));
      nameInput.value = trigger.getAttribute('data-name') || '';
      parentInput.value = '';
    } else if (mode === 'add-sub') {
      title.textContent = 'Add Sub-section to "'
        + (trigger.getAttribute('data-parent-name') || '') + '"';
      form.action = form.getAttribute('data-add-action');
      nameInput.value = '';
      parentInput.value = trigger.getAttribute('data-parent-id') || '';
    } else {
      title.textContent = 'Add Section';
      form.action = form.getAttribute('data-add-action');
      nameInput.value = '';
      parentInput.value = '';
    }
  });

  modal.addEventListener('shown.bs.modal', function () {
    nameInput.focus();
    nameInput.select();
  });
})();
