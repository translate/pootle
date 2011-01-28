(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.apertium = {

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
        _this.targetLang = PTL.editor.normalizeCode($("div#target_lang").text());

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
        $(".apertium").live("click", _this.translate);
      });
    },

    ready: function () {
      var _this = PTL.editor.mt.apertium;
      if (PTL.editor.isSupportedTarget(_this.pairs, _this.targetLang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function () {
          var source = PTL.editor.normalizeCode($(this).attr("lang"));
          if (PTL.editor.isSupportedPair(_this.pairs, source, _this.targetLang)) {
            PTL.editor.addMTButton("apertium",
                                   m("images/apertium.png"),
                                   "Apertium");
          }
        });
      }
    },

    translate: function () {
      PTL.editor.translate(function(sourceText, langFrom, langTo, resultCallback) {
        var content = new Object()
        content.text = sourceText;
        content.type = "txt";
        apertium.translate(content, langFrom, langTo, function (result) {
          if (result.translation) {
            resultCallback(result.translation);
          } else {
            resultCallback(false, "Apertium Error: " + result.error.message);
          }
        });
      });
    }

  };
})(jQuery);
