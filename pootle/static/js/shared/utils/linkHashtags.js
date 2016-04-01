/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


const hashtagRE = /(^|\s+|>)(#[0-9a-z_\-]+)/gi;


function linkToHashtag(tag) {
  const currentLocation = window.location.toString().split('#', 2)[0];
  const hashtag = encodeURIComponent(tag);
  return `${currentLocation}#search=${hashtag}&sfields=notes`;
}


export default function linkHashtags(text) {
  if (!text) {
    return '';
  }

  return text.replace(hashtagRE, (match, before, hashtag) =>
    `${before}<a href="${linkToHashtag(hashtag)}">${hashtag}</a>`
  );
}
