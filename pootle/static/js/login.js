// Evernote JS file login.js
function link_with_existing() {
	$('.form.info').removeClass('hide');
	$('.login').removeClass('hide');
	$('.form.question').addClass('hide');
	$("#id_username").focus();
}

function pootle_login() {
	$('.login').removeClass('hide');
	$("#id_username").focus();
}
