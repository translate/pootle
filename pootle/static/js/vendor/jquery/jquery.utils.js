/*
 * Several utilities that extend jQuery's functionalities.
 */


var Spinner = require('spin');


(function ($) {

  $.fn.spin = function(opts) {
    this.each(function () {
      var $this = $(this),
          data = $this.data();

      if (data.spinner) {
        data.spinner.stop();
        delete data.spinner;
      }
      if (opts !== false) {
        data.spinner = new Spinner($.extend({color: $this.css('color')},
                                             opts)).spin(this);
      }
    });
    return this;
  };

})(jQuery);
