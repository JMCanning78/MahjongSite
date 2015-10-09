(function($) {
	$(function () {
		var message = document.getElementById("message");

		window.getPlayers();
		function getTotalPoints() {
			var total = 0;
			var full = true;
			$(".playerpoints").each(function (index, elem) {
				var val = $(this).val();
				if(val !== "")
					total += parseInt(val);
				else
					full = false;

			});
			if(full && total > 25000 * 4 && $("#players .playerpoints").length == 4) {
				var select = document.createElement("select");
				select.className="playerselect";
				window.populatePlayersSelect($(select));
				$("#players").append(select);
				var input = document.createElement("input");
				input.className="playerpoints";
				input.placeholder = "Score";
				$(input).keypress(playerPointsChange);
				$("#players").append(input);
			}
			else if(total <= 25000 * 4 && $("#players .playerpoints").length == 5){
				$("#players .playerpoints:last-child").last().remove();
				$("#players .playerselect:last-child").last().remove();
			}
			if(full && (total === 25000 * 4 || total === 25000 * 5))
				$("#submit").prop("disabled", false);
			else
				$("#submit").prop("disabled", true);
		}

		function playerPointsChange() {
			getTotalPoints();
		}
		$(".playerpoints").keypress(playerPointsChange);
		$("#submit").click(function () {
			var scores = [];
			var points = $(".playerpoints").map(function() {
				return parseInt($(this).val());
			});
			var players = $(".playerselect").map(function() {
				return window.playersSelectValue($(this));
			});
			for(var i = 0; i < points.length; ++i) {
				scores.push({"player":players[i],"score":points[i]})
			}
			console.log(scores);
			points.sort(function(a, b) {
				return a.score > b.score ? 1 : a.score < b.score ? -1 : 0;
			});
			$.post('/addgame', {scores:JSON.stringify(scores)}, function(data) {
				console.log(data);
				if(data.status !== 0) {
					message.style.display = "block";
					message.innerText = data.error;
				}
				else {
					$("#players").remove();
					$("#submit").remove();
					message.style.display = "block";
					message.innerText = "Game added";
					var add = document.createElement("a");
					add.innerText = "Add another";
					add.href = "/addgame";
					var leaderboard = document.createElement("a");
					leaderboard.innerText = "View Leaderboard";
					leaderboard.href = "/leaderboard";
					var history = document.createElement("a");
					history.innerText = "View Game History";
					history.href = "/history";

					$("#content").append(message);
					$("#content").append(add);
					$("#content").append(leaderboard);
					$("#content").append(history);
				}
			}, 'json')
		});
	});
})(jQuery);
