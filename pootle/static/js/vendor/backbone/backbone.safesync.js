(function(_, Backbone) {
    var sync = Backbone.sync;

    Backbone.sync = function(method, model, options) {
        var lastXHR = model._lastXHR && model._lastXHR[method];

        if ((lastXHR && lastXHR.readyState != 4) && (options && options.safe !== false))
            lastXHR.abort('stale');

        if (!model._lastXHR)
            model._lastXHR = {};

        return model._lastXHR[method] = sync.apply(this, arguments);
    };
})(window._, window.Backbone);
