(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof exports === 'object') {
    module.exports = factory();
  } else {
    root.Levenshtein = factory();
  }
}(this, function () {

  'use strict';

  /* Private functions */

  /*
   * Splits the given text in words.
   *
   * Whitespaces are normalized to a single character and are returned as
   * part of the result.
   *
   * Examples:
   *
   *  "   foo bar  baz   " -> ['', 'foo', 'bar', 'baz', '']
   *  "foo bar" -> ['foo', 'bar']
   *
   */
  var segmentWords = function (text) {
    return text.replace(/\s+/g, ' ').split(' ');
  };


  /*
   * Prepare input for further processing.
   *
   * As a start, ensure the input is a string.
   * Depending on the desired comparison type, a segmentation function
   * will be applied or not.
   */
  var prepareInput = function (input, compare) {
    if (input === null || input === undefined) {
      input = '';
    } else if (typeof input !== 'string' || !input instanceof String) {
      input = (input).toString();
    }

    return (compare === 'words') ? segmentWords(input) : input;
  };


  /*
   * Normalizes `similarity` to the [0..1] range
   *
   * @param `similarity`: calculated similarity
   * @param `maxLength`: maximum length of the arguments used to calculate
   *   the similarity value.
   */
  var normalize = function (similarity, maxLength) {
    return 1 - similarity / maxLength;
  };


  /*
   * Edit distance calculator.
   *
   * From https://en.wikipedia.org/wiki/Levenshtein_distance
   * Based on the iterative algorithm of Sten Hjelmqvist
   *
   */
  var editDistance = function (a, b) {
    // max(|a|, |b|) if min(|a|, |b|) == 0
    if (a.length === 0) {
      return b.length;
    }
    if (b.length === 0) {
      return a.length;
    }

    var previous = [],
        current = [],
        i, j, distance;

    // Initialize previous row of distances
    for (i=0; i<b.length+1; ++i) {
      previous[i] = i;
    }

    // Calculate current row distances from the previous row
    for (i=0; i<a.length; i++) {

      // First element in the row is always i+1: the distance to match the
      // empty string/no word
      current[0] = i + 1;

      for (j=0; j<b.length; j++) {
        distance = (a[i] === b[j]) ? 0 : 1;

        current[j+1] = Math.min(
          current[j] + 1, // deleted
          previous[j+1] + 1, // added
          previous[j] + distance // match/mismatch
        );
      }

      // Copy current row to previous row for the next iteration
      for (j=0; j<current.length; j++) {
        previous[j] = current[j];
      }
    }

    return current[b.length];
  };


  /* Public API */

  var Levenshtein = function (opts) {
    opts = opts || {};
    this.opts = {
      // Measure distance in: 'words', 'strings'
      compare: opts.compare || 'strings'
    };
  };

  Levenshtein.fn = Levenshtein.prototype;

  Levenshtein.fn.prepareInput = prepareInput;

  /*
   * Calculate Levenshtein distance between `a` and `b`.
   *
   * @param `a`: first sequence of characters
   * @param `b`: second sequence of characters
   */
  Levenshtein.fn.distance = function (a, b) {
    var a = prepareInput(a, this.opts.compare),
        b = prepareInput(b, this.opts.compare);

    return editDistance(a, b);
  };


  /*
   * Calculate similarity between sequences `a` and `b`.
   *
   * Normalizes the edit distance to the [0..1] range.
   *
   * @param `a`: first sequence of characters
   * @param `b`: second sequence of characters
   */
  Levenshtein.fn.similarity = function (a, b) {
    var a = prepareInput(a, this.opts.compare),
        b = prepareInput(b, this.opts.compare);

    return normalize(editDistance(a, b), Math.max(a.length, b.length));
  };


  return Levenshtein;

}));
