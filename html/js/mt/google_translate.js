(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.google_translate = {

    url: "http://ajax.googleapis.com/ajax/services/language/translate",
    pairs: [{"source":"af","target":"af"},
            {"source":"sq","target":"sq"},
            {"source":"ar","target":"ar"},
            {"source":"be","target":"be"},
            {"source":"bg","target":"bg"},
            {"source":"ca","target":"ca"},
            {"source":"zh","target":"zh"},
            {"source":"zh-CN","target":"zh-CN"},
            {"source":"zh-TW","target":"zh-TW"},
            {"source":"hr","target":"hr"},
            {"source":"cs","target":"cs"},
            {"source":"da","target":"da"},
            {"source":"nl","target":"nl"},
            {"source":"en","target":"en"},
            {"source":"et","target":"et"},
            {"source":"tl","target":"tl"},
            {"source":"fi","target":"fi"},
            {"source":"fr","target":"fr"},
            {"source":"gl","target":"gl"},
            {"source":"de","target":"de"},
            {"source":"el","target":"el"},
            {"source":"ht","target":"ht"},
            {"source":"iw","target":"iw"},
            {"source":"hi","target":"hi"},
            {"source":"hu","target":"hu"},
            {"source":"is","target":"is"},
            {"source":"id","target":"id"},
            {"source":"ga","target":"ga"},
            {"source":"it","target":"it"},
            {"source":"ja","target":"ja"},
            {"source":"ko","target":"ko"},
            {"source":"lv","target":"lv"},
            {"source":"lt","target":"lt"},
            {"source":"mk","target":"mk"},
            {"source":"ms","target":"ms"},
            {"source":"mt","target":"mt"},
            {"source":"no","target":"no"},
            {"source":"fa","target":"fa"},
            {"source":"pl","target":"pl"},
            {"source":"pt","target":"pt"},
            {"source":"pt-PT","target":"pt-PT"},
            {"source":"ro","target":"ro"},
            {"source":"ru","target":"ru"},
            {"source":"sr","target":"sr"},
            {"source":"sk","target":"sk"},
            {"source":"sl","target":"sl"},
            {"source":"es","target":"es"},
            {"source":"sw","target":"sw"},
            {"source":"sv","target":"sv"},
            {"source":"tl","target":"tl"},
            {"source":"th","target":"th"},
            {"source":"tr","target":"tr"},
            {"source":"uk","target":"uk"},
            {"source":"vi","target":"vi"},
            {"source":"cy","target":"cy"},
            {"source":"yi","target":"yi"}],

    init: function (apiKey) {
      /* Prepare URL for requests. */
      this.url = PTL.editor.settings.secure == false ? this.url : this.url.replace("http", "https");
      this.url += "?callback=?";
      /* Set target language */
      this.targetLang = PTL.editor.normalizeCode($("div#target_lang").text());
      /* Bind event handler */
      $(".googletranslate").live("click", this.translate);
    },

    ready: function () {
      var _this = PTL.editor.mt.google_translate;

      if (PTL.editor.isSupportedTarget(_this.pairs, _this.targetLang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function () {
          var source = PTL.editor.normalizeCode($(this).attr("lang"));
          if (PTL.editor.isSupportedSource(_this.pairs, source)) {
            PTL.editor.addMTButton("googletranslate",
                                   m("images/google-translate.png"),
                                   "Google Translate");
          }
        });
      }
    },

    collectArguments: function (s) {
      this.argSubs[this.argPos] = s;
      return "__" + (this.argPos++) + "__";
    },

    translate: function () {
      var areas = $("[id^=id_target_f_]");
      var sources = $(this).parent().parent().siblings().children(".translation-text");
      var langFrom = PTL.editor.normalizeCode(sources.eq(0).attr("lang"));
      var langTo = PTL.editor.normalizeCode(areas.eq(0).attr("lang"));

      var htmlPat = /<[\/]?\w+.*?>/g;
      // The printf regex based on http://phpjs.org/functions/sprintf:522
      var cPrintfPat = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
      var csharpStrPat = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
      var percentNumberPat = /%\d+/g;
      var pos = 0;

      var _this = PTL.editor.mt.google_translate;

      $(sources).each(function (j) {
        var sourceText = $(this).text();

        // Reset collected arguments array and counter
        _this.argSubs = new Array();
        _this.argPos = 0;

        // Walk through known patterns and replace them with __N__ placeholders
        // for Google Translate to be happy
        
        sourceText = sourceText.replace(htmlPat, function(s) { return _this.collectArguments(s) });
        sourceText = sourceText.replace(cPrintfPat, function(s) { return _this.collectArguments(s) });
        sourceText = sourceText.replace(csharpStrPat, function(s) { return _this.collectArguments(s) });
        sourceText = sourceText.replace(percentNumberPat, function(s) { return _this.collectArguments(s) });

        var transData = {v: '1.0', q: sourceText,
                         langpair: langFrom + '|' + langTo}
        $.getJSON(PTL.editor.mt.google_translate.url, transData, function (r) {
          if (r.responseData && r.responseStatus == 200) {
            var translation = r.responseData.translatedText;

            // Replace temporary __N__ placeholders back to their real values
            for (var i = 0; i < _this.argSubs.length; i++) {
              translation = translation.replace("__" + i + "__", _this.argSubs[i]);
            }

            areas.eq(j).val($("<div />").html(translation).text());
            areas.eq(j).focus();
          } else {
            PTL.editor.displayError("Google Translate Error: " + r.responseDetails);
          }
        });
      });
      PTL.editor.goFuzzy();
      return false;
    }
  };
})(jQuery);
