/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


const requests = {};


function fetch({ url, body, method = 'GET', dataType = 'json', queue = null,
                 crossDomain = false }) {
  const queueName = queue || url;

  if (requests[queueName]) {
    requests[queueName].abort();
  }

  requests[queueName] = (
    $.ajax({
      crossDomain,
      method,
      dataType,
      url: l(url),
      data: body,
    })
  );
  requests[queueName].done(() => {requests[queueName] = null;});
  return requests[queueName];
}


export default fetch;
