/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import expect from 'expect';
import { describe, it } from 'mocha';

import { SYMBOLS } from './font';
import {
  highlightPunctuation, highlightEscapes, highlightHtml, highlightSymbols, nl2br,
} from './highlight';


describe('highlightPunctuation', () => {
  const HL_CLASS = 'highlight-punctuation';
  const HL_START = `<span class="${HL_CLASS} ">`;
  const HL_END = '</span>';
  const tests = [
    {
      description: 'a single punctuation character',
      input: '…',
      expected: `${HL_START}…${HL_END}`,
    },
    {
      description: 'multiple punctuation characters',
      input: '… foo €',
      expected: `${HL_START}…${HL_END} foo ${HL_START}€${HL_END}`,
    },
    {
      description: '',
      input: '',
      expected: '',
    },
  ];

  tests.forEach((test) => {
    it(`highlights ${test.description}`, () => {
      expect(highlightPunctuation(test.input)).toEqual(test.expected);
    });
  });
});


describe('highlightEscapes', () => {
  const HL_CLASS = 'highlight-escape';
  const HL_START = `<span class="${HL_CLASS} ">`;
  const HL_END = '</span>';
  const tests = [
    {
      description: 'nothing without escaped sequences',
      input: 'Føó bäŕ băz błah\\.',
      expected: 'Føó bäŕ băz błah\\.',
    },
    {
      description: 'mixed escaped sequences',
      input: 'Føó\\n bäŕ\\r\\n băz\\t błah\\.',
      expected: (
        `Føó${HL_START}\\n${HL_END} ` +
        `bäŕ${HL_START}\\r${HL_END}${HL_START}\\n${HL_END} ` +
        `băz${HL_START}\\t${HL_END} błah\\.`
      ),
    },
  ];

  tests.forEach((test) => {
    it(`highlights ${test.description}`, () => {
      expect(highlightEscapes(test.input)).toEqual(test.expected);
    });
  });
});


describe('nl2br', () => {
  it('does nothing without new line characters', () => {
    const input = 'Føó bäŕ băz błah.';
    expect(nl2br(input)).toEqual(input);
  });

  it('appends HTML line breaks to new line characters', () => {
    const BR = '<br/>';
    const input = 'Føó\n bäŕ\r\n băz błah.';
    const expected = `Føó\n${BR} bäŕ\r\n${BR} băz błah.`;
    expect(nl2br(input)).toEqual(expected);
  });
});


describe('highlightHtml', () => {
  const HL_CLASS = 'highlight-html';
  const HL_START = `<span class="${HL_CLASS} ">`;
  const HL_END = '</span>';
  const tests = [
    {
      description: 'nothing for empty strings',
      input: '',
      expected: '',
    },
    {
      description: 'nothing for regular text',
      input: 'Føó bäŕ băz błah.',
      expected: 'Føó bäŕ băz błah.',
    },
    {
      description: 'nothing but escapes ampersands for entities',
      input: 'foo&nbsp;bar',
      expected: 'foo&amp;nbsp;bar',
    },
    {
      description: 'nothing but escapes ampersands for entities (doubled)',
      input: 'foo&amp;nbsp;bar',
      expected: 'foo&amp;amp;nbsp;bar',
    },
    {
      description: 'HTML tags',
      input: 'foo<b>bar</b>',
      expected: `foo${HL_START}&lt;b&gt;${HL_END}bar${HL_START}&lt;/b&gt;${HL_END}`,
    },
    {
      description: 'HTML tags with entities',
      input: 'foo<b>&nbsp;</b>',
      expected: (
        `foo${HL_START}&lt;b&gt;${HL_END}&amp;nbsp;${HL_START}&lt;/b&gt;${HL_END}`
      ),
    },
    {
      description: 'nested HTML tags',
      input: 'foo<b><i>&nbsp;</i></b>',
      expected: (
        `foo${HL_START}&lt;b&gt;${HL_END}${HL_START}&lt;i&gt;${HL_END}` +
        `&amp;nbsp;${HL_START}&lt;/i&gt;${HL_END}${HL_START}&lt;/b&gt;${HL_END}`
      ),
    },
    {
      description: 'HTML tags which contain $ between delimiters',
      input: "<a href='$url$'>",
      expected: `${HL_START}&lt;a href='$url$'&gt;${HL_END}`,
    },
    {
      description: 'HTML tags which contain %s between delimiters',
      input: '<a href="%s">',
      expected: `${HL_START}&lt;a href="%s"&gt;${HL_END}`,
    },
  ];

  tests.forEach((test) => {
    it(`highlights ${test.description}`, () => {
      expect(highlightHtml(test.input)).toEqual(test.expected);
    });
  });
});


describe('highlightSymbols', () => {
  const HL_START = '<span class="" data-codepoint="%s">';
  const HL_END = '</span>';
  const tests = [
    {
      description: 'nothing for empty strings',
      input: '',
      expected: '',
    },
    {
      description: 'nothing for regular text',
      input: 'Føó bäŕ băz błah.',
      expected: 'Føó bäŕ băz błah.',
    },
    {
      description: 'newline symbols',
      input: `foo${SYMBOLS.LF}bar`,
      expected: `foo${HL_START.replace('%s', '\\u000A')}${SYMBOLS.LF}${HL_END}bar`,
    },
    {
      description: 'multiple newline symbols',
      input: `foo${SYMBOLS.LF}${SYMBOLS.LF}bar`,
      expected: (
        `foo${HL_START.replace('%s', '\\u000A')}${SYMBOLS.LF}${HL_END}` +
        `${HL_START.replace('%s', '\\u000A')}${SYMBOLS.LF}${HL_END}bar`
      ),
    },
    {
      description: 'non-breaking spaces',
      input: `foo${SYMBOLS.NBSP}bar`,
      expected: `foo${HL_START.replace('%s', '\\u00A0')}${SYMBOLS.NBSP}${HL_END}bar`,
    },
  ];

  tests.forEach((test) => {
    it(`highlights ${test.description}`, () => {
      expect(highlightSymbols(test.input)).toEqual(test.expected);
    });
  });
});
