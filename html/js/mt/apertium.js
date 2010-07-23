/*
 * Apertium Service
 */

$(document).ready(function() {
  var target_lang = $.pootle.normalize_code($("#id_target_f_0").attr("lang"));

  if (apertium.isTranslatable(target_lang)) {
    $.pootle.addMTButton($(".translate-toolbar"),
                         "apertium",
                         "/html/images/apertium.png",
                         "Apertium");

    $(".apertium").click(function(){
      var areas = $("[id^=id_target_f_]");
      var sources = $(this).parent().siblings(".translation-text");
      var lang_from = $.pootle.normalize_code(sources.eq(0).attr("lang"));
      var lang_to = $.pootle.normalize_code(areas.eq(0).attr("lang"));

      // The printf regex based on http://phpjs.org/functions/sprintf:522
      var c_printf_pattern = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
      var csharp_string_format_pattern = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
      var percent_number_pattern = /%\d+/g;
      var pos = 0;
      var argument_subs = new Array();

      $(sources).each(function(j) {
        source_text = source_text.replace(c_printf_pattern, $.pootle.collectArguments);
        source_text = source_text.replace(csharp_string_format_pattern, $.pootle.collectArguments);
        source_text = source_text.replace(percent_number_pattern, $.pootle.collectArguments);

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
            $.pootle.toggleFuzzy(true);
            $.pootle.toggleFuzzyBox(true);
          } else {
            alert("Apertium Error: " + result.error.message);
          }
        });
      });
      return false;
    });
  }

});
