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
				$("#leaderboards").html(Mustache.render(leaderboard, data)).promise().done(function() {
					$(".ordering").click(changeOrdering);
					updateLeaderScores($("#min_games").val(), rank_visible());
					$("tr.eligible, div.membersymbol").click(
						scrollToLegend);
					setupReturnToTop(".returntotop")
				});
			});
	};

	function scrollToLegend() { // Smooth scroll to bottom, slow->fast->slow
		window.smoothScrollTo();
	};

	function totalDigits(counttext) {
		return counttext.split(/[^0-9]+/).map(Math.floor).reduce(
			function(t, e) {
				return t + e
			})
	}

	function updateLeaderScores(min_games, rank_visible) {
		$(".leaderboard").each(function(i, board) {
			/* Get the scores for this board */
			var boardname = $(".lbname", board).text();
			var bd_scores;
			for (bd in scores['leaderboards']) {
				if (scores['leaderboards'][bd]['Date'] == boardname) {
					bd_scores = scores['leaderboards'][bd]['Board'];
					break;
				};
			}
			var last_place = 0;
			$(".leaderbd_row", board).each(function(i, row) {
				/* Hide rows with game counts less than the min games */
				var counttext = row.children[3].innerText,
					count = totalDigits(counttext);

				/* Hide rows with too few games */
				if (count < min_games) {
					$(row).slideUp('fast');
				}
				else {
					$(row).slideDown('fast');
					if (++last_place == bd_scores[i]['Place']) {
						row.children[0].innerText =
							(rank_visible ? last_place :
								bd_scores[i]['Place']).toString();
					}
					else if (rank_visible) {
						row.children[0].innerText = last_place.toString();
					}
					else {
						row.children[0].innerText = '... ' +
							bd_scores[i]['Place'].toString();
						last_place = bd_scores[i]['Place'];
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
		var period = $("#period").val();
		getData(period);
		$(".helptext").slideUp();
		$("." + period + "_help").slideDown();
	});
	$("#min_games").change(function() {
		updateLeaderScores($("#min_games").val(), rank_visible());
	});
});
