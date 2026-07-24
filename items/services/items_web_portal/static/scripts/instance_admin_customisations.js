/*
 * Customisations tab bar responsive behaviour.
 *
 * Rather than relying on a fixed breakpoint, this collapses the tab labels to
 * icons only as soon as the full-label tab bar would overflow its container
 * (which would otherwise show a horizontal scroll bar). Labels are restored
 * whenever there is room for them again.
 */
(function () {
  const tabBar = document.getElementById('customisationsTabs');
  if (!tabBar) {
    return;
  }

  function updateTabLabels() {
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
})();
