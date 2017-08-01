$(function () {
	var leaderboard;
	var periods = ["annual", "biannual", "quarter"];
	$.get("/static/mustache/leaderboard.mst", function(data) {
		leaderboard = data;
	        Mustache.parse(leaderboard);
                var parts = document.URL.split('/');
                var period = parts[parts.length - 2];
                var min_games = Math.floor(parts[parts.length - 1]);
		if(periods.indexOf(period) !== -1)
			$("#period").val(period);
                if(isNaN(min_games))
                        min_games = 1
                $("#min_games").val(min_games);
                getData($("#period").val(), $("#min_games").val());
	});
        function getData(period, min_games) {
		if(periods.indexOf(period) === -1)
			period = "quarter";
		$.getJSON("/leaderdata/" + period + '/' + min_games ,
			  function(data) {
			$("#leaderboards").html(Mustache.render(leaderboard, data));
		});
	}
	$("#period").change(function () {
		getData($("#period").val(), $("#min_games").val());
	});
	$("#min_games").change(function () {
		getData($("#period").val(), $("#min_games").val());
	});
});
