'use strict';

import { Flummox } from 'flummox';

import AuthActions from './actions/AuthActions';
import AuthStore from './stores/AuthStore';


export default class Flux extends Flummox {

  constructor() {
    super();

    this.createActions('auth', AuthActions);
    this.createStore('auth', AuthStore, this);
  }

}
