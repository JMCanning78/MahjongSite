(function($) {
	$(function () {
		var message = document.getElementById("message");

		function checkSubmit(total) {
			var playersSelected = true;
			$(".playerselect").each(function (index, elem) {
				playersSelected = playersSelected && window.playersSelectValue($(this)) !== "";
			});

			if(playersSelected && (total === 25000 * 4 || total === 25000 * 5))
				$("#submit").prop("disabled", false);
			else
				$("#submit").prop("disabled", true);
		}
		function selectChange(e) {
			checkSubmit(getTotalPoints());
		}
		var pointsChange;
		pointsChange = function(e) {
			var total = getTotalPoints();

			if(total > 25000 * 4 && $("#players .playerpoints").length == 4) {
				var select = document.createElement("select");
				select.className="playerselect";
				window.populatePlayersSelect($(select));
				$(select).change(selectChange);
				$("#players").append(select);

				var input = document.createElement("input");
				input.className="playerpoints";
				input.placeholder = "SCORE";
				$(input).keyup(pointsChange);
				$("#players").append(input);
				full = false;
			}
			else if(total === 25000 * 4 && $("#players .playerpoints").length == 5){
				$("#players .playerpoints:last-child").last().remove();
				$("#players .playerselect:last-child").last().remove();
			}

			if(e.keyCode === 13)
				submit();
			checkSubmit(total);
		}
		function getTotalPoints() {
			var total = 0;
			$(".playerpoints").each(function (index, elem) {
				var val = $(this).val();
				if(val !== "")
					total += parseInt(val);
			});
			return total;

		}
		function submit() {
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
			points.sort(function(a, b) {
				return a.score > b.score ? 1 : a.score < b.score ? -1 : 0;
			});
			$.post('/addgame', {scores:JSON.stringify(scores)}, function(data) {
				console.log(data);
				if(data.status !== 0) {
					message.style.display = "block";
					window.setInnerText(message, data.error);
				}
				else {
					$("#players").remove();
					$("#submit").remove();
					message.style.display = "block";
					window.setInnerText(message, "Game added");
					var add = document.createElement("a");
					window.setInnerText(add, "Add another");
					add.href = "/addgame";
					var leaderboard = document.createElement("a");
					window.setInnerText(leaderboard, "View Leaderboard");
					leaderboard.href = "/leaderboard";
					var history = document.createElement("a");
					window.setInnerText(history, "View Game History");
					history.href = "/history";

					$("#content").append(message);
					$("#content").append(add);
					$("#content").append(leaderboard);
					$("#content").append(history);
				}
			}, 'json')
		}
		window.getPlayers(function () {
			$(".playerpoints").keyup(pointsChange);
			$(".playerselect").change(selectChange);
			$("#submit").click(submit);
		});
	});
})(jQuery);
