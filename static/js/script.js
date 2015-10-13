(function($) {
	$(function() {
		var OTHERSTRING = "OTHER (PLEASE SPECIFY)";
		var SELECTSTRING = "PLEASE SELECT A PLAYER";
		var NEWPLAYERSTRING = "NEW PLAYER";

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
			var select = document.createElement("option");
			select.value = "";
			window.setInnerText(select, SELECTSTRING);
			elem.append(select);

			var option = document.createElement("option");
			option.value = OTHERSTRING;
			window.setInnerText(option, OTHERSTRING);
			elem.append(option);

			window.players.forEach(function(player) {
				var option = document.createElement("option");
				option.value = player;
				window.setInnerText(option, player);
				elem.append(option);
			});

			elem.change(function () {
				if($(this).val() === OTHERSTRING && $(this).next(".playerbox").length === 0) {
					var playerbox = document.createElement("input");
					playerbox.className = "playerbox";
					playerbox.placeholder = NEWPLAYERSTRING;
					$(this).after(playerbox)
				}
				else if($(this).val() !== OTHERSTRING && $(this).next(".playerbox").length !== 0)
					$(this).next(".playerbox").remove();
			});
		}
		window.playersSelectValue = function(elem) {
			var val = elem.val()
			if(val === OTHERSTRING)
				val = elem.next(".playerbox").val();
			return val;
		}

		window.setInnerText = function(elem, text) {
			if(document.all)
				elem.innerText = text;
			else
				elem.textContent = text;
		}

		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
})(jQuery);
