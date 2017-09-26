(function($) {
	$(function() {
		var selector = document.getElementById("person");
		var people = document.getElementById("people");
		var tables = document.getElementById("tables");
		var tablesTemplate;
		var currentPlayersTemplate;

		$.get("/static/mustache/tables.mst", function(data) {
			tablesTemplate = data;
			Mustache.parse(tablesTemplate);
		});
		$.get("/static/mustache/currentplayers.mst", function(data) {
			currentPlayersTemplate = data;
			Mustache.parse(currentPlayersTemplate);
		});

		$("#addperson").click(function() {
			var val = $(selector).val();
			$.post("/seating/addcurrentplayer", {
				player: val
			}, function(data) {
				if (data.status !== 0)
					console.log(data);
				else {
					getCurrentPlayers();
					regenTables();
					window.populatePlayerComplete(true);
					$(selector).val("");
				}
			}, 'json');
		});
		$("#clearplayers").click(function() {
			var clearplayers = $("#clearplayers");
			if (confirm("Really clear current players?")) {
				$.post('/seating/clearcurrentplayers', function(data) {
					if (data.status !== 0)
						console.log(data);
					else {
						refresh();
					}
				}, 'json').fail(xhrError);
			}
		});
		$("#meetup").click(function() {
			$.post('/seating/meetup', function(data) {
				if (data.status !== 'success')
					console.log(data.message);
				else
					getCurrentPlayers();
				regenTables();
			}, 'json').fail(xhrError);
		});
		$("#regentables").click(regenTables);

		function removePlayer(player) {
			$.post("/seating/removeplayer", {
				player: player
			}, function(data) {
				getCurrentPlayers();
				regenTables();
			}, 'json');
		}

		function prioritizePlayer(player, priority) {
			$.post("/seating/prioritizeplayer", {
				player: player,
				priority: priority ? 1 : 0
			}, function(data) {
				getCurrentPlayers();
				regenTables();
			}, 'json');
		}

		function regenTables() {
			$.post("/seating/regentables", function(data) {
				getCurrentTables();
			}, 'json').fail(xhrError);
		}

		function getCurrentPlayers() {
			if (window.current_user !== undefined)
				$.getJSON('/seating/currentplayers.json', function(data) {
					if (data.players) {
						data.players.forEach(function(player) {
							player.id = player.name.replace(/ /g, "-");
						});
						$(people).html(Mustache.render(currentPlayersTemplate, data));
						$(".priority").change(function() {
							prioritizePlayer($(this).parent().data("name"), this.checked);
						});
						$(".deletebutton").click(function() {
							removePlayer($(this).parent().data("name"));
						});
					}
					else if (data.message)
						$(people).html("<h1>" + data.message + "</h1>");
				}).fail(xhrError);
		}


		function getCurrentTables() {
			$.getJSON('/seating/currenttables.json', function(data) {
				if (data.status === "success")
					$(tables).html(Mustache.render(tablesTemplate, {
						"tables": data.tables
					}));
				else
					$(tables).html("<h1>" + data.message + "</h1>");
			}).fail(xhrError);
		}

		function refresh() {
			getCurrentPlayers();
			getCurrentTables();
		}
		window.setInterval(function() {
			refresh();
		}, 5000);
		window.populatePlayerComplete();
		refresh();

		function xhrError(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
})(jQuery);
