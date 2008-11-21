$(window).ready(
    function() {
       $("#menu-login a").click(function() {
           if($("#login-form").css("display") == "block") {
               $("#login-form").hide();
               return false;
           } else {
               $("#login-form").show();
               $("#login-form").css({"position":"absolute", "top":$("#menu-login").offset().top+60, "left":$("#menu-login").offset().left-110});
               return false;
           }
       }); 
    });
