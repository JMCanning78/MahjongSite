$(function() {
	var message = document.getElementById("message");

	var playerScoreTemplate;

	$.get("/static/mustache/playerscore.mst", function(data) {
		playerScoreTemplate = data;
		Mustache.parse(playerScoreTemplate);
		addPlayers(4);
		if (typeof window.populatedEditor === "function")
			window.populatedEditor();
	});

	function updateTotal() {
		var total = getTotalPoints();
		$(message).text("Total: " +
			(total < 1000 ? total :
				Math.floor(total / 1000) + "," +
				"00".substr(Math.log10(last3 = total % 1000)) + last3));
		return total;
	}

	function updateHelp() {
		if ($("#players .playerpoints").length === 5) {
			$('.player5help').hide();
			$('.player4help').show();
		}
		else {
			$('.player5help').show();
			$('.player4help').hide();
		}
	}

	function pointsChange(e) {
		var total = updateTotal();

		if (total > 25000 * 4 && $("#players .playerpoints").length === 4) {
			addPlayers();
		}
		else if (total === 25000 * 4 && $("#players .playerpoints").length === 5) {
			$("#players .player:last-child").last().remove();
			updateTotal();
		}
		updateHelp();

		var complete = gameComplete(total);
		if (complete && e.keyCode === 13)
			$("#submit").click();
	}

	function gameComplete(total) {
		var ready = true;
		$(".playercomplete").each(function(index, elem) {
			ready = ready && $(this).val() !== "";
		});

		ready = ready && (total === 25000 * 4 || total === 25000 * 5) &&
			checkUnusedPoints();

		$("#submit").prop("disabled", !ready);
		return ready;
	}

	function completeChange(e) {
		if (gameComplete(getTotalPoints()) && e.keyCode === 13)
			$("#submit").click();
	}

	function getTotalPoints() {
		var total = 0;
		$(".playerpoints, #unusedPoints").each(function(index, elem) {
			total += parseInt($(this).val()) || 0;
		});
		return total;
	}

	function addPlayers(num) {
		for (var i = 0; i < (num || 1); ++i)
			$("#players").append(Mustache.render(playerScoreTemplate));
		window.populatePlayerComplete();
		$(".playerpoints").change(pointsChange).keyup(pointsChange);
		$(".chombos").change(pointsChange).keyup(pointsChange);
		$(".playercomplete").change(completeChange).keyup(completeChange);
		$("#unusedPoints").change(pointsChange).keyup(pointsChange);
	}

	window.checkUnusedPoints = function() {
		var unusedPoints = $("#unusedPoints");
		if (unusedPoints.length == 0)
			return true;
		var unusedPointsIncrement = parseInt(unusedPoints.attr("step")),
			entry = parseInt(unusedPoints.val()) || 0,
			good = (unusedPointsIncrement == 0) ||
			(entry % unusedPointsIncrement) == 0;
		unusedPoints.removeClass(good ? "bad" : "good");
		unusedPoints.addClass(good ? "good" : "bad");
		return good;
	}

	window.submitGame = function(endpoint, callback, senddata) {
		console.log(senddata);
		senddata = senddata || {};
		var scores = [];
		var points = $(".playerpoints").map(function() {
			return parseInt($(this).val()) || 0;
		});
		var chombos = $(".chombos").map(function() {
			return parseInt($(this).val()) || 0;
		});
		var players = $(".playercomplete").map(function() {
			return $(this).val();
		});
		for (var i = 0; i < points.length; ++i) {
			scores.push({
				"player": players[i],
				"score": points[i],
				"chombos": chombos[i]
			})
		};
		$("#unusedPoints").each(function() {
			var val = $(this).val();
			if (val != "" && parseInt(val) > 0) {
				scores.push({
					"player": -1,
					"score": parseInt(val),
					"chombos": 0
				});
			};
		});
		senddata['scores'] = JSON.stringify(scores);
		$.post(endpoint, senddata, function(data) {
			if (data.status !== 0) {
				$("#message").text(data.error);
			}
			else {
				if (typeof callback === 'function')
					callback();
				$("#content > *").not("#message").remove();
				$("#content").append(
					$("<a href='/addgame' class='button'>" +
						"ADD ANOTHER</a>"),
					$("<a href='/leaderboard' class='button'>" +
						"VIEW LEADERBOARD</a>"),
					$("<a href='/history' class='button'>" +
						"VIEW GAME HISTORY</a>"));
			}
		}, 'json');
	}

	$("#unusedpoints").change(checkUnusedPoints);

	var tablesTemplate;
	$("#seating").click(function() {
		function _getCurrentTables() {
			$.getJSON('/seating/currenttables.json', function(data) {
				if (data.status === "success") {
					$("#tables").html(
						"<h3>Click a table to insert its players into the form</h3>" +
						Mustache.render(tablesTemplate, {
							"tables": data.tables
						})
					);
					$("#tables").children(".table").click(function() {
						var players = $(this).children("div");
						if (players.length === 5 && $("#players .player").length === 4)
							addPlayers();
						else if (players.length === 4 && $("#players .player").length === 5)
							$($("#players .playercomplete")[4]).val("");
						players.each(function(i, elem) {
							$($("#players .playercomplete")[i]).val($(elem).clone().children().remove().end().text());
						});
					});
				}
				else
					$("#tables").text(data.message);
			}).fail(xhrError);
		}
		if (tablesTemplate === undefined)
			$.get("/static/mustache/tables.mst", function(data) {
				tablesTemplate = data;
				Mustache.parse(tablesTemplate);
				_getCurrentTables();
			});
		else
			_getCurrentTables();
	});
});
