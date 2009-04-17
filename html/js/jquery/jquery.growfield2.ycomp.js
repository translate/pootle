/*
 * jQuery Growfield Library 2
 *
 * http://code.google.com/p/jquery-dynamic/
 * licensed under the MIT license
 *
 * autor: john kuindji
 */

(function($) {

if ($.support == undefined) $.support = {boxModel: $.boxModel};
var windowLoaded = false;
$(window).one('load', function(){ windowLoaded=true; });

// we need to adapt jquery animations for textareas.
// by default, it changes display to 'block' if we're trying to
// change width or height. We have to prevent this.
$.fx.prototype.originalUpdate = $.fx.prototype.update;
$.fx.prototype.update = false;
$.fx.prototype.update = function () {
    if (!this.options.inline) return this.originalUpdate.call(this);
    if ( this.options.step )
        this.options.step.call( this.elem, this.now, this );
        (jQuery.fx.step[this.prop] || jQuery.fx.step._default)( this );
};

var growfield = function(dom) {
    this.dom = dom;
    this.o = $(dom);

    this.opt = {
        auto: true, animate: 100, easing: null,
        min: false, max: false, restore: false,
        step: false
    };

    this.enabled = this.dummy = this.busy =
    this.initial = this.sizeRelated = this.prevH = this.firstH = false;
};

growfield.prototype = {

    toggle: function(mode) {
        if ((mode=='disable' || mode===false)&&this.enabled) return this.setEvents('off');
        if ((mode=='enable' || mode===true)&&!this.enabled) return this.setEvents('on');
        return this;
    },

    setEvents: function(mode) {
        var o = this.o, opt = this.opt, th = this, initial = false;

        if (mode=='on' && !this.enabled) {
            var windowLoad = o.height() == 0 ? true : false;

            if (!windowLoad || windowLoaded) $(function() { th.prepareSizeRelated(); });
            else $(window).one('load', function() {th.prepareSizeRelated(); });

            if (opt.auto) { // auto mode, textarea grows as you type

                o.bind('keyup.growfield', function(e) { th.keyUp(e); return true; });
                o.bind('focus.growfield', function(e) { th.focus(e); return true; });
                o.bind('blur.growfield', function(e) { th.blur(e); return true; });
                initial = {
                    overflow: o.css('overflow'),
                    cssResize: o.css('resize')
                };
                if ($.browser.safari) o.css('resize', 'none');
                this.initial = initial;
                o.css({overflow: 'hidden'});

                // all styles must be loaded before prepare elements
                if (!windowLoad || windowLoaded) $(function() {
                    th.createDummy(); });
                else $(window).one('load', function() { th.createDummy(); });

            } else { // manual mode, textarea grows as you type ctrl + up|down
                o.bind('keydown.growfield', function(e) { th.manualKeyUp(e); return true; });
                o.css('overflow-y', 'auto');
                if (!windowLoad || windowLoaded) $(function() { th.update(o.height());});
                else $(window).one('load', function() { th.update(o.height()); });
            }
            o.addClass('growfield');
            this.enabled = true;
        }
        else if (mode=='off' && this.enabled) {
            if (this.dummy) {
                this.dummy.remove();
                this.dummy = false;
            }
            o.unbind('.growfield').css('overflow', this.initial.overflow);
            if ($.browser.safari) o.css('resize', this.initial.cssResize);
            this.enabled = false;
        }
        return this;
    },

    setOptions: function(options) {
        var opt = this.opt, o = this.o;
        $.extend(opt, options);
        if (!$.easing) opt.easing = null;
    },

    update: function(h, animate) {
        var sr = this.sizeRelated, val = this.o.val(), opt = this.opt, dom = this.dom, o = this.o,
              th = this, prev = this.prevH;
        var noHidden = !opt.auto, noFocus = opt.auto;

        h = this.convertHeight(Math.round(h), 'inner');
        // get the right height according to min and max value
        h = opt.min > h ? opt.min :
              opt.max && h > opt.max ? opt.max :
              opt.auto && !val ? opt.min : h;

        if (opt.max && opt.auto) {
            if (prev != opt.max && h == opt.max) { // now we reached maximum height
                o.css('overflow-y', 'scroll');
                if (!opt.animate) o.focus(); // browsers do loose cursor after changing overflow :(
                noHidden = true;
                noFocus = false;
            }
            if (prev == opt.max && h < opt.max) {
                o.css('overflow-y', 'hidden');
                if (!opt.animate) o.focus();
                noFocus = false;
            }
        }

        if (h == prev) return true;
        this.prevH = h;

        if (animate) {
            th.busy = true;
            o.animate({height: h}, {
                duration: opt.animate,
                easing: opt.easing,
                overflow: null,
                inline: true, // this option isn't jquery's. I added it by myself, see above
                complete: function(){
                    // safari/chrome fix
                    // somehow textarea turns to overflow:scroll after animation
                    // i counldn't find it in jquery fx :(, so it looks like some bug
                    if (!noHidden) o.css('overflow', 'hidden');
                    // but if we still need to change overflow (due to opt.max option)
                    // we have to invoke focus() event, otherwise browser will loose cursor
                    if (!noFocus) o.focus();
                    th.busy = false;
                },
                queue: false
            });
        } else dom.style.height = h+'px';
    },

    manualKeyUp: function(e) {
        if (!e.ctrlKey) return;
        if (e.keyCode != 38 && e.keyCode != 40) return;
        this.update(
            this.o.outerHeight() + (this.opt.step*( e.keyCode==38? -1: 1)),
            this.opt.animate
        );
    },

    keyUp: function(e) {
        if (this.busy) return true;
        if ($.inArray(e.keyCode, [37,38,39,40]) != -1) return true;
        this.update(this.getDummyHeight(), this.opt.animate);
    },

    focus: function(e) {
        if (this.busy) return true;
        if (this.opt.restore) this.update(this.getDummyHeight(), this.opt.animate);
    },

    blur: function(e) {
        if (this.busy) return true;
        if (this.opt.restore) this.update(0, false);
    },

    getDummyHeight: function() {
        var val = this.o.val(), h = 0, sr = this.sizeRelated, add = "\n111\n111";

        // Safari has some defect with double new line symbol at the end
        // It inserts additional new line even if you have only one
        // But that't not the point :)
        // Another question is how much pixels to keep at the bottom of textarea.
        // We'll kill many rabbits at the same time by adding two new lines at the end
        if ($.browser.safari) val = val.substring(0, val.length-1); // safari has an additional new line ;(

        if (!sr.lh || !sr.fs) val += add;

        this.dummy.val(val);

        // IE requires to change height value in order to recalculate scrollHeight.
        // otherwise it stops recalculating scrollHeight after some magical number of pixels
        if ($.browser.msie) this.dummy[0].style.height = this.dummy[0].scrollHeight+'px';

        h = this.dummy[0].scrollHeight;
        if (sr.lh && sr.fs) h += sr.lh > sr.fs ? sr.lh+sr.fs :  sr.fs * 2;

        // now we have to minimize dummy back, or we'll get wrong scrollHeight next time
        if ($.browser.msie) this.dummy[0].style.height = '20px'; // random number

        return h;
    },

    createDummy: function() {
        var o = this.o, val = this.o.val();
        // we need dummy to calculate scrollHeight
        // (there are some tricks that can't be applied to the textarea itself, otherwise user will see it)
        // Also, dummy must be a textarea too, and must be placed at the same position in DOM
        // in order to keep all the inherited styles
        var dummy = o.clone().addClass('growfieldDummy').attr('name', '').attr('tabindex', -9999)
                               .css({position: 'absolute', left: -9999, top: 0, height: '20px', resize: 'none'})
                               .insertBefore(o).show();

        // if there is no initial value, we have to add some text, otherwise textarea will jitter
        // at the first keydown
        if (!val) dummy.val('dummy text');
        this.dummy = dummy;
        // lets set the initial height
        this.update(!jQuery.trim(val) ? 0 : this.getDummyHeight(), false);
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
    },

    prepareSizeRelated: function() {
        var o = this.o, opt = this.opt;

        if (!opt.min) {
            opt.min = parseInt(o.css('min-height'), 10) || this.firstH || parseInt(o.height(), 10) || 20;
            if (opt.min <= 0) opt.min = 20; // opera fix
            if (!this.firstH) this.firstH = opt.min;
        }
        if (!opt.max) {
            opt.max = parseInt(o.css('max-height'), 10) || false;
            if (opt.max <= 0) opt.max = false; // opera fix
        }
        if (!opt.step) opt.step = parseInt(o.css('line-height'), 10) || parseInt(o.css('font-size'), 10) || 20;

        var sr = {
            pt: parseInt(o.css('paddingTop'), 10)||0,
            pb: parseInt(o.css('paddingBottom'), 10)||0,
            bt: parseInt(o.css('borderTopWidth'), 10)||0,
            bb: parseInt(o.css('borderBottomWidth'), 10)||0,
            lh: parseInt(o.css('lineHeight'), 10) || false,
            fs: parseInt(o.css('fontSize'), 10) || false
        };

        this.sizeRelated = sr;
    }
};

$.fn.growfield = function(options) {
    if ('destroy'==options) return this.each(function() {
        var gf = $(this).data('growfield');
        if (gf == undefined) return true;
        gf.toggle(false);
        $(this).removeData('growfield');
        return true;
    });
    if ('restart'==options) return this.each(function(){
        var gf = $(this).data('growfield');
        if (gf == undefined) return true;
        gf.toggle(false).toggle(true);
    });
    var tp = typeof options;
    return this.each(function() {
        if (!/textarea/i.test(this.tagName)||$(this).hasClass('growfieldDummy')) return true;
        var initial = false, o = $(this), gf = o.data('growfield');
        if (gf == undefined) {
            initial = true;
            o.data('growfield', new growfield(this));
            gf = o.data('growfield');
        }
        if (initial) {
            var opt = $.extend({}, $.fn.growfield.defaults, options);
            gf.setOptions(opt);
        }
        if (!initial && (!options || tp == 'object')) gf.setOptions(options);
        if (tp == 'string') {
            if (options.indexOf('!')==0 && $.fn.growfield.presets[options.substr(1)]) o.unbind('.'+i+'.'+options.substr(1));
            else if ($.fn.growfield.presets[options]) {
                var pOpt = $.fn.growfield.presets[options];
                gf.setOptions(pOpt, options);
            }
        }
        if (initial && !opt.skipEnable) gf.toggle(true);
        if (!initial && (tp == 'boolean' || options=='enable' || options == 'disable')) gf.toggle(options);
    });
};

$.fn.growfield.defaults = {};
$.fn.growfield.presets = {};

})(jQuery);