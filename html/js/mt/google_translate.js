(function($) {
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

    init: function(apikey) {
      /* Prepare URL for requests. */
      this.url = PTL.editor.settings.secure == false ? this.url : this.url.replace("http", "https");
      this.url += "?callback=?";
      /* Set target language */
      this.target_lang = PTL.editor.normalize_code($("#id_target_f_0").attr("lang"));
      /* Bind event handler */
      $(".googletranslate").live("click", this.translate);
    },

    ready: function() {
      var _this = PTL.editor.mt.google_translate;

      if (PTL.editor.isSupportedTarget(_this.pairs, _this.target_lang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function() {
          var source = PTL.editor.normalize_code($(this).attr("lang"));
          if (PTL.editor.isSupportedSource(_this.pairs, source)) {
            PTL.editor.addMTButton("googletranslate",
                                   m("images/google-translate.png"),
                                   "Google Translate");
          }
        });
      }
    },

    translate: function() {
      var areas = $("[id^=id_target_f_]");
      var sources = $(this).parent().parent().siblings().children(".translation-text");
      var lang_from = PTL.editor.normalize_code(sources.eq(0).attr("lang"));
      var lang_to = PTL.editor.normalize_code(areas.eq(0).attr("lang"));

      // The printf regex based on http://phpjs.org/functions/sprintf:522
      var c_printf_pattern = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
      var csharp_string_format_pattern = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
      var percent_number_pattern = /%\d+/g;
      var pos = 0;
      var argument_subs = new Array();

      $(sources).each(function(j) {
        var source_text = $(this).text();
        source_text = source_text.replace(c_printf_pattern, PTL.editor.collectArguments);
        source_text = source_text.replace(csharp_string_format_pattern, PTL.editor.collectArguments);
        source_text = source_text.replace(percent_number_pattern, PTL.editor.collectArguments);

        var trans_data = {v: '1.0', q: source_text,
                         langpair: lang_from + '|' + lang_to}
        $.getJSON(PTL.editor.mt.google_translate.url, trans_data, function(r) {
          if (r.responseData && r.responseStatus == 200) {
            var translation = r.responseData.translatedText;
            for (var i=0; i<argument_subs.length; i++)
              translation = translation.replace("__" + i + "__", argument_subs[i]);
            areas.eq(j).val($("<div />").html(translation).text());
            areas.eq(j).focus();
          } else {
            PTL.editor.error("Google Translate Error: " + r.responseDetails);
          }
        });
      });
      PTL.editor.goFuzzy();
      return false;
    }
  };
})(jQuery);
