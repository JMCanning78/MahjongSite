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
			$("#submit").click();
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
		if(gameComplete(getTotalPoints()) && e.keyCode === 13)
			$("#submit").click();
	}
	function getTotalPoints() {
		var total = 0;
		$(".playerpoints").each(function (index, elem) {
			total += parseInt($(this).val()) || 0;
		});
		return total;
	}
	function addPlayers(num) {
		for(var i = 0; i < (num || 1); ++i)
			$("#players").append(Mustache.render(playerScoreTemplate));
		window.populatePlayerComplete();
		$(".playerpoints").keyup(pointsChange);
		$(".playercomplete").keyup(completeChange);
	}
	window.submitGame = function(endpoint, callback, senddata) {
		senddata = senddata || {};
		var scores = [];
		var points = $(".playerpoints").map(function() {
			return parseInt($(this).val()) || 0;
		});
		var chombos = $(".chombos").map(function() {
			return parseInt($(this).val()) || 0;
		});
		var players = $(".playercomplete").map(function() {
			return $(this).val();
		});
		for(var i = 0; i < points.length; ++i) {
			scores.push({"player":players[i],"score":points[i],"chombos":chombos[i]})
		}
		senddata['scores'] = JSON.stringify(scores);
		$.post(endpoint, senddata, function(data) {
			console.log(data);
			if(data.status !== 0) {
				$("#message").text(data.error);
			}
			else {
				if(typeof callback === 'function')
					callback();
				$("#players").remove();
				$("#submit").remove();
				$("#content").append($("<a href='/leaderboard' class='button'>VIEW LEADERBOARD</a>"));
				$("#content").append($("<a href='/history' class='button'>VIEW GAME HISTORY</a>"));
			}
		}, 'json');
	}
});
