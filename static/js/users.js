(function($) {
	$(function() {
		$(".user-player-update").click(function() {
			var user = $(this).parents(".user");
			var playerId = user.data("id");
			var newPlayer = $(user).find(".user-player").val();

			var data = {
				"user": playerId,
				"newPlayer": newPlayer,
			};
			console.log(data);

			$.post("/admin/users", data, function(data) {
				$.notify(data.message, data.status);
			}, 'json');

		});
		window.populatePlayerComplete();
	});
})(jQuery);
