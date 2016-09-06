/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import L20nEditor from './L20nEditor';
import L20nSource from './L20nSource';


const L20nAdaptor = {
  editorComponent: L20nEditor,
  unitSourceComponent: L20nSource,
};


export default L20nAdaptor;
