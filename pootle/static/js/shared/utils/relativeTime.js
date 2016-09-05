/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { nt, t } from './i18n';
import { timeDelta } from './time';


function relativeTimeMessage({
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
