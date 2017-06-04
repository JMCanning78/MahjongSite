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
				scores.push({"player":players[i],"score":points[i],"chombos":chombos[i]})
			}
			$.post('/admin/edit/' + window.gameid, {scores:JSON.stringify(scores), gamedate:$("#gamedate").val()}, function(data) {
				console.log(data);
				if(data.status !== 0) {
					$(message).text(data.error);
				}
				else {
					$("#gamedate").remove();
					$("#players").remove();
					$("#submit").remove();
					$(message).text("GAME EDITED");
					var reedit = document.createElement("a");
					$(reedit).text("EDIT AGAIN");
					reedit.href = "/admin/edit/" + window.gameid;
					reedit.className = "button";
					var leaderboard = document.createElement("a");
					$(leaderboard).text("VIEW LEADERBOARD");
					leaderboard.href = "/leaderboard";
					leaderboard.className = "button";
					var history = document.createElement("a");
					$(history).text("VIEW GAME HISTORY")
					history.href = "/history";
					history.className = "button";

					$("#content").append(message);
					$("#content").append(reedit);
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
