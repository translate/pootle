/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import expect from 'expect';
import { describe, it } from 'mocha';

import { CHARACTERS, SYMBOLS, raw2sym, sym2raw } from './font';


describe('raw2sym (regular mode)', () => {
  const tests = [
    {
      description: 'nothing without special characters',
      input: 'Føó bäŕ băz błah\\.',
      expected: 'Føó bäŕ băz błah\\.',
    },
    {
      description: 'nothing for escaped symbols',
      input: 'Foo\\tbar\\n',
      expected: 'Foo\\tbar\\n',
    },

    {
      description: 'special characters with symbols',
      input: ([
        CHARACTERS.NULL, CHARACTERS.BELL, CHARACTERS.BS, CHARACTERS.BS,
        CHARACTERS.TAB, CHARACTERS.VT, CHARACTERS.FF, CHARACTERS.ESC,
        CHARACTERS.NBSP,
      ].join('')),
      expected: ([
        SYMBOLS.NULL, SYMBOLS.BELL, SYMBOLS.BS, SYMBOLS.BS,
        SYMBOLS.TAB, SYMBOLS.VT, SYMBOLS.FF, SYMBOLS.ESC,
        SYMBOLS.NBSP,
      ].join('')),
    },

    {
      description: 'a single space at the beginning',
      input: ' Foo bar',
      expected: `${SYMBOLS.SPACE}Foo bar`,
    },
    {
      description: 'a single space at the end',
      input: 'Foo bar ',
      expected: `Foo bar${SYMBOLS.SPACE}`,
    },
    {
      description: 'double spaces in the middle',
      input: 'Foo  bar',
      expected: `Foo${SYMBOLS.SPACE}${SYMBOLS.SPACE}bar`,
    },
    {
      description: 'extra spaces everywhere',
      input: '  Foo   bar    ',
      expected: (
        `${SYMBOLS.SPACE}${SYMBOLS.SPACE}Foo` +
        `${SYMBOLS.SPACE}${SYMBOLS.SPACE}${SYMBOLS.SPACE}bar` +
        `${SYMBOLS.SPACE}${SYMBOLS.SPACE}${SYMBOLS.SPACE}${SYMBOLS.SPACE}`
      ),
    },
    {
      description: 'whitespace around [NBSP]',
      input: `foo ${CHARACTERS.NBSP} bar`,
      expected: `foo${SYMBOLS.SPACE}${SYMBOLS.NBSP}${SYMBOLS.SPACE}bar`,
    },
    {
      description: 'whitespace around [TAB]',
      input: `foo ${CHARACTERS.TAB} bar`,
      expected: `foo${SYMBOLS.SPACE}${SYMBOLS.TAB}${SYMBOLS.SPACE}bar`,
    },

    {
      description: 'whitespace before punctuation (!)',
      input: 'foo ! Bar',
      expected: `foo${SYMBOLS.SPACE}! Bar`,
    },
    {
      description: 'whitespace before punctuation (?)',
      input: 'foo ? Bar',
      expected: `foo${SYMBOLS.SPACE}? Bar`,
    },
    {
      description: 'whitespace before punctuation (:)',
      input: 'foo : Bar',
      expected: `foo${SYMBOLS.SPACE}: Bar`,
    },

    {
      description: 'new line at end of line',
      input: `one${CHARACTERS.LF}`,
      expected: `one${SYMBOLS.LF}${CHARACTERS.LF}`,
    },
    {
      description: 'new line in the middle of the line',
      input: `one${CHARACTERS.LF}two`,
      expected: `one${SYMBOLS.LF}${CHARACTERS.LF}two`,
    },
    {
      description: 'new line in the middle of the line',
      input: `one${CHARACTERS.LF}two`,
      expected: `one${SYMBOLS.LF}${CHARACTERS.LF}two`,
    },
    {
      description: 'new line and whitespace at end of line',
      input: `one ${CHARACTERS.LF}`,
      expected: `one${SYMBOLS.SPACE}${SYMBOLS.LF}${CHARACTERS.LF}`,
    },
    {
      description: 'new line and whitespace at beginning of line',
      input: `one${CHARACTERS.LF} `,
      expected: `one${SYMBOLS.LF}${CHARACTERS.LF}${SYMBOLS.SPACE}`,
    },
    {
      description: 'new line and whitespace before the end of line',
      input: `one ${CHARACTERS.LF}`,
      expected: `one${SYMBOLS.SPACE}${SYMBOLS.LF}${CHARACTERS.LF}`,
    },
  ];

  describe('conversion', () => {
    tests.forEach((test) => {
      it(`converts ${test.description}`, () => {
        expect(raw2sym(test.input)).toEqual(test.expected);
      });
    });
  });

  describe('round-tripping', () => {
    tests.forEach((test) => {
      it(`roundtrips ${test.description}`, () => {
        expect(sym2raw(raw2sym(test.input))).toEqual(test.input);
      });
    });
  });
});


describe('raw2sym (raw mode)', () => {
  const tests = [
    {
      description: 'nothing without special characters',
      input: 'Føóbäŕbăzbłah\\.',
      expected: 'Føóbäŕbăzbłah\\.',
    },
    {
      description: 'nothing for escaped symbols',
      input: 'Foo\\tbar\\n',
      expected: 'Foo\\tbar\\n',
    },

    {
      description: 'special characters with symbols',
      input: (
        Object.keys(CHARACTERS)
          .filter(key => key !== 'LF' && key !== 'CR')
          .map(key => CHARACTERS[key]).join('')
      ),
      expected: (
        Object.keys(SYMBOLS)
          .filter(key => key !== 'LF' && key !== 'CR')
          .map(key => SYMBOLS[key]).join('')
      ),
    },

    {
      description: 'spaces anywhere',
      input: ' Foo bar baz  blah   ',
      expected: (
        `${SYMBOLS.SPACE}Foo` +
        `${SYMBOLS.SPACE}bar` +
        `${SYMBOLS.SPACE}baz` +
        `${SYMBOLS.SPACE}${SYMBOLS.SPACE}blah` +
        `${SYMBOLS.SPACE}${SYMBOLS.SPACE}${SYMBOLS.SPACE}`
      ),
    },
  ];

  describe('conversion', () => {
    tests.forEach((test) => {
      it(`converts ${test.description}`, () => {
        expect(raw2sym(test.input, { isRawMode: true })).toEqual(test.expected);
      });
    });
  });

  describe('round-tripping', () => {
    tests.forEach((test) => {
      it(`roundtrips ${test.description}`, () => {
        expect(sym2raw(raw2sym(test.input, { isRawMode: true })))
          .toEqual(test.input);
      });
    });
  });
});
