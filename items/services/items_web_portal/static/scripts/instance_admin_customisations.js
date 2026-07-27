/*
 * Customisations admin page behaviour:
 *   1. Responsive tab bar (collapse labels to icons when they would overflow).
 *   2. Case Fields add/edit modal population and delete confirmation.
 */
(function () {
  /* ----------------------------------------------------------------
   * Responsive tab bar
   * ---------------------------------------------------------------- */
  const tabBar = document.getElementById('customisationsTabs');

  function updateTabLabels() {
    if (!tabBar) {
      return;
    }
    // Measure in the labels-shown state so the decision is based on the space
    // the labels actually need, not the collapsed width. Removing the class
    // first forces a synchronous reflow before we read the dimensions.
    tabBar.classList.remove('icons-only');
    if (tabBar.scrollWidth > tabBar.clientWidth) {
      tabBar.classList.add('icons-only');
    }
  }

  window.addEventListener('resize', updateTabLabels);
  updateTabLabels();

  /* ----------------------------------------------------------------
   * Case field add / edit modal
   * ---------------------------------------------------------------- */
  const modal = document.getElementById('caseFieldModal');
  const form = document.getElementById('caseFieldForm');
  const title = document.getElementById('caseFieldModalLabel');
  const appliesAll = document.getElementById('cf-applies-all');
  const projectsWrapper = document.getElementById('cf-projects-wrapper');
  const projectsSelect = document.getElementById('cf-projects');

  const ADD_ACTION = '/admin/customisations/case_fields';
  const systemNote = document.getElementById('cf-system-note');

  function toggleProjects() {
    if (!appliesAll || !projectsWrapper) {
      return;
    }
    projectsWrapper.style.display = appliesAll.checked ? 'none' : 'block';
  }

  // System fields may only have their active state and project assignment
  // changed, so lock (and visibly grey out) every other control. Using
  // `disabled` rather than `readOnly` makes the locked state obvious; it is
  // safe because the server rebuilds a system field's immutable attributes
  // from its stored values and ignores whatever the form submits for them.
  function applySystemLock(isSystem) {
    if (!form) {
      return;
    }
    form.field_name.disabled = isSystem;
    form.system_name.disabled = isSystem;
    form.description.disabled = isSystem;
    form.default_value.disabled = isSystem;
    form.field_type.disabled = isSystem;
    form.is_required.disabled = isSystem;
    if (systemNote) {
      systemNote.style.display = isSystem ? 'block' : 'none';
    }
  }

  // Build the Default value control to match the selected field type so the
  // entered default is valid for that type (e.g. a Checkbox default is a
  // true/false choice, a Date default is a date picker). The control always
  // uses name="default_value" so the form submits it regardless of type.
  function renderDefaultControl(type, value) {
    const container = document.getElementById('cf-default-control');
    if (!container) {
      return;
    }
    value = value || '';

    let html;
    switch (type) {
      case 'Checkbox':
        html = '<select class="form-select" id="cf-default-value" name="default_value">'
             + '<option value="false">Unchecked</option>'
             + '<option value="true">Checked</option></select>';
        break;
      case 'Date':
        html = '<input type="date" class="form-control" id="cf-default-value" name="default_value">';
        break;
      case 'Integer':
        html = '<input type="number" step="1" class="form-control" id="cf-default-value" name="default_value">';
        break;
      case 'Url (Link)':
        html = '<input type="url" class="form-control" id="cf-default-value" name="default_value">';
        break;
      case 'Text':
        html = '<textarea class="form-control" id="cf-default-value" name="default_value" rows="2"></textarea>';
        break;
      default: // String, Dropdown, User
        html = '<input type="text" class="form-control" id="cf-default-value" name="default_value">';
    }

    container.innerHTML = html;
    const control = container.firstElementChild;

    if (control.tagName === 'SELECT') {
      control.value = (value === 'true' || value === '1') ? 'true' : 'false';
    } else {
      control.value = value;
    }
  }

  if (form && form.field_type) {
    // Rebuild the default control (starting empty) whenever the type changes.
    form.field_type.addEventListener('change', function () {
      renderDefaultControl(this.value, '');
    });
  }

  function setProjectSelection(names) {
    if (!projectsSelect) {
      return;
    }
    const wanted = new Set(names.filter(Boolean));
    Array.from(projectsSelect.options).forEach(function (opt) {
      opt.selected = wanted.has(opt.value);
    });
  }

  if (appliesAll) {
    appliesAll.addEventListener('change', toggleProjects);
  }

  // Populate the shared modal for either "add" or "edit" when it opens.
  if (modal && form) {
    modal.addEventListener('show.bs.modal', function (event) {
      const trigger = event.relatedTarget;
      const isEdit = trigger && trigger.classList.contains('edit-field-btn');

      if (isEdit) {
        const id = trigger.getAttribute('data-id');
        const isSystem = trigger.getAttribute('data-is-system') === '1';
        title.textContent = isSystem ? 'Edit System Field' : 'Edit Case Field';
        form.action = ADD_ACTION + '/' + id + '/modify';

        form.field_name.value = trigger.getAttribute('data-field-name') || '';
        form.system_name.value = trigger.getAttribute('data-system-name') || '';
        form.description.value = trigger.getAttribute('data-description') || '';
        form.field_type.value = trigger.getAttribute('data-field-type') || '';
        renderDefaultControl(form.field_type.value,
                             trigger.getAttribute('data-default-value') || '');
        form.enabled.checked = trigger.getAttribute('data-enabled') === '1';
        form.is_required.checked = trigger.getAttribute('data-is-required') === '1';
        appliesAll.checked = trigger.getAttribute('data-applies-all') === '1';

        const projects = (trigger.getAttribute('data-projects') || '').split(',');
        setProjectSelection(projects);

        applySystemLock(isSystem);
      } else {
        title.textContent = 'Add Case Field';
        form.action = ADD_ACTION;
        form.reset();
        renderDefaultControl(form.field_type.value, '');
        setProjectSelection([]);
        applySystemLock(false);
      }

      toggleProjects();
    });
  }

  /* ----------------------------------------------------------------
   * Case field delete confirmation
   * ---------------------------------------------------------------- */
  const deleteModal = document.getElementById('confirmDeleteFieldModal');
  const deleteForm = document.getElementById('cfDeleteForm');
  const deleteName = document.getElementById('cf-delete-name');
  const confirmCheckbox = document.getElementById('cfConfirmCheckbox');
  const confirmButton = document.getElementById('cfConfirmDeleteButton');

  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', function (event) {
      const trigger = event.relatedTarget;
      const id = trigger.getAttribute('data-id');
      deleteName.textContent = trigger.getAttribute('data-field-name') || '';
      deleteForm.action = '/admin/customisations/case_fields/' + id + '/delete';
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
