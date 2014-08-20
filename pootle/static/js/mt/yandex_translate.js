(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.yandex_translate = {

    buttonClassName: "yandex-translate",
    hint: "Yandex.Translate",
    validatePair: false,

    /* using Yandex.Tanslate API v1.5 */
    url: "https://translate.yandex.net/api/v1.5/tr.json/translate",

    /* For a list of currently supported languages:
     * http://api.yandex.ru/translate/langs.xml
     *
     * Yandex supports translations between any of the supported languages
     * (any combination is acceptable)
     *
     */

    supportedLanguages: [
      'az', 'be', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'et',
      'fi', 'fr', 'hr', 'hu', 'hy', 'it', 'lt', 'lv', 'mk', 'nl', 'no',
      'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'tr', 'uk'
    ],

    init: function (apiKey) {
      /* Init variables */
      this.pairs = [];
      for (var i=0; i<this.supportedLanguages.length; i++) {
        this.pairs.push({
          'source': this.supportedLanguages[i],
          'target': this.supportedLanguages[i]
        });
      };

      /* Prepare URL for requests. */
      this.url += "?callback=?";
      /* Set API key */
      this.apiKey = apiKey;
      /* Bind event handler */
      $(document).on("click", ".yandex-translate", this.translate);
    },

    ready: function () {
      PTL.editor.addMTButtons(PTL.editor.mt.yandex_translate);
    },

    translate: function () {
      PTL.editor.translate(this, function(sourceText, langFrom, langTo, resultCallback) {
        var transData = {key: PTL.editor.mt.yandex_translate.apiKey,
                         text: sourceText,
                         lang: langFrom+"-"+langTo};
        $.jsonp({
          url: PTL.editor.mt.yandex_translate.url,
          data: transData,
          success: function (r) {
            if (r.text) {
              resultCallback({
                translation: r.text[0]
              });
            } 
          },
          error: function (dbg, textStatus) {
            if(textStatus == "timeout")
            {
              resultCallback({
                msg: "Yandex.Translate: timeout"
              });
            } 
            else {
              resultCallback({
                msg: "Yandex.Translate: error"
              });
            } 
          }
        });
      });
    }
  };
})(jQuery);
