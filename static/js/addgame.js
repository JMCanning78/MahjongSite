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
		var tplayers = $(this).children("div.player");
		if (tplayers.length == 5 && $("#players .player").length == 4)
			window.addPlayers();
		else if (tplayers.length == 4 && $("#players .player").length == 5)
			window.addPlayers(-1);
		tplayers.each(function(i, elem) {
			$($("#players .playercomplete")[i])
				.val($(elem).clone().children().remove().end().text());
		});
		window.smoothScrollTo(0, 0);
	});
});
