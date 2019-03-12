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
				if (data.status !== 'success') {
					console.log(data.message);
					$.notify(data.message);
				}
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
			var meetupbutton = $(this);
			meetupbutton.prop("disabled", true);
			$.post('/seating/meetup', function(data) {
				if (data.status !== 'success') {
					console.log(data.message);
					$.notify(data.message);
				}
				getCurrentPlayers();
				regenTables();
				meetupbutton.prop("disabled", false);
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

		function prioritizePlayer() {
			var player = $(this).parent().data("name"),
				priority = $(this).data("priority") || 0,
				newpriority = mod(priority - 1, 3);
			$.post("/seating/prioritizeplayer", {
				player: player,
				priority: newpriority
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
						$(".player-status").click(prioritizePlayer);
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
						"tables": data.tables,
						"numplayers": data.numplayers
					}));
				else
					$(tables).html("<h1>" + data.message + "</h1>");
			}).fail(xhrError);
		}

		function refresh() {
			getCurrentPlayers();
			getCurrentTables();
		}
		var refresher = null;

		function change_auto_refresh() {
			if ($("#auto-refresh-seating").prop("checked")) {
				refresher = setInterval(refresh, 5000);
			}
			else if (refresher) {
				clearInterval(refresher);
				refresher = null;
			}
		}
		$("#auto-refresh-seating").change(change_auto_refresh);
		window.populatePlayerComplete();
		refresh();
		change_auto_refresh();

		function xhrError(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
})(jQuery);
