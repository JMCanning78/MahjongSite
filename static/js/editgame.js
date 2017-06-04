(function($) {
	$(function () {
		$("#gamedate").datepicker({
			"dateFormat":"yy-mm-dd",
			"showAnim": "slideDown"
		}).val(scores[0][4]);

		$("#submit").click(window.submitGame.bind(this,
			'/admin/edit/' + window.gameid, function() {
				$("#gamedate").remove();
				$("#message").text("GAME EDITED");
				$("#content").append($("<a href='/admin/edit/" + window.gameid + "' class='button'>EDIT AGAIN</a>"));
			}, {gamedate:scores[0][4]}));

		window.populatedEditor = function () {
			for(var i = 0; i < scores.length; ++i) {
				var player = $("#players").children(".player").eq(i);

				player.children(".playercomplete").val(scores[i][1]);
				player.children(".chombos").val(scores[i][3]);
				player.children(".playerpoints").val(scores[i][2]).trigger('keyup');
			}
		};
	});
})(jQuery);
