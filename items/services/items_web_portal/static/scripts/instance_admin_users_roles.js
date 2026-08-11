/*
 * Users & Roles page behaviour.
 *
 * Confirmation banners dismiss themselves after a delay set per message by
 * the server (data-auto-dismiss-ms). Errors deliberately carry no such
 * attribute and stay until the user closes them: a missed confirmation costs
 * nothing, whereas a missed error leaves someone believing an action
 * succeeded when it did not.
 */
(function () {
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
})();
