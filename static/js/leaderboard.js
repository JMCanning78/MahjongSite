$(function () {
	var leaderboard;
	var periods = ["annual", "biannual", "quarter"];
	$.get("/static/mustache/leaderboard.mst", function(data) {
		leaderboard = data;
		Mustache.parse(leaderboard);
		var period = document.URL.split('/');
		period = period[period.length - 1];
		if(periods.indexOf(period) !== -1)
			$("#period").val(period);
		getData($("#period").val());
	});
	function getData(period) {
		if(periods.indexOf(period) === -1)
			period = "annual";
		$.getJSON("/leaderdata/" + period, function(data) {
			$("#leaderboards").html(Mustache.render(leaderboard, data));
		});
	}
	$("#period").change(function () {
		getData($("#period").val());
	});
});
