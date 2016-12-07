(function($) {
	$(function () {
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
					$(message).text(data.error);
				}
				else {
					$("#players").remove();
					$("#submit").remove();
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
			$("#submit").click(submit);
		});
	});
})(jQuery);
