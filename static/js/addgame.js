(function($) {
	$(function () {
		$("#submit").click(window.submitGame.bind(this,
			"/addgame", function() {
				$("#message").text("GAME ADDED");
				$("#content").append($("<a href='/addgame' class='button'>ADD ANOTHER</a>"));

			        $(".player5help").each(function (index, elem) {
				    elem.style.display = "none"
				});
			        $(".player4help").each(function (index, elem) {
				    elem.style.display = "none"
				});
			}, undefined));
	});
})(jQuery);
