$(function() {
	$("#submit").on("click", function() {
		$("#submit").attr("disabled", true);
		var prevText = $("#submit").text();
		$("#submit").text("Adding...");

		submitGame('/addgame',
			function() {
				$("#message").text("GAME ADDED")
			},
			undefined,
			function() {
				$("#submit").attr("disabled", false);
				$("#submit").text(prevText);
			});
	});

	$("#tables").children(".table").click(function() {
		var players = $(this).children("div.player");
		if (players.length === 5 && $("#players .player").length === 4)
			window.addPlayers();
		else if (players.length === 4 && $("#players .player").length === 5)
			$($("#players .playercomplete")[4]).val("");
		players.each(function(i, elem) {
			$($("#players .playercomplete")[i])
				.val($(elem).clone().children().remove().end().text());
		});
	});
});
