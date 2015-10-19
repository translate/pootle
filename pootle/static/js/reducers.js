/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import { combineReducers } from 'redux';

import auth from './auth/reducers';


let asyncReducers = {};


export function registerReducers(newReducers) {
  asyncReducers = assign({}, asyncReducers, newReducers);
}


function createReducer() {
  return combineReducers(assign(
    {},
    { auth },
    asyncReducers
  ));
}


export default createReducer;
