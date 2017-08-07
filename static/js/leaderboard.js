$(function() {
	var leaderboard;
	var periods = ["annual", "biannual", "quarter"];
	var orderings = ["PLACE", "ORDER"];
	var min_games = 1;
	var scores;
	$.get("/static/mustache/leaderboard.mst", function(data) {
		leaderboard = data;
		Mustache.parse(leaderboard);
		var parts = document.URL.split('/');
		var period = parts[parts.length - 1];
		if (periods.indexOf(period) !== -1)
			$("#period").val(period);
		if (isNaN(min_games))
			min_games = 1
		$("#min_games").val(min_games);
		getData($("#period").val());
	});

	function getData(period) {
		if (periods.indexOf(period) === -1)
			period = "quarter";
		$.getJSON("/leaderdata/" + period,
			function(data) {
				scores = data;
				$("#leaderboards").html(Mustache.render(leaderboard, data));
				$(".ordering").click(changeOrdering);
				updateLeaderScores($("#min_games").val(), rank_visible());
			});
	}

	function updateLeaderScores(min_games, rank_visible) {
		$(".leaderboard").each(function(i, board) {
			/* Get the scores for this board */
			var boardname = $("#lbname", board).text();
			var bd_scores;
			for (bd in scores['leaderboards']) {
				if (scores['leaderboards'][bd]['name'] == boardname) {
					bd_scores = scores['leaderboards'][bd]['scores'];
					break;
				};
			}
			var last_place = 0;
			$(".leaderbd_row", board).each(function(i, row) {
				/* Hide rows with game counts less than the min games */
				var counttext = row.children[3].innerText;
				var plus1 = counttext.search(/[^0-9]/)
				if (plus1 < 0) {
					count = Math.floor(counttext)
				} else if (plus1 == 0) {
					count = 0
				} else {
					count = Math.floor(counttext.substr(0, plus1)) + 1
				}
				/* Hide rows with too few games */
				if (count < min_games) {
					$(row).slideUp('fast');
				} else {
					$(row).slideDown('fast');
					if (++last_place == bd_scores[i]['place']) {
						row.children[0].innerText =
							(rank_visible ? last_place :
								bd_scores[i]['place']).toString();
					} else if (rank_visible) {
						row.children[0].innerText = last_place.toString();
					} else {
						row.children[0].innerText = '... ' +
							bd_scores[i]['place'].toString();
						last_place = bd_scores[i]['place'];
					}
				}
			});
		});
	}

	function changeOrdering() {
		var currenttext = $(".ordering:first").text();
		var i = orderings.indexOf(currenttext);
		if (i < 0) {
			i = 0
		};
		$(".ordering").each(function(j, e) {
			$(e).text(orderings[1 - i]);
		});
		updateLeaderScores($("#min_games").val(), i == 0)
	}

	function rank_visible() {
		return orderings.indexOf($(".ordering:first").text()) == 1;
	}
	$("#period").change(function() {
		getData($("#period").val());
	});
	$("#min_games").change(function() {
		updateLeaderScores($("#min_games").val(), rank_visible());
	});
});
