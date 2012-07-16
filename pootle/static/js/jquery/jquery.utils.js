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

})(jQuery);
