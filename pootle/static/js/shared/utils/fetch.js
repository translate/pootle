/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


let requests = {};


function fetch({url, body, method='POST', dataType='json'}) {
  if (requests[url]) {
    requests[url].abort();
  }

  requests[url] = (
    $.ajax({
      method,
      url: l(url),
      data: body,
      dataType: dataType,
    })
  );

  return requests[url];
}


export default fetch;
