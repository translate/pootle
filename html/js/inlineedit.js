tpagestart = function(first, last, currurl){
 editfun = function(value, settings) {
    newtext = value;
    ln = settings.linenum;

    // Prepare the data for posting
    data = {};
    data["trans"+ln] = newtext
    if (settings.submitdata["stype"] == "submit") {
      data["submit"+ln] = "Submit";
    }
    if (settings.submitdata["stype"] == "suggest") {
      data["submitsuggest"+ln] = "Suggest";
    }

    // Post the data
    $.post(currurl, data);

    // Return the submitted value so the page updates
    if (settings.submitdata["stype"] == "submit") {
      $(settings.fuzzydiv).removeClass("translate-translation-fuzzy");
      return(value);
    }
    if (settings.submitdata["stype"] == "suggest") {
      $(settings.sugglink).hide("normal");
      scount = $(settings.sugglink).children(".scount");
      scount.html(parseInt(scount.html())+1)
      $(settings.sugglink).show("normal");

      $(settings.suggdiv).children(".sugglist").append("<li></li>");
      // value might have XSS, so it better be added as text
      $(settings.suggdiv).children(".sugglist").children("li:last-child").text(value);
      $(settings.suggdiv).children(".sugglist").children("li:last-child").prepend("<span class=\"suggauthor\" dir=\"ltr\">(NEW)</span></li>");
      
      return(settings.original);
    }
 };

// Set up the script for each 
  for (ln = first; last >= ln; ln++) { // For each translation idem
    etrans = $(".edittrans"+ln);
    if (etrans.length > 0) { // If a stock, no plural class exists, its singular
      etrans.editable(editfun, {
        allowsuggest: etrans.hasClass("suggestable"), 
        allowsubmit : etrans.hasClass("submitable"),
        suggdiv     : etrans.siblings(".suggestions"),
        sugglink    : etrans.siblings(".sugglink"),
        fuzzydiv    : etrans.parent(".translate-translation-fuzzy"),
        linenum     : ln,
        event       : 'dblclick',
        original    : etrans[0].innerHTML,
        type        : 'translator',
        onblur      : 'ignore',
        indicator   : 'Saving...',
        placeholder : '<span class="placeholder">Add translation</span>',
        width       : 250,
        autogrow    : {
                       lineHeight : 16,
                       maxHeight  : 512
                      }
      });
    } else {
    // FIXME Plurals aren't working right now, as it only provides a suggestion
    // for one form, which leads to index out of bounds errors when you try and
    // view that suggestion.

    /*
      for (pn = 0; 6 > pn; pn++) { // Otherwise, loop through plurals
        ptrans = $(".edittrans"+ln+"p"+pn);
        if (ptrans.length > 0) {
          ptrans.editable(editfun, {
            allowsuggest: ptrans.hasClass("suggestable"), 
            allowsubmit : ptrans.hasClass("submitable"), 
            suggdiv     : ptrans.parent().siblings(".suggestions"),
            sugglink    : ptrans.parent().siblings(".sugglink"),
            fuzzydiv    : etrans.parent().parent(".translate-translation-fuzzy"),
            linenum     : ln+"."+pn,
            event       : 'dblclick',
            original    : ptrans[0].innerHTML,
            type        : 'translator',
            onblur      : 'cancel',
            indicator   : 'Saving...',
            placeholder : '<span class="placeholder">Add translation</span>',
            autogrow    : {
                           lineHeight : 16,
                           maxHeight  : 512
                          }
          });
        } else {
          break; // The second we find we missed a plural, abort the loop
        }
      }
    */
    }
  }
};

$(document).ready(function(){

  // Define a custom translator type for jeditable
  $.editable.addInputType('translator', {
    element : function(settings, original) {
      var textarea = $('<textarea>');
      if (settings.rows) {
        textarea.attr('rows', settings.rows);
      } else {
        textarea.height(settings.height);
      }
      if (settings.cols) {
        textarea.attr('cols', settings.cols);
      } else {
        textarea.width(settings.width);
      }
      $(this).append(textarea);
      return(textarea);
    },
    plugin : function(settings, original) {
      $('textarea', this).autogrow(settings.autogrow);
    },
    buttons : function(settings, original) {

      if (settings.allowsuggest) {
        // Add a suggest button
        var suggest = $('<input type="button">');
        suggest.val("Suggest");
        $(this).append(suggest);
      
        // Configure suggest button
        form = this;
        $(suggest).click(function(e) {
          e.preventDefault();
          settings.submitdata["stype"] = "suggest"
          form.submit();
          return false;
        });
      }


      if (settings.allowsubmit) {
        // Add a submit button
        var submit = $('<input type="button">');
        submit.val("Submit");
        $(this).append(submit);
      
        // Configure submit button
        form = this;
        $(submit).click(function(e) {
          e.preventDefault();
          settings.submitdata["stype"] = "submit"
          form.submit();
          return false;
        });
      }

      // Add a cancel link
      settings.cancel = '<a href="#" class="cancellink">Cancel</a>';
      settings.submit = null; 
      var default_buttons = $.editable.types['defaults'].buttons
      default_buttons.apply(this, [settings, original]);

      
    }
  });
});
