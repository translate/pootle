(function ($) {
    
    window.PTL = window.PTL || {};

    PTL.reports = {

        init: function () {
            
            /* Compile templates */
            this.tmpl = {results: $.template($("#language_user_activity").html()),};

            $(document).on("click", "#reports-show", function (e) {
                PTL.reports.date_range = PTL.reports.calendar.getSelectedAsText();
                PTL.reports.user = $('#reports-user').val();
                
                PTL.reports.update();               
            });

            $(document).on("click", "#current-month", function (e) {
                PTL.reports.calendar.setSelected([Kalendae.moment().date(1), Kalendae.moment()]);
                PTL.reports.date_range = PTL.reports.calendar.getSelectedAsText();

                PTL.reports.update();

                return false;
            });

            $(document).on("click", "#previous-month", function (e) {
                PTL.reports.calendar.setSelected([Kalendae.moment().subtract({M:1}).date(1), Kalendae.moment().date(1).subtract('days', 1)]);
                PTL.reports.date_range = PTL.reports.calendar.getSelectedAsText();

                PTL.reports.update();

                return false;
            });

            $(document).on("keypress", "#reports-user", function (e) {
                if (e.which === 13) {
                    PTL.reports.user = $('#reports-user').val();

                    PTL.reports.update();     
                }
            });
            
            this.calendar = new Kalendae({
                attachTo: document.getElementById('reports-calendar'),
                months:3,
                mode:'range',
                selected:[Kalendae.moment().date(1), Kalendae.moment()]
            });
            
            this.date_range = this.calendar.getSelectedAsText();
            this.user = null;

            PTL.reports.currentRowIsEven = false;

            setTimeout(function () {
                $.history.init(function (hash) {
                
                    var params = PTL.utils.getParsedHash(hash);

                    // Walk through known report criterias and apply them to the reports object
                    if ('start' in params && 'end' in params) {
                        PTL.reports.date_range = [params['start'], params['end']];
                    } 

                    if ('user' in params) {
                        PTL.reports.user = params['user'];    
                    } 
                                       
                    $('#reports-user').val(PTL.reports.user);
                    PTL.reports.calendar.setSelected(PTL.reports.date_range);     
                    PTL.reports.buildResults();

                }, {'unescape': true});

            }, 1); // not sure why we had a 1000ms timeout here


        },

        validate: function() {
            if (PTL.reports.user) {
                return  PTL.reports.date_range.length == 2;
            } else {
                return false;
            }
        },

        update: function() {
            if (PTL.reports.validate()) {
                var newHash = "user=" + PTL.reports.user + "&start=" + PTL.reports.date_range[0] + "&end=" + PTL.reports.date_range[1];
                $.history.load(newHash);
            } else {
                alert('Wrong input data');
            }
        },

        buildResults: function () {
            reqData = {start: PTL.reports.date_range[0], end: PTL.reports.date_range[1], user: PTL.reports.user};

            $.ajax({
                url: 'activity',
                data: reqData,
                dataType: 'json',
                async: true,
                success: function (data) {
                    $('#reports-results').empty();
                    $('#reports-results').html(PTL.reports.tmpl.results($, {data: data}).join(""));     
                },
                error: function(xhr, s) {
                    alert('Error status: ' + xhr.status);
                }
            });
        },

        dateRangeString: function (d1, d2) {
            var res = '';
            var m1 = Kalendae.moment(d1);
            var m2 = Kalendae.moment(d2);
            
            if (m1.year() == m2.year()) {
                if (m1.month() == m2.month()) {
                    if (m1.date() == m2.date()) {
                        return m1.format('MMMM D, YYYY');
                    } else {
                        return m1.format('MMMM D') + ' &mdash; ' + m2.date() + m2.format(', YYYY');
                    }
                } else {
                    return m1.format('MMMM D') + ' &mdash; ' + m2.format('MMMM D, YYYY');
                }   
            } else {
                return m1.format('MMMM D, YYYY') + ' &mdash; ' + m2.format('MMMM D, YYYY');
            }
        },

        formatDate: function (d) {
            m = Kalendae.moment(d);
            return m.format('MMM, D');
        },

        cycleEvenOdd: function() {
            PTL.reports.currentRowIsEven = !PTL.reports.currentRowIsEven;
            
            if (PTL.reports.currentRowIsEven) {
                return 'even';
            } else {
                return 'odd';
            }
        },

        resetRowStyle: function() {
            PTL.reports.currentRowIsEven = false;
        }



    };

})(jQuery);

$(function ($) {
    PTL.reports.init();
});
