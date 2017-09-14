$(function() {
	$("#submit").on("click", function() {
		submitGame('/addgame',
			function() {
				$("#message").text("GAME ADDED")
			},
			undefined);
	});
});
