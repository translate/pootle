/*
 * GOOGLE TRANSLATE Service
 */
google.load("language", "1");

google.setOnLoadCallback(function() {
  var target_lang = $("#id_target_f_0").attr("lang").replace('_', '-');

  if (google.language.isTranslatable(target_lang)) {
    var sources = $(".translate-toolbar").prev(".translation-text");
    $(sources).each(function() {
      var source = $(this).attr("lang");
      if (google.language.isTranslatable(source)) {
        $.pootle.addMTButton($(this).siblings(".translate-toolbar"),
                             "googletranslate",
                             "/html/images/google-translate.png",
                             "Google Translate");
      }
    });

    $(".googletranslate").click(function(){
      var area = $("#id_target_f_0");
      var source = $(this).parent().siblings(".translation-text");
      var source_text = source.text();
      var lang_from = $.pootle.normalize_code(source.attr("lang"));
      /*var lang_from = "en";*/
      var lang_to = $.pootle.normalize_code(area.attr("lang"));

      // The printf regex based on http://phpjs.org/functions/sprintf:522
      var c_printf_pattern = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
      var csharp_string_format_pattern = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
      var percent_number_pattern = /%\d+/g;
      var pos = 0;
      var argument_subs = new Array();
      var collectArguments = function (substring) {
        if (substring == '%%') {
          return '%%';
        }
        argument_subs[pos] = substring;
        substitute_string = "__" + pos + "__";
        pos = pos + 1;
        return substitute_string;
      }
      source_text = source_text.replace(c_printf_pattern, collectArguments);
      source_text = source_text.replace(csharp_string_format_pattern, collectArguments);
      source_text = source_text.replace(percent_number_pattern, collectArguments);

      var content = new Object()
      content.text = source_text;
      content.type = "text";
      google.language.translate(content, lang_from, lang_to, function(result) {
        if (result.translation) {
          var translation = result.translation;
          for (var i=0; i<argument_subs.length; i++)
            translation = translation.replace("__" + i + "__", argument_subs[i]);
          area.val(translation);
          area.focus();
          $.pootle.toggleFuzzy(true);
          $.pootle.toggleFuzzyBox(true);
        } else {
          alert("Google Translate Error: " + result.error.message);
        }
      });
      return false;
    });
  }

});
