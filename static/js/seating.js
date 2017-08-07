(function($) {
	$(function() {
		var selector = document.getElementById("person");
		var people = document.getElementById("people");
		var tables = document.getElementById("tables");
		var tablesTemplate;

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
			$.getJSON('/seating/currentplayers.json', function(data) {
				$(people).html("");
				data.forEach(function(playerdata) {
					player = playerdata[0];
					var newplayer = document.createElement("div");
					newplayer.className = "player";

					var priority = document.createElement("input");
					priority.id = player.replace(/ /g, "-") + "-priority";
					priority.type = "checkbox";
					priority.checked = !!playerdata[1];
					priority.className = "priority";
					$(priority).change(function(player) {
						return function() {
							prioritizePlayer(player, this.checked);
						};
					}(player));
					newplayer.appendChild(priority);

					var priorityview = document.createElement("label");
					priorityview.htmlFor = priority.id;
					newplayer.appendChild(priorityview);

					var playername = document.createElement("span");
					$(playername).text(player);
					newplayer.appendChild(playername);

					var deleteButton = document.createElement("a");
					$(deleteButton).text("✖");
					deleteButton.className = "deletebutton noselect clickable"
					$(deleteButton).click(function(player) {
						return function() {
							removePlayer(player);
						};
					}(player));
					newplayer.appendChild(deleteButton);

					people.appendChild(newplayer);
				});
			}).fail(xhrError);
		}

		$.get("/static/mustache/tables.mst", function(data) {
			tablesTemplate = data;
			Mustache.parse(tablesTemplate);
		});

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
