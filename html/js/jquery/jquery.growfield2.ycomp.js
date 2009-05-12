/*
 * The MIT License
 *
 * Copyright (c) 2009 Johann Kuindji
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 * @author Johann Kuindji, Dmitriy Likhten
 * http://code.google.com/p/jquery-growfield/
 */
(function($) {
if ($.support === undefined) {
    $.support = { boxModel: $.boxModel };
}
var windowLoaded = false;
$(window).one('load', function(){ windowLoaded=true; });

// we need to adapt jquery animations for textareas.
// by default, it changes display to 'block' if we're trying to
// change width or height. We have to prevent this.
// THIS WILL NOT ALTER JQUERY ORIGINAL BEHAVIORS, IT WILL HOWEVER ADD
// SOME SO THAT GROWFIELD ANIMATIONS WORK CORRECTLY.
$.fx.prototype.originalUpdate = $.fx.prototype.update;
$.fx.prototype.update = false;
$.fx.prototype.update = function () {
    if (!this.options.inline) {
        return this.originalUpdate.call(this);
    }
    if ( this.options.step ) {
        this.options.step.call( this.elem, this.now, this );
    }
    (jQuery.fx.step[this.prop] || jQuery.fx.step._default)( this );
};

$.growfield = function(dom,options){
    // Extend ptt(prototype) with our own private variables/
    // shared's functions are re-referenced and not cloned so
    // memory is kept at a minimum.
    var that = $.extend({
        dom: dom,
        o: $(dom),
        enabled: false,
        dummy: false,
        busy: false,
        initial: false,
        sizseRelated: false,
        prevH: false,
        firstH: false,
        restoreH: false,
        opt: $.extend({},$.fn.growfield.defaults,options)
    },$.growfield.ptt);

    return that;
};

//-----------------------------------------------------
// This is the base class for all $.growfield objects
// (their prototype)
//-----------------------------------------------------
$.growfield.ptt = (function(){
    //-----------------------------------------------------
    //EVENT HANDLERS for dealing with the growfield object
    //-----------------------------------------------------
    var manualKeyUp = function(e) {
        var obj = e.data;
        if (e.ctrlKey && (e.keyCode == 38 || e.keyCode == 40)){
            obj.update(
                obj.o.outerHeight() + (obj.opt.step*( e.keyCode==38? -1: 1)),
                obj.opt.animate
            );
        }
    };

    var keyUp = function(e) {
        var obj = e.data;
        if (!obj.busy){
            if ($.inArray(e.keyCode, [37,38,39,40]) === -1) {
                obj.update(obj.getDummyHeight(), obj.opt.animate);
            }
        }
        return true;
    };

    var focus = function(e) {
        var obj = e.data;
        if (!obj.busy) {
            if (obj.opt.restore) {
                obj.update(obj.dummy ? obj.getDummyHeight() : obj.restoreH, obj.opt.animate, 'growback');
            }
        }
    };

    var blur = function(e) {
        var obj = e.data;
        if (!obj.busy) {
            if (obj.opt.restore) {
                obj.update(0, obj.opt.animate, 'restore');
            }
        }
    };

    var prepareSizeRelated = function(e) {
        var obj = e.data;
        var o = obj.o;
        var opt = obj.opt;

        if (!opt.min) {
            opt.min = parseInt(o.css('min-height'), 10) || obj.firstH || parseInt(o.height(), 10) || 20;
            if (opt.min <= 0) {
                opt.min = 20; // opera fix
            }
            if (!obj.firstH) {
                obj.firstH = opt.min;
            }
        }
        if (!opt.max) {
            opt.max = parseInt(o.css('max-height'), 10) || false;
            if (opt.max <= 0) {
                opt.max = false; // opera fix
            }
        }
        if (!opt.step) {
            opt.step = parseInt(o.css('line-height'), 10) || parseInt(o.css('font-size'), 10) || 20;
        }

        var sr = {
            pt: parseInt(o.css('paddingTop'), 10)||0,
            pb: parseInt(o.css('paddingBottom'), 10)||0,
            bt: parseInt(o.css('borderTopWidth'), 10)||0,
            bb: parseInt(o.css('borderBottomWidth'), 10)||0,
            lh: parseInt(o.css('lineHeight'), 10) || false,
            fs: parseInt(o.css('fontSize'), 10) || false
        };

        obj.sizeRelated = sr;
    };

    /**
     * Create a dummy if one does not yet exist.
     */
    var createDummy = function(e) {
        var obj = e.data;
        if(!obj.dummy){
            var val = obj.o.val();
            // we need dummy to calculate scrollHeight
            // (there are some tricks that can't be applied to the textarea itself, otherwise user will see it)
            // Also, dummy must be a textarea too, and must be placed at the same position in DOM
            // in order to keep all the inherited styles
            var dummy = obj.o.clone();
            dummy.addClass('growfieldDummy');
            dummy.attr('tabindex', -9999);
            dummy.css({
                position: 'absolute',
                left: -9999,
                top: 0,
                height: '20px',
                resize: 'none'});
            // The dummy must be inserted after otherwise google chrome will
            // focus on the dummy instead of on the actual text area, focus will always
            // be lost.
            dummy.insertAfter(obj.o);
            dummy.show();

            // if there is no initial value, we have to add some text, otherwise textarea will jitter
            // at the first keydown
            if (!val) {
                dummy.val('dummy text');
            }
            obj.dummy = dummy;
            // lets set the initial height
            // Pootle customisation: we disable this so that the initial height
            // will be what we asked for.
            // obj.update((!$.trim(val) || obj.opt.restore) ? 0 : obj.getDummyHeight(), false);
        }
    };

    /**
     * Remove the dummy if one exists
     */
    var removeDummy = function(e) {
        obj = e.data;
        if(obj.dummy){
            obj.dummy.remove();
            delete obj.dummy;
        }
    };

    //-----------------------------------------------------
    // END EVENT HANDLERS
    //-----------------------------------------------------

    // This will bind to $(document).ready if the height is loaded
    // or a window.load event already occurred.
    // OR it will just bind to the window.load event.
    var executeWhenReady = function(data,fn){
        if (data.o.height() !== 0 || windowLoaded) {
            $(document).ready(function(){
                fn({data:data});
            });
        }
        else {
            $(window).one('load', data, fn);
        }
    };

    //-----------------------------------------------------
    // Public methods.
    //-----------------------------------------------------
    var that = {
        // Toggle the functionality.
        // enable or true will enable growfield
        // disable or false will disable growfield
        toggle: function(mode) {
            if ((mode=='disable' || mode===false)&&this.enabled) {
                this.unbind();
            }
            else if ((mode=='enable' || mode===true)&&!this.enabled) {
                this.bind();
            }
            return this;
        },

        // Bind all growfield events to the object.
        bind: function(){
            executeWhenReady(this,prepareSizeRelated);
            var opt = this.opt;
            var o = this.o;

            // auto mode, textarea grows as you type
            if (opt.auto) {

                o.bind('keyup.growfield', this, keyUp);
                this.initial = {
                    overflow: this.o.css('overflow'),
                    cssResize: this.o.css('resize')
                };
                // We want to ensure that safari and google chrome do not allow
                // the user to drag-to-resize the field. This should only be enabled
                // if auto mode is disabled.
                if ($.browser.safari) {
                    o.css('resize', 'none');
                }
                o.css('overflow','hidden');

                o.bind('focus.growfield', this, createDummy);
                // all styles must be loaded before prepare elements
                // we need to ensure the dummy exists at least for a short
                // time so that we can calculate the initial state...
                executeWhenReady(this, createDummy);
                executeWhenReady(this, removeDummy);
            }
            // manual mode, textarea grows as you type ctrl + up|down
            else {
                o.bind('keydown.growfield', this, manualKeyUp);
                o.css('overflow-y', 'auto');
                executeWhenReady(this,function(e){
                    e.data.update(e.data.o.height());
                });
            }
            o.bind('focus.growfield', this, focus);
            o.bind('blur.growfield', this, blur);
            o.bind('blur.growfield', this, removeDummy);

            // Custom events provided in options
            if (opt.onHeightChange) {
                o.bind('onHeightChange.growfield', opt.onHeightChange);
            }
            if (opt.onRestore) {
                o.bind('onRestore.growfield', opt.onRestore);
            }
            if (opt.onGrowBack) {
                o.bind('onGrowBack.growfield', opt.onGrowBack);
            }

            this.enabled = true;

            return this;
        },

        // Unbind all growfield events from the object (including custom events)
        unbind: function() {
            removeDummy({data:this});
            this.o.unbind('.growfield');
            this.o.css('overflow', this.initial.overflow);
            if ($.browser.safari) {
                this.o.css('resize', this.initial.cssResize);
            }
            this.enabled = false;

            return this;
        },

        // Trigger custom events according to updateMode
        triggerEvents: function(updateMode) {
            var o = this.o;
            o.trigger('onHeightChange.growfield');
            if (updateMode == 'restore') {
                o.trigger('onRestore.growfield');
            }
            if (updateMode == 'growback') {
                o.trigger('onGrowBack.growfield');
            }
        },

        update: function(h, animate, updateMode) {
            var sr = this.sizeRelated;
            var val = this.o.val();
            var opt = this.opt;
            var dom = this.dom;
            var o = this.o;
            var th = this;
            var prev = this.prevH;
            var noHidden = !opt.auto;
            var noFocus = opt.auto;

            h = this.convertHeight(Math.round(h), 'inner');
            // get the right height according to min and max value
            h = opt.min > h ? opt.min :
                  opt.max && h > opt.max ? opt.max :
                  opt.auto && !val ? opt.min : h;

            if (opt.max && opt.auto) {
                if (prev != opt.max && h == opt.max) { // now we reached maximum height
                    o.css('overflow-y', 'scroll');
                    if (!opt.animate) {
                        o.focus(); // browsers do loose cursor after changing overflow :(
                    }
                    noHidden = true;
                    noFocus = false;
                }
                if (prev == opt.max && h < opt.max) {
                    o.css('overflow-y', 'hidden');
                    if (!opt.animate) {
                        o.focus();
                    }
                    noFocus = false;
                }
            }

            if (h == prev) {
                return true;
            }
            // in case of restore in manual mode we have to store
            // previous height (we can't get it from dummy)
            if (!opt.auto && updateMode == 'restore') {
                this.restoreH = this.convertHeight(this.prevH, 'outer');
            }
            this.prevH = h;

            if (animate) {
                th.busy = true;
                o.animate({height: h}, {
                    duration: opt.animate,
                    easing: ($.easing ? opt.easing : null),
                    overflow: null,
                    inline: true, // this option isn't jquery's. I added it by myself, see above
                    complete: function(){
                        // safari/chrome fix
                        // somehow textarea turns to overflow:scroll after animation
                        // i counldn't find it in jquery fx :(, so it looks like some bug
                        if (!noHidden) {
                            o.css('overflow', 'hidden');
                        }
                        // but if we still need to change overflow (due to opt.max option)
                        // we have to invoke focus() event, otherwise browser will loose cursor
                        if (!noFocus && updateMode != 'restore') {
                            o.focus();
                        }
                        if (updateMode == 'growback') {
                            dom.scrollTop = dom.scrollHeight;
                        }
                        th.busy = false;
                        th.triggerEvents(updateMode);
                    },
                    queue: false
                });
            } else {
                dom.style.height = h+'px';
                this.triggerEvents(updateMode);
            }
        },

        getDummyHeight: function() {
            var val = this.o.val();
            var h = 0;
            var sr = this.sizeRelated;
            var add = "\n111\n111";

            // Safari has some defect with double new line symbol at the end
            // It inserts additional new line even if you have only one
            // But that't not the point :)
            // Another question is how much pixels to keep at the bottom of textarea.
            // We'll kill many rabbits at the same time by adding two new lines at the end
            // (but if we have font-size and line-height defined, we'll add two line-heights)
            if ($.browser.safari) {
                val = val.substring(0, val.length-1); // safari has an additional new line ;(
            }

            if (!sr.lh || !sr.fs) {
                val += add;
            }

            this.dummy.val(val);

            // IE requires to change height value in order to recalculate scrollHeight.
            // otherwise it stops recalculating scrollHeight after some magical number of pixels
            if ($.browser.msie) {
                this.dummy[0].style.height = this.dummy[0].scrollHeight+'px';
            }

            h = this.dummy[0].scrollHeight;

            // if line-height is greater than font-size we'll add line-height + font-size
            // otherwise font-size * 2
            // there is no special logic in this behavior, it's been developed from visual testing
            if (sr.lh && sr.fs) {
                h += sr.lh > sr.fs ? sr.lh+sr.fs :  sr.fs * 2;
            }

            // now we have to minimize dummy back, or we'll get wrong scrollHeight next time
            //if ($.browser.msie) {
            //    this.dummy[0].style.height = '20px'; // random number
            //}

            return h;
        },

        convertHeight: function(h, to) {
            var sr = this.sizeRelated, mod = (to=='inner' ? -1 : 1), bm = $.support.boxModel;
            // what we get here in 'h' is scrollHeight value.
            // so we need to subtract paddings not because of boxModel,
            // but only if browser includes them to the scroll height (which is not defined by box model)
            return h
                + (bm ? sr.bt : 0) * mod
                + (bm ? sr.bb : 0) * mod
                + (bm ? sr.pt : 0) * mod
                + (bm ? sr.pb : 0) * mod;
        }

    };

    return that;
})();

/**
 * The growfield function. This will make a textarea a growing text area.
 *
 * @param {Object} options - See API for details on possible paramaters.
 */
$.fn.growfield = function(options) {
    // enable/disable is same thing as true/false
    switch(options){
        case 'enable':
            options = true;
            break;
        case 'disable':
            options = false;
            break;
    }

    // we need to know what was passed as the options
    var tp = typeof options;

    // These variables are used to reduce string comparisons
    // happening over and over.
    var conditions = {
        bool: tp == 'boolean',
        string: tp == 'string',
        object: tp == 'object',
        restart: options == 'restart',
        destroy: options == 'destroy'
    };

    // If the type of the options is a string
    // and is not one of the pre-defined ones, then
    // options is a preset.
    if(conditions.string && !conditions.destroy && !conditions.restart){
        options = $.fn.growfield.presets[options];
        // change to new conditions
        conditions.string = false;
        conditions.object = true;
    }

    // completely remove growfield from the dom elements
    if (conditions.destroy) {
        this.each(function() {
            var self = $(this);
            var gf = self.data('growfield');
            if (gf !== undefined) {
                gf.unbind();
                self.removeData('growfield');
            }
        });
    }
    // Apply growfield
    else {
        var textareaRegex = /textarea/i;
        this.each(function() {
            // only deal with textareas which are not dummy fields.
            if (textareaRegex.test(this.tagName) && !$(this).hasClass('growfieldDummy')) {
                var o = $(this);
                var gf = o.data('growfield');
                // Create the new options
                if (gf === undefined) {
                    gf = $.growfield(this,options);
                    o.data('growfield', gf);

                    // Bind only if the options is not a boolean
                    // or is not "false". Because options = a false boolean
                    // indicates intial bind should not happen.
                    if(!conditions.bool || options){
                        gf.bind();
                    }
                }
                // Otherwise apply actions based on the options provided
                else {
                    // If new options provided, set them
                    if(conditions.object && options) {
                        $.extend(gf.opt,options);
                    }
                    // If toggling enable/disable then do it
                    else if (conditions.bool) {
                        gf.toggle(options);
                    }
                    // If restarting, restart
                    else if (conditions.restart) {
                        gf.unbind();
                        gf.bind();
                    }
                }
            }
        });
    }

    return this;
};

/**
 * These are the default options to use, unless specified when invoking growfield.
 */
$.fn.growfield.defaults ={
    // Should the growfield automatically expand?
    auto: true,
    // The animation speed for expanding (false = off)
    animate: 100,
    // The easiny function to use, if the jquery.easing plugin is not present during
    // execution, this will always be treated as null regardless of the set value
    easing: null,
    // The minimum height (defaults to CSS min-height, or the current height of the element)
    min: false,
    // The maximum height (defaults to CSS max-height, or unlimited)
    max: false,
    // Should the element restore to it's original size after focus is lost?
    restore: false,
    // How many pixels to expand when the user is about to have to scroll. Defaults to 1 line.
    step: false
};

/**
 * These are presets. The presets are indexed by name containing different preset
 * option objects. When growfield is invoked with the preset's name, that options object
 * is loaded without having to be specified each time.
 */
$.fn.growfield.presets = {};

})(jQuery);

