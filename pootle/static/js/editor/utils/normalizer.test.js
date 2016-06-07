/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import expect from 'expect';
import { describe, it } from 'mocha';

import { hasCRLF, normalize, denormalize } from './normalizer';


describe('hasCRLF', () => {
  const tests = [
    {
      description: 'null',
      input: null,
      expected: false,
    },
    {
      description: 'undefined',
      input: undefined,
      expected: false,
    },
    {
      description: 'true',
      input: true,
      expected: false,
    },
    {
      description: '"" (empty string)',
      input: '',
      expected: false,
    },
    {
      description: 'string with \\r\\n',
      input: 'foo\r\nbar',
      expected: true,
    },
    {
      description: 'string with \\n',
      input: 'foo\nbar',
      expected: false,
    },
  ];

  tests.forEach((test) => {
    it(`can detect CRLF in ${test.description}`, () => {
      expect(hasCRLF(test.input)).toBe(test.expected);
    });
  });
});


describe('normalize', () => {
  const tests = [
    {
      description: 'invalid input',
      input: 'foo\nbar',
      expected: [],
    },
    {
      description: 'single LF',
      input: ['foo\nbar'],
      expected: ['foo\nbar'],
    },
    {
      description: ['single CRLF'],
      input: ['foo\r\nbar'],
      expected: ['foo\nbar'],
    },
    {
      description: ['multiple CRLFs anywhere'],
      input: ['\r\nfoo\r\nbar\r\n'],
      expected: ['\nfoo\nbar\n'],
    },
  ];

  tests.forEach((test) => {
    it(`normalizes ${test.description}`, () => {
      expect(normalize(test.input)).toEqual(test.expected);
    });
  });
});


describe('denormalize', () => {
  const tests = [
    {
      description: 'invalid input',
      input: 'foo\nbar',
      expected: [],
    },
    {
      description: 'LF',
      input: ['foo\nbar'],
      expected: ['foo\r\nbar'],
    },
    {
      description: ['CRLF (should not happen)'],
      input: ['foo\r\nbar'],
      expected: ['foo\r\r\nbar'],
    },
  ];

  tests.forEach((test) => {
    it(`denormalizes ${test.description}`, () => {
      expect(denormalize(test.input)).toEqual(test.expected);
    });
  });
});
