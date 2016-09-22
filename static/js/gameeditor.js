$(function () {
	var message = document.getElementById("message");

	var playerScoreTemplate;
	$.get("/static/mustache/playerscore.mst", function(data) {
		playerScoreTemplate = data;
		Mustache.parse(playerScoreTemplate);
		addPlayers(4);
		if(typeof window.populatedEditor === "function")
			window.populatedEditor();
	});
	function pointsChange(e) {
		var total = getTotalPoints();
		$(message).text("Total: " + total);

		if(total > 25000 * 4 && $("#players .playerpoints").length == 4)
			addPlayers();
		else if(total === 25000 * 4 && $("#players .playerpoints").length == 5)
			$("#players .player:last-child").last().remove();

		var complete = gameComplete(total);
		if(complete && e.keyCode === 13)
			submit();
	}
	window.addPlayers = function(num) {
		for(var i = 0; i < (num || 1); ++i)
			$("#players").append(Mustache.render(playerScoreTemplate));
		populatePlayerComplete($("input.playercomplete"));
		$(".playerpoints").keyup(pointsChange);
		$(".playercomplete").keyup(completeChange);
	}
	function gameComplete(total) {
		var playersSelected = true;
		$(".playercomplete").each(function (index, elem) {
			playersSelected = playersSelected && $(this).val() !== "";
		});

		playersSelected = playersSelected && (total === 25000 * 4 || total === 25000 * 5);
		$("#submit").prop("disabled", !playersSelected);
		return playersSelected;
	}
	function completeChange(e) {
		gameComplete(getTotalPoints());
	}
	function getTotalPoints() {
		var total = 0;
		$(".playerpoints").each(function (index, elem) {
			var val = $(this).val();
			total += val === ""?0:parseInt(val);
		});
		return total;

	}
});
