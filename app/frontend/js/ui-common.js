/* DEPRECATED — PromptMaster F2+: use assets/. Auto-loads canonical script. */
(function () {
  var src = "/ui/assets/js/components/toast.js";
  if (document.querySelector('script[data-siga-shim="' + src + '"]')) return;
  var s = document.createElement('script');
  s.src = src;
  s.async = false;
  s.dataset.sigaShim = src;
  document.head.appendChild(s);
})();
(function () {
  var src = "/ui/assets/js/components/table.js";
  if (document.querySelector('script[data-siga-shim="' + src + '"]')) return;
  var s = document.createElement('script');
  s.src = src;
  s.async = false;
  s.dataset.sigaShim = src;
  document.head.appendChild(s);
})();
