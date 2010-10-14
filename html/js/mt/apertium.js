(function($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.apertium = {

    url: "http://api.apertium.org/JSLibrary.js",
    cookie_name: "apertium_pairs",
    cookie_options: {path: '/', expires: 15},

    init: function(apikey) {
      var _this = PTL.editor.mt.apertium;
      /* Load Apertium library */
      _this.url = apikey == undefined ? _this.url : _this.url + '?key=' + apikey;
      $.getScript(_this.url, function() {
        /* Init variables */
        var _this = PTL.editor.mt.apertium;
        _this.target_lang = PTL.editor.normalize_code($("#id_target_f_0").attr("lang"));

        _this.pairs = $.cookie(_this.cookie_name);
        if (!_this.pairs) {
          var pairs = apertium.getSupportedLanguagePairs();
          _this.pairs = $.map(pairs, function(obj, i) {
            return {source: obj.source, target: obj.target};
          });
          var cookie_data = JSON.stringify(_this.pairs);
          $.cookie(_this.cookie_name, cookie_data, _this.cookie_options);
        } else {
          _this.pairs = $.parseJSON(_this.pairs);
        }

        /* Bind event handler */
        $(".apertium").live("click", _this.translate);
      });

    },

    ready: function() {
      var _this = PTL.editor.mt.apertium;
      if (PTL.editor.isSupportedTarget(_this.pairs, _this.target_lang)) {
        var sources = $("div.placeholder").prev(".translation-text");
        $(sources).each(function() {
          var source = PTL.editor.normalize_code($(this).attr("lang"));
          if (PTL.editor.isSupportedPair(_this.pairs, source, _this.target_lang)) {
            PTL.editor.addMTButton($(this).parent().siblings().children(".translate-toolbar"),
                                   "apertium",
                                   m("images/apertium.png"),
                                   "Apertium");
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

        var content = new Object()
        content.text = source_text;
        content.type = "txt";
        apertium.translate(content, lang_from, lang_to, function(result) {
          if (result.translation) {
            var translation = result.translation;
            for (var i=0; i<argument_subs.length; i++)
              translation = translation.replace("__" + i + "__", argument_subs[i]);
            areas.eq(j).val(translation);
            areas.eq(j).focus();
          } else {
            alert("Apertium Error: " + result.error.message);
          }
        });
      });
      PTL.editor.goFuzzy();
      return false;
    }
  };
})(jQuery);
