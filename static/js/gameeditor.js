$(function() {
	var message = document.getElementById("message");

	var playerScoreTemplate, scorePerPlayer = 25000,
		unusedPointsIncrement = 0;

	$.get("/static/mustache/playerscore.mst", function(data) {
		playerScoreTemplate = data;
		Mustache.parse(playerScoreTemplate);
		addPlayers(4);
		if (typeof window.populatedEditor === "function")
			window.populatedEditor();
	});

	function updatePointSettings() {
		var date = $("#gamedate").val(),
			param = date ? "?date=" + date : "";
		$.get("/pointsettings" + param,
			function(data) {
				if (data.status == 0) {
					scorePerPlayer = data.scorePerPlayer;
					unusedPointsIncrement = data.unusedPointsIncrement;
					$("#unusedpoints").prop("step", unusedPointsIncrement);
					gameComplete();
					checkUnusedPoints();
					$(".gametotal").text(
						addCommaSeparators(
							$("#players .playerpoints").length *
							scorePerPlayer));
				}
			}, 'json');
	}
	$(updatePointSettings);

	function addCommaSeparators(num, digits) {
		if (digits == null) {
			digits = 3
		};
		var thresh = Math.pow(10, digits),
			result = "",
			sign = num < 0 ? "-" : "";
		if (num < 0) {
			num = -num
		};
		while (num >= thresh) {
			s = "" + num;
			result = "," + s.slice(-digits) + result
			num = Math.floor(num / thresh)
		}
		return sign + num + result
	};

	function updateTotal() {
		var total = getTotalPoints();
		$(message).text("Total: " + addCommaSeparators(total));
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

		if (total > scorePerPlayer * 4 && $("#players .playerpoints").length === 4) {
			addPlayers();
		}
		else if (total === scorePerPlayer * 4 && $("#players .playerpoints").length === 5) {
			$("#players .player:last-child").last().remove();
			updateTotal();
		}
		updateHelp();

		var complete = gameComplete(total);
		if (complete && e.keyCode === 13)
			$("#submit").click();
	}

	function gameComplete(total) {
		if (total == null) {
			total = getTotalPoints()
		};
		var ready = true;
		$(".playercomplete").each(function(index, elem) {
			ready = ready && $(this).val() !== "";
		});

		ready = ready && (total === scorePerPlayer * 4 ||
				total === scorePerPlayer * 5) &&
			checkUnusedPoints();

		$("#submit").prop("disabled", !ready);
		return ready;
	}

	function completeChange(e) {
		if (gameComplete() && e.keyCode === 13)
			$("#submit").click();
	}

	function getTotalPoints() {
		var total = 0;
		$(".playerpoints, #unusedPoints").each(function(index, elem) {
			total += parseInt($(this).val()) || 0;
		});
		return total;
	}

	window.addPlayers = function(num) {
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
		unusedPoints.prop("disabled", unusedPointsIncrement == 0);
		if (unusedPointsIncrement == 0) {
			unusedPoints.val('')
		};
		var entry = parseInt(unusedPoints.val()) || 0,
			good = (unusedPointsIncrement == 0 && entry == 0) ||
			(entry % unusedPointsIncrement) == 0;
		unusedPoints.removeClass(good ? "bad" : "good");
		unusedPoints.addClass(good ? "good" : "bad");
		return good;
	}

	window.submitGame = function(endpoint, callback, senddata, errorcallback) {
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
				"Name": players[i],
				"RawScore": points[i],
				"Chombos": chombos[i]
			})
		};
		$("#unusedPoints").each(function() {
			var val = $(this).val();
			if (val != "" && parseInt(val) > 0) {
				scores.push({
					"PlayerId": -1,
					"RawScore": parseInt(val),
					"Chombos": 0
				});
			};
		});
		senddata['scores'] = JSON.stringify(scores);
		$.post(endpoint, senddata, function(data) {
			if (data.status !== 0) {
				$("#message").text(data.error);
				if (typeof errorcallback === "function") {
					errorcallback(data);
				}
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

	$("#unusedPoints").change(checkUnusedPoints).keyup(checkUnusedPoints);
	$("#gamedate").change(updatePointSettings);
});
