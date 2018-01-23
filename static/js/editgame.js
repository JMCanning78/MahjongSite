(function($) {
	$(function() {
		$("#gamedate").datepicker({
			"dateFormat": "yy-mm-dd",
			"showAnim": "slideDown"
		}).val(scores[0][4]);

		$("#submit").click(function() {
			$("#submit").attr("disabled", true);
			$("#submit").text("Editing...");

			window.submitGame(
				'/admin/edit/' + window.gameid,
				function() {
					$("#message").text("GAME EDITED");
					$("#content").append($("<a href='/admin/edit/" + window.gameid + "' class='button'>EDIT AGAIN</a>"));
				},
				{
					'gamedate': $("#gamedate").val()
				},
				function() {
					$("#submit").attr("disabled", false);
				}
			);
		});

		window.populatedEditor = function() {
			for (var i = 0; i < scores.length; ++i) {
				var player = $("#players").children(".player").eq(i);

				player.children(".playercomplete").val(scores[i][1]);
				player.children(".chombos").val(scores[i][3]);
				player.children(".playerpoints").val(scores[i][2]).trigger('keyup');
			}
		};
	});
})(jQuery);
