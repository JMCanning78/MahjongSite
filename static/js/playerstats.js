$(function () {
	var playerstats;
	$.get("/static/mustache/playerstats.mst", function(data) {
		playerstats = data;
		Mustache.parse(playerstats);
		var parts = document.URL.split('/');
		player = parts[parts.length - 1];
		getData(player);
	});
	function getData(player) {
		$.getJSON("/playerstatsdata/" + player, function(data) {
		    $("#playerstats").html(Mustache.render(playerstats, data));
		});
	}
});
