(function($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.apertium = {

    url: "http://api.apertium.org/JSLibrary.js",
    cookieName: "apertium_pairs",
    cookieOptions: {path: '/', expires: 15},

    init: function(apiKey) {
      var _this = PTL.editor.mt.apertium;
      /* Load Apertium library */
      _this.url = apiKey == undefined ? _this.url : _this.url + '?key=' + apiKey;
      $.getScript(_this.url, function() {
        /* Init variables */
        var _this = PTL.editor.mt.apertium;
        _this.targetLang = PTL.editor.normalizeCode($("div#target_lang").text());

        _this.pairs = $.cookie(_this.cookieName);
        if (!_this.pairs) {
          var pairs = apertium.getSupportedLanguagePairs();
          _this.pairs = $.map(pairs, function(obj, i) {
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

    ready: function() {
      var _this = PTL.editor.mt.apertium;
      if (PTL.editor.isSupportedTarget(_this.pairs, _this.targetLang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function() {
          var source = PTL.editor.normalizeCode($(this).attr("lang"));
          if (PTL.editor.isSupportedPair(_this.pairs, source, _this.targetLang)) {
            PTL.editor.addMTButton("apertium",
                                   m("images/apertium.png"),
                                   "Apertium");
          }
        });
      }
    },

    translate: function() {
      var areas = $("[id^=id_target_f_]");
      var sources = $(this).parent().parent().siblings().children(".translation-text");
      var langFrom = PTL.editor.normalizeCode(sources.eq(0).attr("lang"));
      var langTo = PTL.editor.normalizeCode(areas.eq(0).attr("lang"));

      // The printf regex based on http://phpjs.org/functions/sprintf:522
      var cPrintfPat = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
      var csharpStrPat = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
      var percentNumberPat = /%\d+/g;
      var pos = 0;
      var argSubs = new Array();

      $(sources).each(function(j) {
        var sourceText = $(this).text();
        sourceText = sourceText.replace(cPrintfPat, PTL.editor.collectArguments);
        sourceText = sourceText.replace(csharpStrPat, PTL.editor.collectArguments);
        sourceText = sourceText.replace(percentNumberPat, PTL.editor.collectArguments);

        var content = new Object()
        content.text = sourceText;
        content.type = "txt";
        apertium.translate(content, langFrom, langTo, function(result) {
          if (result.translation) {
            var translation = result.translation;
            for (var i=0; i<argSubs.length; i++)
              translation = translation.replace("__" + i + "__", argSubs[i]);
            areas.eq(j).val(translation);
            areas.eq(j).focus();
          } else {
            PTL.editor.displayError("Apertium Error: " + result.error.message);
          }
        });
      });
      PTL.editor.goFuzzy();
      return false;
    }
  };
})(jQuery);
