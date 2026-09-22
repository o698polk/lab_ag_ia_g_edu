/* DEPRECATED — PromptMaster F2+: use assets/. Auto-loads canonical script. */
(function () {
  var src = "/ui/assets/js/core/auth.js";
  if (document.querySelector('script[data-siga-shim="' + src + '"]')) return;
  var s = document.createElement('script');
  s.src = src;
  s.async = false;
  s.dataset.sigaShim = src;
  document.head.appendChild(s);
})();
