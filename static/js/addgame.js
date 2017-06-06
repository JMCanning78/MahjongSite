(function($) {
	$(function () {
		$("#submit").click(window.submitGame.bind(this,
			"/addgame", function() {
				$("#message").text("GAME ADDED");
				$("#content").append($("<a href='/addgame' class='button'>ADD ANOTHER</a>"));
			}, undefined));
	});
})(jQuery);
