$(document).ready(function() {

/* Pootle namespace */
  $.pootle = {};


/*
 * FOCUS
 */

  // Set initial focus on page load
  var initialFocus = $(".translate-original-focus textarea");
  $.pootle.focusedElement = initialFocus.get(0);
  if ($.pootle.focusedElement != null) {
      $.pootle.focusedElement.focus();
  }

  // Update focus when appropriate
  $(".focusthis").live("focus", function(e) {
    $.pootle.focusedElement = e.target;
  });


/*
 * REPLACEMENTS
 */

  // Write TM results into the currently focused element
  $(".writetm").live("click", function() {
    var tmtext = $(".tm-translation", this).text();
    var element = $($.pootle.focusedElement);
    var start = element.caret().start + tmtext.length;
    element.val(element.caret().replace(tmtext));
    element.caret(start, start);
  });

  // Write special chars, tags and escapes into the currently focused element
  $(".writespecial, .translate-full .translation-highlight-escape, .translate-full .translation-highlight-html").live("click", function() {
    var specialtext = $(this).text();
    var element = $($.pootle.focusedElement);
    var start = element.caret().start + specialtext.length;
    element.val(element.caret().replace(specialtext));
    element.caret(start, start);
  });


/*
 * COPY ORIGINAL TRANSLATION
 */

  $("a.copyoriginal").live("click", function() {
    var sources = $(".translation-text", $(this).parent().parent().parent());
    var clean_sources = [];
    $.each(sources, function(i) {
      clean_sources[i] = $(this).text()
                                .replace("\n", "\\n\n", "g")
                                .replace("\t", "\\t", "g");
    });

    var targets = $("[id^=id_target_f_]");
    if (targets.length) {
      var max = clean_sources.length - 1;
      for (var i=0; i<targets.length; i++) {
        var newval = clean_sources[i] || clean_sources[max];
        $(targets.get(i)).val(newval);
      }
      $(targets).get(0).focus();
      $.pootle.goFuzzy();
    }
  });


/*
 * UNFUZZY
 */

  keepstate = false;
  $("textarea.translation").live("keyup blur", function() {
    if (!keepstate && $(this).attr("defaultValue") != $(this).val()) {
      $.pootle.ungoFuzzy();
    }
  });

  $("input.fuzzycheck").live("click", function() {
    if ($.pootle.isFuzzy()) {
      $.pootle.doFuzzyArea();
    } else {
      $.pootle.undoFuzzyArea();
    }
  });

  $.pootle.doFuzzyArea = function() {
    $("tr.translate-translation-row").addClass("translate-translation-fuzzy");
  };

  $.pootle.undoFuzzyArea = function() {
    $("tr.translate-translation-row").removeClass("translate-translation-fuzzy");
  };

  $.pootle.doFuzzyBox = function() {
    var checkbox = $("input.fuzzycheck");
    if (!$.pootle.isFuzzy()) {
      checkbox.attr("checked", "checked");
    }
  };

  $.pootle.undoFuzzyBox = function() {
    var checkbox = $("input.fuzzycheck");
    if ($.pootle.isFuzzy()) {
      checkbox.removeAttr("checked");
    }
  };

  $.pootle.goFuzzy = function() {
    if (!$.pootle.isFuzzy()) {
      keepstate = true;
      $.pootle.doFuzzyArea();
      $.pootle.doFuzzyBox();
    }
  };

  $.pootle.ungoFuzzy = function() {
    if ($.pootle.isFuzzy()) {
      keepstate = true;
      $.pootle.undoFuzzyArea();
      $.pootle.undoFuzzyBox();
    }
  };

  $.pootle.isFuzzy = function() {
    var checkbox = $("input.fuzzycheck");
    var checked = checkbox.attr("checked");
    if (checked == undefined || checked == false) {
      return false;
    } else {
      return true;
    }
  };


/*
 * SUGGESTIONS
 */

/* REVIEWING SUGGESTIONS */

  function handlesuggestions(url, data) {
    $.post(url,
           {data: JSON.stringify(data)},
           function(rdata) {
             $("#response").remove();
             if (rdata.status == "success") {
               // Remove processed suggestion
               $.each(rdata.del_ids, function() {
                 var deleted = this[0] + "-" + this[1];
                 $("#suggestion" + deleted).fadeOut(500);
               });
               // If it's an accept, then update the textareas
               if (rdata.hasOwnProperty("accepted_id")) {
                 var textareas = $("#translate-suggestion-container").siblings("textarea");
                 var accepted= rdata.accepted_id[0] + "-" + rdata.accepted_id[1];
                 var inputs = $("#suggestion" + accepted + " .translate-suggestion").children().siblings("input");
                 $.each(textareas, function(i) {
                   $(this).val(inputs.eq(i).val());
                 });
               }
               // If there are no more suggestions left, remove
               // the current translation block.
               if (!rdata.diffs.hasOwnProperty("0")) {
                 $("#translate-original-container").fadeOut(500);
               }
               // Update current diff otherwise
               else {
                 var current = $("#translate-original-container .translate-original-block");
                 var forms = rdata.diffs;
                 $.each(current, function() {
                   var insertat = $("div", this);
                   $.each(forms, function() {
                     $(insertat).html(this.diff);
                   });
                 });
               }
             }
           }, "json");
  }

    $("#translate-suggestion-container .rejectsugg").live("click", function() {
      var element = $(this).parent().parent();
      var uid = $('.translate-container input#id_id').val();
      var suggid = $(this).siblings("input.suggid").val();
      var url = l('/suggestion/reject/') + uid + '/' + suggid;
      $.post(url, {'reject': 1},
             function(rdata) {
               $("#response").remove();
               element.fadeOut(500);
             }, "json");
      return false;
    });

    $("#translate-suggestion-container .acceptsugg").live("click", function() {
      var element = $(this).parent().parent();
      var uid = $('.translate-container input#id_id').val();
      var suggid = $(this).siblings("input.suggid").val();
      var url = l('/suggestion/accept/') + uid + '/' + suggid;
      $.post(url, {'accept': 1},
             function(rdata) {
               $("#response").remove();
               $.each(rdata.newtargets, function(i, target) {
                 $("textarea#id_target_f_" + i).val(target).focus();
               });
               $.each(rdata.newdiffs, function(suggid, sugg) {
                 $.each(sugg, function(i, target) {
                   $("#suggdiff-" + suggid + "-" + i).html(target);
                 });
               });
               element.fadeOut(500);
             }, "json");
      return false;
    });

    $("#translate-checks-block .rejectcheck").live("click", function() {
      var element = $(this).parent();
      var checkid = $(this).siblings("input.checkid").val();
      var uid = $('.translate-container input#id_id').val();
      var url = l('/qualitycheck/reject/') + uid + '/' + checkid;
      $.post(url, {'reject': 1},
             function(rdata) {
               $("#response").remove();
               element.fadeOut(500);
             }, "json");
      return false;
    });

/*
 * HELPER FUNCTIONS
 */

  $(".collapse").live("click", function(event) {
    event.preventDefault();
    $(this).siblings(".collapsethis").slideToggle("fast");
    if ($("textarea", $(this).next("div.collapsethis")).length) {
      $("textarea", $(this).next("div.collapsethis")).focus();
    }
  });

  $.pootle.isSupportedSource = function(pairs, source) {
    for (var i in pairs) {
      if (source == pairs[i].source) {
        return true;
      }
    }
    return false;
  };

  $.pootle.isSupportedTarget = function(pairs, target) {
    for (var i in pairs) {
      if (target == pairs[i].target) {
        return true;
      }
    }
    return false;
  };

  $.pootle.isSupportedPair = function(pairs, source, target) {
    for (var i in pairs) {
      if (source == pairs[i].source &&
          target == pairs[i].target) {
        return true;
      }
    }
    return false;
  };

  $.pootle.addMTButton = function(element, aclass, imgfn, tooltip) {
      var a = document.createElement("a");
      a.setAttribute("class", "translate-mt " + aclass);
      var img = document.createElement("img");
      img.setAttribute("src", imgfn);
      img.setAttribute("title", tooltip);
      a.appendChild(img);
      element.prepend(a);
  };

  $.pootle.normalize_code = function(locale) {
      var clean = locale.replace('_', '-')
      var atIndex = locale.indexOf("@");
      if (atIndex != -1) {
        clean = clean.slice(0, atIndex);
      }
      return clean;
  };

  $.pootle.collectArguments = function(substring) {
    if (substring == '%%') {
      return '%%';
    }
    argument_subs[pos] = substring;
    substitute_string = "__" + pos + "__";
    pos = pos + 1;
    return substitute_string;
  };

});
