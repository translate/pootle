/*
 * Apertium Service
 */

$(document).ready(function() {
  var target_lang = $("#id_target_f_0").attr("lang").replace('_', '-');

  if (apertium.isTranslatable(target_lang)) {
    $.pootle.addMTButton("apertium", "/html/images/apertium.png", "Apertium");

    $(".apertium").click(function(){
      var orig = $("#id_source_f_0");
      var area = $("#id_target_f_0");
      var orig_text = orig.val();
      var lang_from = "en";
      var lang_to = area.attr("lang").replace('_', '-');

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
      orig_text = orig_text.replace(c_printf_pattern, collectArguments);
      orig_text = orig_text.replace(csharp_string_format_pattern, collectArguments);
      orig_text = orig_text.replace(percent_number_pattern, collectArguments);

      var content = new Object()
      content.text = orig_text;
      content.type = "txt";
      apertium.translate(content, lang_from, lang_to, function(result) {
        if (result.translation) {
          var translation = result.translation;
          for (var i=0; i<argument_subs.length; i++)
            translation = translation.replace("__" + i + "__", argument_subs[i]);
          area.val(translation);
          area.parent().parent().addClass("translate-translation-fuzzy");
          var checkbox = $("input.fuzzycheck");
          checkbox.attr("checked", "checked");
          area.focus();
          keepstate = true;
        } else {
          alert("Apertium Error: " + result.error.message);
        }
      });
      return false;
    });
  }

});
