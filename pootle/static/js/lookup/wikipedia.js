(function ($) {
  window.PTL.editor.lookup = window.PTL.editor.lookup || {};

  PTL.editor.lookup.wikipedia = {

    buttonClassName: "wikipedia",
    hint: "Wikipedia",
    url: "//%(querylang)s.wikipedia.org/wiki/%(query)s'",

    init: function () {
      /* Bind event handler */
      $(document).on("click", ".wikipedia", this.lookup);
    },

    ready: function () {
      PTL.editor.addLookupButtons(PTL.editor.lookup.wikipedia);
    },

    lookup: function (e) {
      e.preventDefault()
      PTL.editor.lookup(this, function(lookupText, langFrom, langTo) {
        var url = '//' + langFrom + '.m.wikipedia.org/wiki/' + lookupText.replace(/ /g, "_");
        return url;
      });
    }
  };
})(jQuery);
