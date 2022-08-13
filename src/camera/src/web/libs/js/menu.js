jQuery(document).ready(function($){

	var navigationContainer = $('#cd-nav').addClass('is-fixed'),
		mainNavigation = navigationContainer.find('#cd-main-nav ul');

	//open or close the menu clicking on the bottom "menu" link
	$('#cd-nav li a').on('click', function(){
        $('.cd-nav-trigger').click();
    })
	$('.cd-nav-trigger').on('click', function(){
		$(this).toggleClass('menu-is-open');
		//we need to remove the transitionEnd event handler (we add it when scolling up with the menu open)
		mainNavigation.off('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend').toggleClass('is-visible');

	});

});