(function($) {
	$(function () {
		var message = document.getElementById("message");

		var pointsChange;
		var playerScoreTemplate;
		$.get("/static/mustache/playerscore.mst", function(data) {
			playerScoreTemplate = data;
			Mustache.parse(playerScoreTemplate);
			addPlayers(4);
		});
		function addPlayers(num) {
			for(var i = 0; i < (num || 1); ++i)
				$("#players").append(Mustache.render(playerScoreTemplate));
		}
		function checkSubmit(total) {
			var playersSelected = true;
			$(".playercomplete").each(function (index, elem) {
				playersSelected = playersSelected && $(this).val() !== "";
			});


			playerSelected = playersSelected && (total === 25000 * 4 || total === 25000 * 5);
			$("#submit").prop("disabled", !playerSelected);
			return playerSelected;
		}
		function completeChange(e) {
			checkSubmit(getTotalPoints());
		}
		pointsChange = function(e) {
			var total = getTotalPoints();

			if(total > 25000 * 4 && $("#players .playerpoints").length == 4)
				addPlayers();
			else if(total === 25000 * 4 && $("#players .playerpoints").length == 5)
				$("#players .player:last-child").last().remove();

			if(checkSubmit(total) && e.keyCode === 13)
				submit();
		}
		function getTotalPoints() {
			var total = 0;
			$(".playerpoints").each(function (index, elem) {
				var val = $(this).val();
				total += val === ""?0:parseInt(val);
			});
			return total;

		}
		function submit() {
			var scores = [];
			var points = $(".playerpoints").map(function() {
				return parseInt($(this).val());
			});
			var chombos = $(".chombos").map(function() {
				var val = $(this).val();
				return val===""?0:parseInt(val);
			});
			var players = $(".playercomplete").map(function() {
				return $(this).val();
			});
			for(var i = 0; i < points.length; ++i) {
				scores.push({"player":players[i],"score":points[i],"chombos":chombos[i],"newscore":points[i]-chombos[i]*8000})
			}
			scores.sort(function(a, b) {
				return a.newscore > b.newscore ? -1 : a.newscore < b.newscore ? 1 : 0;
			});
			$.post('/addgame', {scores:JSON.stringify(scores)}, function(data) {
				console.log(data);
				if(data.status !== 0) {
					message.style.display = "block";
					$(message).text(data.error);
				}
				else {
					$("#players").remove();
					$("#submit").remove();
					message.style.display = "block";
					$(message).text("GAME ADDED");
					var add = document.createElement("a");
					$(add).text("ADD ANOTHER");
					add.href = "/addgame";
					var leaderboard = document.createElement("a");
					$(leaderboard).text("VIEW LEADERBOARD");
					leaderboard.href = "/leaderboard";
					var history = document.createElement("a");
					$(history).text("VIEW GAME HISTORY")
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
			$(".playercomplete").keyup(completeChange);
			$("#submit").click(submit);
		});
	});
})(jQuery);
