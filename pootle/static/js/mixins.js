window.PTL = window.PTL || {};

PTL.mixins = PTL.mixins || {};


/* Mixin to handle Django forms */
PTL.mixins.Forms = {

  displayErrors: function (xhr) {
    var errors = $.parseJSON(xhr.responseText).errors;
    $('ul.errorlist').remove();

    for (var fieldName in errors) {
      this.validationError(fieldName, errors[fieldName]);
    }
  },

  /* Injects a form validation error next to the input it failed to
   * validate */
  validationError: function (fieldName, msgs) {
    var $field = $('#id_' + fieldName),
        errorList = ['<ul class="errorlist">'];
    for (var i=0; i<msgs.length; i++) {
      errorList.push(['<li>', msgs[i], '</li>'].join(''));
    }
    errorList.push(['</ul>']);

    $field.after(errorList.join(''));
  }

};
