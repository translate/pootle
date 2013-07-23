// Evernote JS file login.js
function link_with_existing() {
	$('.form.info').removeClass('hidden');
	$('.login').removeClass('hidden');
	$('.form.question').addClass('hidden');
	$("#id_username").focus();
}

function pootle_login() {
	$('.login').removeClass('hidden');
	$("#id_username").focus();
}


