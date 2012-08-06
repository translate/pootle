/*
 * Several utilities that extend jQuery's functionalities.
 */
(function ($) {

  /* Returns the selector if it has any matching nodes, otherwise returns false.
   * Source:
   * http://stackoverflow.com/questions/7228464/find-fallback-element-in-jquery
   */
  $.fn.ifExists = function () {
    if (this.length > 0) {
      return this;
    }
    return false;
  };

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
