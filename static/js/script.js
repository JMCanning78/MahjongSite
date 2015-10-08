(function($) {
	$(function() {
		window.getPlayers = function(callback) {
			$.getJSON('/seating/players.json', function(data) {
				window.players = data;
				$("select.playerselect").html("");

				populatePlayersSelect($("select.playerselect"))

				if(typeof callback === 'function')
					callback();
			}).fail(window.xhrError);
		}
		window.populatePlayersSelect = function(elem) {
			window.players.forEach(function(player) {
				var option = document.createElement("option");
				option.value = player;
				option.innerText = player;
				elem.append(option);
			});
		}

		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
})(jQuery);
