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
			var option = document.createElement("option");
			option.value = "Other (Please Specify)";
			option.innerText = "Other (Please Specify)";
			elem.append(option);
			elem.change(function () {
				if($(this).val() === "Other (Please Specify)" && $(this).next(".playerbox").length === 0) {
					var playerbox = document.createElement("input");
					playerbox.className = "playerbox";
					playerbox.placeholder = "New Player";
					$(this).after(playerbox)
				}
				else if($(this).val() !== "Other (Please Specify)" && $(this).next(".playerbox").length !== 0)
					$(this).next(".playerbox").remove();
			});
		}
		window.playersSelectValue = function(elem) {
			var val = elem.val()
			if(val === "Other (Please Specify)")
				val = elem.next(".playerbox").val();
			return val;
		}

		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
})(jQuery);
