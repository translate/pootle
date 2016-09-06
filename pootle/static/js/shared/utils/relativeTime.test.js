/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import expect from 'expect';
import { describe, it } from 'mocha';

import relativeTimeModule from './relativeTime';
import { relativeTime } from './relativeTime';

const relativeTimeMessage = relativeTimeModule.__GetDependency__(
  'relativeTimeMessage'
);


describe('relativeTime', () => {
  it('returns an empty string for undefined time deltas', () => {
    expect(relativeTime('')).toEqual('');
    expect(relativeTime(null)).toEqual('');
    expect(relativeTime(undefined)).toEqual('');
    expect(relativeTime('Invalid')).toEqual('');
    expect(relativeTime('2016-14-12')).toEqual('');
    expect(relativeTime('2016-12-12 25:02:11')).toEqual('');
  });
});


describe('relativeTimeMessage', () => {
  const tests = [
    {
      unit: 'immediately due times',
      delta: {
        seconds: 0,
        minutes: 0,
        hours: 0,
        days: 0,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: 'A few seconds ago',
    },
    {
      unit: 'a minute of difference',
      delta: {
        seconds: 22,
        minutes: 1,
        hours: 0,
        days: 0,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: 'A minute ago',
    },
    {
      unit: 'minutes of difference',
      delta: {
        seconds: 2,
        minutes: 29,
        hours: 0,
        days: 0,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: '29 minutes ago',
    },
    {
      unit: 'an hour of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 1,
        days: 0,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: 'An hour ago',
    },
    {
      unit: 'hours of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 0,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: '23 hours ago',
    },
    {
      unit: 'a day of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 1,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: 'Yesterday',
    },
    {
      unit: 'days of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 6,
        weeks: 0,
        months: 0,
        years: 0,
      },
      expected: '6 days ago',
    },
    {
      unit: 'a week of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 1,
        months: 0,
        years: 0,
      },
      expected: 'A week ago',
    },
    {
      unit: 'weeks of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 3,
        months: 0,
        years: 0,
      },
      expected: '3 weeks ago',
    },
    {
      unit: 'a month of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 3,
        months: 1,
        years: 0,
      },
      expected: 'A month ago',
    },
    {
      unit: 'months of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 3,
        months: 4,
        years: 0,
      },
      expected: '4 months ago',
    },
    {
      unit: 'a year of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 3,
        months: 4,
        years: 1,
      },
      expected: 'A year ago',
    },
    {
      unit: 'years of difference',
      delta: {
        seconds: 9,
        minutes: 2,
        hours: 23,
        days: 8,
        weeks: 3,
        months: 4,
        years: 6,
      },
      expected: '6 years ago',
    },
  ];

  tests.forEach((test) => {
    it(`covers ${test.unit}`, () => {
      expect(relativeTimeMessage(test.delta)).toEqual(test.expected);
    });
  });
});
