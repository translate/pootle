/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


let requests = {};


function fetch({ url, body, method='GET', dataType='json', queue=null,
                 crossDomain=false }) {
  queue = queue || url;

  if (requests[queue]) {
    requests[queue].abort();
  }

  requests[queue] = (
    $.ajax({
      crossDomain,
      method,
      url: l(url),
      data: body,
      dataType: dataType,
    })
  );

  return requests[queue];
}


export default fetch;
