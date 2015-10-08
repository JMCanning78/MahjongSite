(function($) {
	$(function () {
		var message = document.getElementById("message");

		window.getPlayers();
		function getTotalPoints() {
			var total = 0;
			$(".playerpoints").each(function (index, elem) {
				var val = $(this).val();
				if(val !== "")
					total += parseInt(val);

			});
			if(total > 25000 * 4 && $("#players .playerpoints").length == 4) {
				var select = document.createElement("select");
				select.className="playerselect";
				window.populatePlayersSelect($(select));
				$("#players").append(select);
				var input = document.createElement("input");
				input.className="playerpoints";
				input.placeholder = "Score";
				$(input).change(playerPointsChange);
				$("#players").append(input);
			}
			else if(total < 25000 * 4 && $("#players .playerpoints").length == 5){
				$("#players .playerpoints:last-child").last().remove();
				$("#players .playerselect:last-child").last().remove();
			}
			if(total === 25000 * 4 || total === 25000 * 5)
				$("#submit").prop("disabled", false);
			else
				$("#submit").prop("disabled", true);
		}

		function playerPointsChange() {
			getTotalPoints();
		}
		$(".playerpoints").change(playerPointsChange);
		$("#submit").click(function () {
			var scores = [];
			var points = $(".playerpoints").map(function() {
				return parseInt($(this).val());
			});
			var players = $(".playerselect").map(function() {
				return $(this).val();
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
					message.style.display = "";
					message.innerText = data.error;
				}
				else {
					$("#players").remove();
					$("#submit").remove();
					message.style.display = "";
					message.innerText = "Game added";
					var link = document.createElement("a");
					link.innerText = "View Leaderboard";
					link.href = "/leaderboard";

					$("body").append(message);
					$("body").append(link);
				}
			}, 'json')
		});
	});
})(jQuery);
