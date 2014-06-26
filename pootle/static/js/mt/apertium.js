(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.apertium = {

    buttonClassName: "apertium",
    hint: "Apertium",
    validatePair: true,

    url: "http://api.apertium.org/JSLibrary.js",
    cookieName: "apertium_pairs",
    cookieOptions: {path: '/', expires: 15},

    init: function (apiKey) {
      var _this = PTL.editor.mt.apertium;
      /* Load Apertium library */
      _this.url = apiKey == undefined ? _this.url : _this.url + '?key=' + apiKey;
      $.getScript(_this.url, function () {
        /* Init variables */
        var _this = PTL.editor.mt.apertium;

        _this.pairs = $.cookie(_this.cookieName);
        if (!_this.pairs) {
          var pairs = apertium.getSupportedLanguagePairs();
          _this.pairs = $.map(pairs, function (obj, i) {
            return {source: obj.source, target: obj.target};
          });
          var cookie_data = JSON.stringify(_this.pairs);
          $.cookie(_this.cookieName, cookie_data, _this.cookieOptions);
        } else {
          _this.pairs = $.parseJSON(_this.pairs);
        }

        /* Bind event handler */
        $(document).on("click", ".apertium", _this.translate);
      });
    },

    ready: function () {
      PTL.editor.addMTButtons(PTL.editor.mt.apertium);
    },

    translate: function () {
      PTL.editor.translate(this, function(sourceText, langFrom, langTo, resultCallback) {
        var content = new Object()
        content.text = sourceText;
        content.type = "txt";
        apertium.translate(content, langFrom, langTo, function (result) {
          if (result.translation) {
            resultCallback({
              translation: result.translation
            });
          } else {
            resultCallback({
              msg: "Apertium Error: " + result.error.message
            });
          }
        });
      });
    }

  };
})(jQuery);
