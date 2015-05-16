(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.yandex_translate = {

    buttonClassName: "yandex-translate",
    hint: "Yandex.Translate",
    validatePair: false,

    /* using Yandex.Tanslate API v1.5 */
    url: "https://translate.yandex.net/api/v1.5/tr.json/translate",

    /* For a list of currently supported languages:
     * https://tech.yandex.com/translate/doc/dg/concepts/langs-docpage/
     * The service translates between any of these listed languages.
     *
     * For a list of language pairs:
     * https://translate.yandex.net/api/v1.5/tr.json/getLangs?key=API_KEY
     * The results returned indicate permissible pairs, this code makes no
     * assumptions about directionality.
     *
     *
     */

    supportedLanguages: [
      'ar', 'az', 'be', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es',
      'et', 'fi', 'fr', 'he', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka',
      'ko', 'lt', 'lv', 'mk', 'ms', 'mt', 'nl', 'no', 'pl', 'pt', 'ro', 'ru',
      'sk', 'sl', 'sq', 'sr', 'sv', 'th', 'tr', 'uk', 'vi', 'zh'
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
            if(textStatus === "timeout")
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
