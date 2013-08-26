(function ($) {
  window.PTL.editor.mt = window.PTL.editor.mt || {};

  PTL.editor.mt.google_translate = {

    buttonClassName: "google-translate",
    hint: "Google Translate",
    validatePair: false,

    /* using Google Translate API v2 */
    url: "https://www.googleapis.com/language/translate/v2",

    /* For a list of currently supported languages:
     * https://developers.google.com/translate/v2/using_rest#language-params
     * FIXME note that we seem not to use this list, but an API does exist to
     * query if Google supports a given language */
    pairs: [{"source":"af","target":"af"},
            {"source":"sq","target":"sq"},
            {"source":"ar","target":"ar"},
            {"source":"be","target":"be"},
            {"source":"bg","target":"bg"},
            {"source":"ca","target":"ca"},
            {"source":"zh","target":"zh"},
            {"source":"zh-CN","target":"zh-CN"},
            {"source":"zh-TW","target":"zh-TW"},
            {"source":"hr","target":"hr"},
            {"source":"cs","target":"cs"},
            {"source":"da","target":"da"},
            {"source":"nl","target":"nl"},
            {"source":"en","target":"en"},
            {"source":"et","target":"et"},
            {"source":"tl","target":"tl"},
            {"source":"fi","target":"fi"},
            {"source":"fr","target":"fr"},
            {"source":"gl","target":"gl"},
            {"source":"de","target":"de"},
            {"source":"el","target":"el"},
            {"source":"ht","target":"ht"},
            {"source":"iw","target":"iw"},
            {"source":"hi","target":"hi"},
            {"source":"hu","target":"hu"},
            {"source":"is","target":"is"},
            {"source":"id","target":"id"},
            {"source":"ga","target":"ga"},
            {"source":"it","target":"it"},
            {"source":"ja","target":"ja"},
            {"source":"ko","target":"ko"},
            {"source":"lv","target":"lv"},
            {"source":"lt","target":"lt"},
            {"source":"mk","target":"mk"},
            {"source":"ms","target":"ms"},
            {"source":"mt","target":"mt"},
            {"source":"no","target":"no"},
            {"source":"fa","target":"fa"},
            {"source":"pl","target":"pl"},
            {"source":"pt","target":"pt"},
            {"source":"pt-PT","target":"pt-PT"},
            {"source":"ro","target":"ro"},
            {"source":"ru","target":"ru"},
            {"source":"sr","target":"sr"},
            {"source":"sk","target":"sk"},
            {"source":"sl","target":"sl"},
            {"source":"es","target":"es"},
            {"source":"sw","target":"sw"},
            {"source":"sv","target":"sv"},
            {"source":"tl","target":"tl"},
            {"source":"th","target":"th"},
            {"source":"tr","target":"tr"},
            {"source":"uk","target":"uk"},
            {"source":"vi","target":"vi"},
            {"source":"cy","target":"cy"},
            {"source":"yi","target":"yi"}],

    init: function (apiKey) {
      /* Prepare URL for requests. */
      this.url += "?callback=?";
      /* Set API key */
      this.apiKey = apiKey;
      /* Bind event handler */
      $(document).on("click", ".google-translate", this.translate);
    },

    ready: function () {
      PTL.editor.addMTButtons(PTL.editor.mt.google_translate);
    },

    translate: function () {
      PTL.editor.translate(this, function(sourceText, langFrom, langTo, resultCallback) {
        var transData = {key: PTL.editor.mt.google_translate.apiKey,
                         q: sourceText,
                         source: langFrom,
                         target: langTo}
        $.getJSON(PTL.editor.mt.google_translate.url, transData, function (r) {
          if (r.data && r.data.translations) {
            resultCallback(r.data.translations[0].translatedText);
          } else {
            if (r.error && r.error.message) {
              resultCallback(false, "Google Translate Error: " + r.error.message);
            } else {
              resultCallback(false, "Malformed response from Google Translate API");
            }
          }
        });
      });
    }
  };
})(jQuery);
