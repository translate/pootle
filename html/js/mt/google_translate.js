(function($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.google_translate = {

    url: "http://www.google.com/jsapi",
    cookie_name: "google_pairs",
    cookie_options: {path: '/', expires: 15},

    init: function(apikey) {
      var _this = PTL.editor.mt.google_translate;
      /* Load Google Translate library */
      _this.url = PTL.editor.settings.secure == false ? _this.url : _this.url.replace("http", "https");

      $.getScript(_this.url, function() {
        //google.load("language", "1");
        /* Init variables */
        var _this = PTL.editor.mt.google_translate;
        _this.target_lang = PTL.editor.normalize_code($("#id_target_f_0").attr("lang"));
        _this.pairs = $.cookie(_this.cookie_name);
        if (!_this.pairs) {
          _this.pairs = [];
          $.each(google.language.Languages, function(k, v) {
            if (v != "" && google.language.isTranslatable(v)) {
              _this.pairs.push({source: v, target: v});
            }
          });
          var cookie_data = JSON.stringify(_this.pairs);
          $.cookie(_this.cookie_name, cookie_data, _this.cookie_options);
        } else {
          _this.pairs = $.parseJSON(_this.pairs);
        }

        /* Bind event handler */
        $(".googletranslate").live("click", _this.translate);
      });
    },

    ready: function() {
      var _this = PTL.editor.mt.google_translate;

      if (PTL.editor.isSupportedTarget(_this.pairs, _this.target_lang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function() {
          var source = PTL.editor.normalize_code($(this).attr("lang"));
          if (PTL.editor.isSupportedSource(_this.pairs, _this.source)) {
            PTL.editor.addMTButton($(this).parent().siblings().children(".translate-toolbar"),
                                 "googletranslate",
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

        var content = new Object();
        content.text = source_text;
        content.type = "text";
        google.language.translate(content, lang_from, lang_to, function(result) {
          if (result.translation) {
            var translation = result.translation;
            for (var i=0; i<argument_subs.length; i++)
              translation = translation.replace("__" + i + "__", argument_subs[i]);
            areas.eq(j).val(translation);
            areas.eq(j).focus();
          } else {
            alert("Google Translate Error: " + result.error.message);
          }
        });
      });
      PTL.editor.goFuzzy();
      return false;
    }
  };
})(jQuery);
