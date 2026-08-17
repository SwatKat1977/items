/*
 * Users & Roles page behaviour:
 *   1. Responsive tab bar (collapse labels to icons when they would overflow).
 *   2. Confirmation banner auto-dismiss.
 *   3. Role add/edit modal population and the Add/Modify-implies-Read rule.
 *   4. Role delete confirmation.
 */
(function () {
  /* ----------------------------------------------------------------
   * Responsive tab bar
   * ---------------------------------------------------------------- */
  var tabBar = document.getElementById('usersRolesTabs');

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
   * Confirmation banners dismiss themselves after a delay set per message
   * by the server (data-auto-dismiss-ms). Errors deliberately carry no such
   * attribute and stay until the user closes them: a missed confirmation
   * costs nothing, whereas a missed error leaves someone believing an
   * action succeeded when it did not.
   * ---------------------------------------------------------------- */
  var banners = document.querySelectorAll('[data-auto-dismiss-ms]');

  Array.prototype.forEach.call(banners, function (banner) {
    var delay = parseInt(banner.getAttribute('data-auto-dismiss-ms'), 10);

    // No delay, an unparsable one, or zero means "leave it alone", so a
    // malformed value fails towards keeping the message rather than hiding
    // it prematurely.
    if (!delay || delay <= 0) {
      return;
    }

    window.setTimeout(function () {
      // Bootstrap may not be present in a test harness that renders the
      // template without the full page; fall back to simply hiding.
      if (window.bootstrap && window.bootstrap.Alert) {
        window.bootstrap.Alert.getOrCreateInstance(banner).close();
      } else {
        banner.style.display = 'none';
      }
    }, delay);
  });

  /* ----------------------------------------------------------------
   * Role add / edit modal
   * ---------------------------------------------------------------- */
  var roleModal = document.getElementById('roleModal');
  var roleForm = document.getElementById('roleForm');
  var roleTitle = document.getElementById('roleModalLabel');

  var ADD_ROLE_ACTION = '/admin/users_roles/roles';

  // Add/Modify implies Read (see user_roles_design.md §4.1): ticking
  // Add/Modify auto-ticks and locks Read, since the combination of
  // add-modify-without-read is rejected by the backend anyway. Locking it
  // client-side turns a would-be validation error into something that is
  // simply not reachable through the checkboxes.
  function wirePermissionRow(area) {
    var readBox = document.getElementById('role-perm-' + area + '-read');
    var addModifyBox = document.getElementById('role-perm-' + area + '-add-modify');

    if (!readBox || !addModifyBox) {
      return;
    }

    addModifyBox.addEventListener('change', function () {
      if (addModifyBox.checked) {
        readBox.checked = true;
        readBox.disabled = true;
      } else {
        readBox.disabled = false;
      }
    });
  }

  if (roleForm) {
    Array.prototype.forEach.call(
      roleForm.querySelectorAll('.role-perm-add-modify'),
      function (box) {
        wirePermissionRow(box.getAttribute('data-area'));
      });

    // Disabled form fields are not submitted by the browser at all - so a
    // Read checkbox locked (disabled) by the rule above would silently
    // vanish from the submitted form, sending can_add_modify=true with
    // can_read absent/false and tripping the exact validation error the
    // lock exists to prevent. Re-enable everything just before submission,
    // once the user can no longer change it, so its "on" value is included.
    roleForm.addEventListener('submit', function () {
      Array.prototype.forEach.call(
        roleForm.querySelectorAll('input[type="checkbox"]:disabled'),
        function (box) {
          box.disabled = false;
        });
    });
  }

  function resetPermissionGrid() {
    if (!roleForm) {
      return;
    }
    Array.prototype.forEach.call(
      roleForm.querySelectorAll('input[type="checkbox"]'),
      function (box) {
        box.checked = false;
        box.disabled = false;
      });
  }

  function applyPermissionGrid(permissionsByArea) {
    resetPermissionGrid();
    Object.keys(permissionsByArea).forEach(function (area) {
      var perm = permissionsByArea[area];
      var readBox = document.getElementById('role-perm-' + area + '-read');
      var addModifyBox = document.getElementById('role-perm-' + area + '-add-modify');
      var deleteBox = document.getElementById('role-perm-' + area + '-delete');

      if (readBox) {
        readBox.checked = !!perm.can_read;
      }
      if (addModifyBox) {
        addModifyBox.checked = !!perm.can_add_modify;
      }
      if (deleteBox) {
        deleteBox.checked = !!perm.can_delete;
      }
      if (addModifyBox && addModifyBox.checked && readBox) {
        readBox.checked = true;
        readBox.disabled = true;
      }
    });
  }

  // Populate the shared modal for either "add" or "edit" when it opens.
  if (roleModal && roleForm) {
    roleModal.addEventListener('show.bs.modal', function (event) {
      var trigger = event.relatedTarget;
      var isEdit = trigger && trigger.classList.contains('edit-role-btn');

      if (isEdit) {
        var id = trigger.getAttribute('data-id');
        roleTitle.textContent = 'Edit Role';
        roleForm.action = ADD_ROLE_ACTION + '/' + id + '/modify';
        roleForm.name.value = trigger.getAttribute('data-name') || '';

        var permissions;
        try {
          permissions = JSON.parse(trigger.getAttribute('data-permissions') || '{}');
        } catch (e) {
          permissions = {};
        }
        applyPermissionGrid(permissions);
      } else {
        roleTitle.textContent = 'Add Role';
        roleForm.action = ADD_ROLE_ACTION;
        roleForm.reset();
        resetPermissionGrid();
      }
    });
  }

  /* ----------------------------------------------------------------
   * Role delete confirmation
   * ---------------------------------------------------------------- */
  var deleteRoleModal = document.getElementById('confirmDeleteRoleModal');
  var deleteRoleForm = document.getElementById('roleDeleteForm');
  var deleteRoleName = document.getElementById('role-delete-name');
  var deleteRoleFormName = document.getElementById('role-delete-form-name');
  var roleConfirmCheckbox = document.getElementById('roleConfirmCheckbox');
  var roleConfirmButton = document.getElementById('roleConfirmDeleteButton');

  if (deleteRoleModal) {
    deleteRoleModal.addEventListener('show.bs.modal', function (event) {
      var trigger = event.relatedTarget;
      var id = trigger.getAttribute('data-id');
      var name = trigger.getAttribute('data-name') || '';
      deleteRoleName.textContent = name;
      deleteRoleFormName.value = name;
      deleteRoleForm.action = '/admin/users_roles/roles/' + id + '/delete';
      roleConfirmCheckbox.checked = false;
      roleConfirmButton.disabled = true;
    });

    deleteRoleModal.addEventListener('hidden.bs.modal', function () {
      roleConfirmCheckbox.checked = false;
      roleConfirmButton.disabled = true;
    });
  }

  if (roleConfirmCheckbox) {
    roleConfirmCheckbox.addEventListener('change', function () {
      roleConfirmButton.disabled = !this.checked;
    });
  }

  if (roleConfirmButton) {
    roleConfirmButton.addEventListener('click', function () {
      deleteRoleForm.submit();
    });
  }
})();
