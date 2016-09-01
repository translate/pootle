/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { nt, t } from './i18n';


/**
 * A version of `Math.trunc` which returns absolute values.
 *
 * @param {Number} number - the number to truncate.
 * @return {Number} - positive integer
 */
function absTrunc(number) {
  const truncated = Math.trunc(number);
  return truncated < 0 ? truncated * -1 : truncated;
}


/**
 * Calculates the time difference from `isoDateTime` to the current date as
 * provide by the client.
 *
 * Note the difference calculation doesn't intend to be smart about leap years
 * and number of days per month, but rather a simple and naive implementation.
 *
 * @param {String} isoDateTime - a date and time combination in ISO 8601 format
 * as understood by browsers' `Date.parse()`.
 * @return {Object} - An object with the delta difference specified in seconds,
 * minutes, hours, days, weeks and months. The `isFuture` boolean
 * property indicates whether the difference refers to a future time.
 * When the value passed is invalid or cannot be parsed, every property in the
 * object will be `null`.
 */
export function timeDelta(isoDateTime) {
  const providedTime = isoDateTime && Date.parse(isoDateTime);
  if (!providedTime || isNaN(providedTime)) {
    return {
      isFuture: null,
      seconds: null,
      minutes: null,
      hours: null,
      days: null,
      weeks: null,
      months: null,
      years: null,
    };
  }

  const now = (new Date()).valueOf();
  const delta = providedTime - now;

  const isFuture = delta > 0;

  const seconds = absTrunc(delta / 1000);
  const minutes = absTrunc(seconds / 60);
  const hours = absTrunc(minutes / 60);
  const days = absTrunc(hours / 24);
  const weeks = absTrunc(days / 7);
  const months = absTrunc(days / 30);  // naive: assuming 30 days per month
  const years = absTrunc(days / 365);  // naive: assuming 365 days per year

  return {
    isFuture,
    seconds,
    minutes,
    hours,
    days,
    weeks,
    months,
    years,
  };
}


export function relativeTimeMessage({
  minutes, hours, days, weeks, months, years,
}) {
  if (years > 0) {
    if (years === 1) {
      return t('A year ago');
    }
    return nt('%(count)s year ago', '%(count)s years ago',
              years, { count: years });
  }

  if (months > 0) {
    if (months === 1) {
      return t('A month ago');
    }
    return nt('%(count)s month ago', '%(count)s months ago',
              months, { count: months });
  }

  if (weeks > 0) {
    if (weeks === 1) {
      return t('A week ago');
    }
    return nt('%(count)s week ago', '%(count)s weeks ago',
              weeks, { count: weeks });
  }

  if (days > 0) {
    if (days === 1) {
      return t('Yesterday');
    }
    return nt('%(count)s day ago', '%(count)s days ago',
              days, { count: days });
  }

  if (hours > 0) {
    if (hours === 1) {
      return t('An hour ago');
    }
    return nt('%(count)s hour ago', '%(count)s hours ago',
              hours, { count: hours });
  }

  if (minutes > 0) {
    if (minutes === 1) {
      return t('A minute ago');
    }
    return nt('%(count)s minute ago', '%(count)s minutes ago',
              minutes, { count: minutes });
  }

  return t('A few seconds ago');
}


/**
 * Generate a human-readable relative time message.
 *
 * @param {String} isoDateTime - a date and time combination in ISO 8601 format
 * as understood by browsers' `Date.parse()`.
 * @return {String} - Message referring to the relative time. Returns an empty
 * string if the provided date time is invalid or cannot be parsed.
 */
export function relativeTime(isoDateTime) {
  const {
    isFuture, minutes, hours, days, weeks, months, years,
  } = timeDelta(isoDateTime);

  if (isFuture === null) {
    return '';
  }

  return relativeTimeMessage({ minutes, hours, days, weeks, months, years });
}
