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

/*
 * The move section pop-up (list page only). A section's move button
 * (data-bs-target="#moveSectionModal") carries data-id, data-name,
 * data-parent-id (its current parent, empty for the top level) and
 * data-subtree-ids (itself and everything beneath it, comma separated). The
 * destination list starts on the current parent and leaves out that subtree:
 * a section cannot be moved into itself or into one of its own sub-sections.
 */
(function () {
  const modal = document.getElementById('moveSectionModal');
  const form = document.getElementById('moveSectionForm');

  if (!modal || !form) {
    return;
  }

  const nameLabel = document.getElementById('move-section-name');
  const select = document.getElementById('move-section-parent');

  modal.addEventListener('show.bs.modal', function (event) {
    const trigger = event.relatedTarget;
    const subtree = (trigger.getAttribute('data-subtree-ids') || '')
      .split(',').filter(Boolean);

    nameLabel.textContent = trigger.getAttribute('data-name') || '';
    form.action = form.getAttribute('data-action-template')
      .replace('__ID__', trigger.getAttribute('data-id'));

    Array.from(select.options).forEach(function (option) {
      const inside = subtree.indexOf(option.value) !== -1;
      option.hidden = inside;
      option.disabled = inside;
    });
    select.value = trigger.getAttribute('data-parent-id') || '';
  });
})();

/*
 * Section delete (list page only). A section's delete button
 * (data-bs-target="#confirmDeleteSectionModal") carries data-id, data-name and
 * data-testcase-count (the test cases deleting it would remove, including
 * those in sub-sections). It opens ONE confirmation that says what will be
 * lost:
 *   - no test cases: a plain confirmation that posts a plain delete;
 *   - some: a red warning with the count, a confirmation worded to match, and
 *     a button that posts cascade=true.
 * If the count on the page was out of date, the server refuses a plain delete
 * and the page comes back with #confirmCascadeSectionModal, which is opened
 * here straight away (data-auto-open) as a backstop.
 */
(function () {
  const modal = document.getElementById('confirmDeleteSectionModal');
  const form = document.getElementById('secDeleteForm');

  if (modal && form) {
    const nameLabel = document.getElementById('sec-delete-name');
    const warning = document.getElementById('sec-delete-warning');
    const countLabel = document.getElementById('sec-delete-count');
    const nounLabel = document.getElementById('sec-delete-noun');
    const checkbox = document.getElementById('secConfirmCheckbox');
    const checkboxLabel = document.getElementById('secConfirmLabel');
    const cascadeInput = document.getElementById('sec-cascade');
    const confirmButton = document.getElementById('secConfirmDeleteButton');

    const reset = function () {
      checkbox.checked = false;
      confirmButton.disabled = true;
    };

    modal.addEventListener('show.bs.modal', function (event) {
      const trigger = event.relatedTarget;
      const count = parseInt(trigger.getAttribute('data-testcase-count'), 10)
        || 0;
      const noun = count === 1 ? 'test case' : 'test cases';

      nameLabel.textContent = trigger.getAttribute('data-name') || '';
      form.action = form.getAttribute('data-action-template')
        .replace('__ID__', trigger.getAttribute('data-id'));

      if (count > 0) {
        countLabel.textContent = count;
        nounLabel.textContent = noun;
        warning.style.display = 'block';
        checkboxLabel.textContent = 'I confirm I want to delete this section '
          + 'and its ' + count + ' ' + noun + '.';
        confirmButton.textContent = 'Delete section and ' + count + ' ' + noun;
        cascadeInput.value = 'true';
      } else {
        warning.style.display = 'none';
        checkboxLabel.textContent = 'I confirm I want to delete this item.';
        confirmButton.textContent = 'OK';
        cascadeInput.value = '';
      }

      reset();
    });

    modal.addEventListener('hidden.bs.modal', reset);

    checkbox.addEventListener('change', function () {
      confirmButton.disabled = !this.checked;
    });

    confirmButton.addEventListener('click', function () {
      form.submit();
    });
  }

  const cascadeModal = document.getElementById('confirmCascadeSectionModal');
  if (cascadeModal && cascadeModal.getAttribute('data-auto-open') === 'true') {
    new bootstrap.Modal(cascadeModal).show();
  }
})();
