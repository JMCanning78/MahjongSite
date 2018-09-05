(function($) {
	$(function() {
		var players = null;

		var OTHERSTRING = "OTHER (PLEASE SPECIFY)";
		var SELECTSTRING = "PLEASE SELECT A PLAYER";
		var NEWPLAYERSTRING = "NEW PLAYER";

		function getPlayers() {
			$.getJSON('/seating/players.json', function(data) {
				players = data;
				populatePlayerComplete();
			}).fail(window.xhrError);
		}
		window.populatePlayerComplete = function(force) {
			if (players === null || force)
				return getPlayers();
			var elem = $("input.playercomplete");
			elem.autocomplete({
				source: players,
				minLength: 2
			});
			if (elem.next(".clearplayercomplete").length === 0) {
				elem.after("<button class=\"clearplayercomplete\">✖</button>");
				elem.each(function(_, complete) {
					$(complete).next(".clearplayercomplete").click(function(clearbutton) {
						$(complete).val("");
						$(complete).trigger("change");
					});
				});
			}
		}

		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		}
	});
	window.smoothScrollTo = function(x, y, interval, step, base) {
		if (x == null) {
			x = 0
		};
		if (y == null) {
			y = document.body.scrollHeight - window.innerHeight
		};
		if (interval == null) {
			interval = 10
		};
		if (step == null) {
			step = 0.02
		};
		if (base == null) {
			base = 30
		};
		var timer, t = -1.0,
			start_x = window.scrollX,
			start_y = window.scrollY;

		function incrScroll() {
			if (t >= 1.0 || (window.scrollX == x && window.scrollY == y)) {
				clearInterval(timer);
			}
			else {
				var new_x, new_y;
				t += step;
				if (t >= 1.0) {
					new_x = x;
					new_y = y
				}
				else {
					var base2t = Math.pow(base, t);
					var scale = base2t / (base2t + 1.0 / base2t);
					new_x = start_x + Math.floor((x - start_x) * scale);
					new_y = start_y + Math.floor((y - start_y) * scale);
				}
				window.scrollTo(new_x, new_y);
			};
		};
		timer = setInterval(incrScroll, interval);
	};

	window.mod = function(num, modulus) {
		var remainder = num % modulus;
		if (modulus > 0) {
			while (remainder < 0) {
				remainder += modulus
			}
		};
		return remainder;
	}
})(jQuery);
