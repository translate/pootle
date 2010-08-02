/*
 * GOOGLE TRANSLATE Service
 */
google.load("language", "1");

google.setOnLoadCallback(function() {
  var target_lang = $.pootle.normalize_code($("#id_target_f_0").attr("lang"));

  var cookie_name = "google_pairs";
  var cookie_options = {path: '/', expires: 15};
  var code_map = {'fl': 'tl', 'he': 'iw'};
  var pairs = $.cookie(cookie_name);
  if (!pairs) {
    var pairs = [];
    $.each(google.language.Languages, function(k, v) {
      if (v != "" && google.language.isTranslatable(v)) {
        pairs.push({source: v, target: v});
      }
    });
    var cookie_data = JSON.stringify(pairs);
    $.cookie(cookie_name, cookie_data, cookie_options);
  } else {
    pairs = $.parseJSON(pairs);
  }

  if ($.pootle.isSupportedTarget(pairs, target_lang)) {
    var sources = $(".translate-toolbar").prev(".translation-text");
    $(sources).each(function() {
      var source = $.pootle.normalize_code($(this).attr("lang"));
      if ($.pootle.isSupportedSource(pairs, source)) {
        $.pootle.addMTButton($(this).siblings(".translate-toolbar"),
                             "googletranslate",
                             "/html/images/google-translate.png",
                             "Google Translate");
      }
    });

    $(".googletranslate").click(function() {
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
        var source_text = $(this).text();
        source_text = source_text.replace(c_printf_pattern, $.pootle.collectArguments);
        source_text = source_text.replace(csharp_string_format_pattern, $.pootle.collectArguments);
        source_text = source_text.replace(percent_number_pattern, $.pootle.collectArguments);

        var content = new Object()
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
      $.pootle.goFuzzy();
      return false;
    });

  }

});
